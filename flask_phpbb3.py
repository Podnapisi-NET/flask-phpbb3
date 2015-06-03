from __future__ import absolute_import

try:
  import psycopg2
  import psycopg2.extras
except ImportError:
  from psycopg2cffi import compat
  compat.register()
  import psycopg2.extras

import functools

from flask import _app_ctx_stack as stack

class PhpBB3(object):
  KNOWN_OPERATIONS = (
    'fetch',
    'get',
    'has',
  )
  KNOWN_DRIVERS = (
    'psycopg2',
  )

  def __init__(self, app = None, cache = None):
    self._functions = {}
    self.app = app
    if app is not None:
      self.init_app(app, cache)

  def init_app(self, app, cache = None):
    # Setup default configs
    self._config = {
      'general': dict (
        DRIVER       = 'psycopg2', # TODO Add other drivers and reusability from other extensions
        VERSION      = '3.1', # TODO Currenlty only 3.1 is available
      ),
      'db': dict(
        HOST         = '127.0.0.1',
        DATABASE     = 'phpbb3',
        USER         = 'phpbb3',
        PASSWORD     = '',
        TABLE_PREFIX = 'phpbb_',
      ),
      'session_backend': dict(
        TYPE = 'simple',
      ),
    }
    # Load configs
    self._config['general'].update(app.config.get('PHPBB3', {}))
    self._config['db'].update(app.config.get('PHPBB3_DATABASE', {}))
    self._config['session_backend'].update(app.config.get('PHPBB3_SESSION_BACKEND', {}))

    # Use passed in cache interface (see Flask-Cache extension)
    self._cache = cache
    if self._cache is None:
      # Setup our own
      cache_backend = self._config['session_backend'].get('TYPE', 'simple')
      if cache_backend == 'simple':
        from werkzeug.contrib.cache import SimpleCache
        self._cache = SimpleCache()
      elif cache_backend == 'memcached':
        from werkzeug.contrib.cache import MemcachedCache
        self._cache = MemcachedCache(
          self._config['session_backend'].get('SERVERS', ['127.0.0.1:11211']),
          key_prefix = self._config['session_backend'].get('KEY_PREFIX', 'phpbb3')
        )

    # Setup available SQL functions
    self._prepare_statements()

    # Setup teardown
    app.teardown_appcontext(self.teardown)

    # Add ourselves to the app, so session interface can function
    app.phpbb3 = self

    # Use our session interface
    # TODO Is it wise to do it here? Should user do it himself?
    app.session_interface = PhpBB3SessionInterface(app)

  @property
  def _db(self):
    """Returns database connection."""
    ctx = stack.top
    if ctx is not None:
      if not hasattr(ctx, 'phpbb3_db'):
        ctx.phpbb3_db = psycopg2.connect(
          'dbname={DATABASE} host={HOST} user={USER} password={PASSWORD}'.format(**self._config['db']),
          connection_factory = psycopg2.extras.DictConnection
        )
      return ctx.phpbb3_db

  def _prepare_statements(self):
    """Initializes prepared SQL statements, depending on version of PHPBB3."""
    self._functions.update(dict(
      get_autologin  = "SELECT u.* "
                       "FROM {TABLE_PREFIX}users u, {TABLE_PREFIX}sessions_keys k "
                       "WHERE u.user_type IN (0, 3)" # FIXME Make it prettier, USER_NORMAL and USER_FOUNDER
                         "AND k.user_id = u.user_id"
                         "AND k.key_id = %(key)s",
      get_session    = "SELECT * "
                       "FROM {TABLE_PREFIX}sessions s, {TABLE_PREFIX}users u "
                       "WHERE s.session_id = %(session_id)s "
                         "AND s.session_user_id = u.user_id",
      get_user       = "SELECT * "
                       "FROM {TABLE_PREFIX}users "
                       "WHERE user_id = %(user_id)s",
      has_membership = "SELECT ug.group_id "
                       "FROM {TABLE_PREFIX}user_group ug "
                       "WHERE ug.user_id = %(user_id)s "
                         "AND ug.group_id = %(group_id)s "
                         "AND ug.user_pending = 0 "
                       "LIMIT 1",
      has_membership_resolve = "SELECT ug.group_id "
                               "FROM {TABLE_PREFIX}user_group ug, {TABLE_PREFIX}groups g "
                               "WHERE ug.user_id = %(user_id)s "
                                 "AND g.group_name = %(group_name)s "
                                 "AND ug.group_id = g.group_id "
                                 "AND ug.user_pending = 0 "
                               "LIMIT 1",
      fetch_acl_options = "SELECT * FROM {TABLE_PREFIX}acl_options ORDER BY auth_option_id"
    ))

    # TODO Add/Move to version specific queries

  def _sql_query(self, operation, query, skip = 0, limit = 10, **kwargs):
    """Executes a query with values in kwargs."""
    if operation not in self.KNOWN_OPERATIONS:
      raise ValueError("Unknown operation")

    # FIXME Driver specific code!
    c = self._db.cursor()

    if operation == 'fetch':
      # Add skip and limit
      query += ' OFFSET {:d}'.format(skip)
      if limit:
        query += 'LIMIT {:d}'.format(limit)

    c.execute(query.format(**self._config['db']), kwargs)

    output = None
    if operation == 'get':
      output = c.fetchone()
      c.close()
      if output is not None:
        output = dict(output)
    elif operation == 'has':
      output = bool(c.fetchone())
      c.close()
    elif operation == 'fetch':
      # FIXME a more performant option
      output = (dict(i) for i in c)

    return output

  def __getattr__(self, name):
    if name not in self._functions:
      raise AttributeError("Function {} does not exist.".format(name))
    func = self._functions[name]
    if callable(func):
      return functools.partial(func, self)
    else:
      return functools.partial(self._sql_query, name.split('_')[0], func)

  def teardown(self, exception):
    ctx = stack.top
    if hasattr(ctx, 'phphbb3_db'):
      ctx.phpbb3_db.close()

from flask.sessions import SessionMixin, SessionInterface

class PhpBB3Session(dict, SessionMixin):
  def __init__(self):
    # Some session related variables
    self.modified = False
    self.new = False
    self._read_only_properties = set([])

    # Some ACL related things
    self._acl_options = None
    self._acl = None
    self._acl_cache = {}

  def __setitem__(self, key, value):
    super(PhpBB3Session, self).__setitem__(key, value)
    if key not in self._read_only_properties:
      self.modified = True

  @property
  def is_authenticated(self):
    """Helper method to test if user is authenticated."""
    return self.get('user_id', 1) > 1

  def is_member(self, group):
    """Tests if user is a member of specified group."""
    from flask import current_app

    if isinstance(group, int):
      # Try with default group
      if group == self['group_id']:
        return True

      # Access database
      return current_app.phpbb3.has_membership(user_id  = self['user_id'],
                                               group_id = group)
    else:
      # Use group name
      return current_app.phpbb3.has_membership_resolve(user_id    = self['user_id'],
                                                       group_name = group)

  def _load_acl(self):
    if self._acl is not None and self._acl_options:
      # Nothing to load/convert
      return

    from flask import current_app

    # Fetch from cache
    self._acl_options = current_app.phpbb3._cache.get('_acl_options')

    if not self._acl_options:
      # Load ACL options, so we can decode the user ACL
      self._acl_options = {
        'local': {},
        'global': {}
      }
      local_index = 0
      global_index = 0

      for opt in current_app.phpbb3.fetch_acl_options(limit = None):
        if opt['is_local'] == 1:
          self._acl_options['local'][opt['auth_option']] = local_index
          local_index += 1
        if opt['is_global'] == 1:
          self._acl_options['global'][opt['auth_option']] = global_index
          global_index += 1
        # TODO By looking phpbb3 code, here also comes translation option <=> id

      # Store it into cache
      current_app.phpbb3._cache.set('_acl_options', self._acl_options)

    if not self._acl:
      # Load/transform user's ACL data
      seq_cache = {}
      self._acl = {}

      for f, perms in enumerate(self['user_permissions'].rstrip().splitlines()):
        if not perms:
          continue

        # Do the conversion magic
        self._acl[str(f)] = ''
        for sub in [perms[j:j + 6] for j in range(0, len(perms), 6)]:
          if sub in seq_cache:
            converted = seq_cache[sub]
          else:
            converted = bin(int(sub, 36))[2:]
            converted = seq_cache[sub] = '0' * (31 - len(converted)) + converted

          self._acl[str(f)] += converted

  def has_privilege(self, option, forum_id = 0):
    """Test if user has global or local (if forum_id is set) privileges."""
    # We load the ACL
    self._load_acl()

    # Make sure it is int, and convert it into str for mapping purposes
    forum_id = str(int(forum_id))

    # Parse negation
    negated = option.startswith('!')
    if negated:
      option = option[1:]

    if forum_id not in self._acl_cache or option not in self._acl_cache[forum_id]:
      # Default is, no permission
      self._acl_cache.setdefault(forum_id, {})[option] = False

      # Global permissions...
      if option in self._acl_options['global'] and '0' in self._acl:
        try:
          self._acl_cache[forum_id][option] = bool(int(self._acl['0'][self._acl_options['global'][option]]))
        except IndexError:
          pass

      # Local permissions...
      if forum_id != '0' and option in self._acl_options['local']:
        try:
          self._acl_cache[forum_id][option] |= bool(int(self._acl.get(forum_id, '0' * 31)[self._acl_options['local'][option]]))
        except IndexError:
          pass

    return negated ^ self._acl_cache[forum_id][option]

  def has_privileges(self, *options, **kwargs):
    output = False
    for option in options:
      output |= self.has_privilege(option, **kwargs)
    return output

class PhpBB3SessionInterface(SessionInterface):
  """A read-only session interface to access phpBB3 session."""
  session_class = PhpBB3Session

  def __init__(self, app):
    """Initializes session interface with app and possible cache (Flask-Cache) object for storing additional data."""
    self.cache = app.phpbb3._cache

  def open_session(self, app, request):
    cookie_name = app.config.get('PHPBB3_COOKIE_NAME', 'phpbb3_')

    session_id = request.args.get('sid', type = str) or request.cookies.get(cookie_name + 'sid', None)
    if not session_id:
      session_id = None

    user = None
    if session_id:
      # Try to fetch session
      user = app.phpbb3.get_session(session_id = session_id)
      if 'username' in user:
        user['username'] = user['username'].decode('utf-8', 'ignore')
    else:
      # Use anonymous user
      user = app.phpbb3.get_user(user_id = 1)

    # Create session
    session = self.session_class()

    # Set session data
    if isinstance(user, dict) and user:
      session._read_only_properties = set(user.keys())
      session.update(user)

      import json

      # Read from local storage backend
      data = self.cache.get('sessions_' + session['session_id'])
      try:
        data = json.loads(data or '')
      except ValueError:
        data = None
      if not isinstance(data, dict):
        data = {}
      session.update(data)

    return session

  def save_session(self, app, session, response):
    """Currenlty does nothing."""
    if session.modified and session._read_only_properties:
      import json
      # Store all 'storable' properties
      data = dict([(k, v) for k, v in session.items() if k not in session._read_only_properties])
      self.cache.set('sessions_' + session['session_id'], json.dumps(data))
