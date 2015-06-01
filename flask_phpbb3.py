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
      'api': dict(
        URL    = 'http://127.0.0.1/connector',
        SECRET = '',
      ),
      'session_backend': dict(
        TYPE    = 'simple',
        SERVERS = None,
      ),
    }
    # Load configs
    self._config['general'].update(app.config.get('PHPBB3', {}))
    self._config['db'].update(app.config.get('PHPBB3_DATABASE', {}))
    self._config['api'].update(app.config.get('PHPBB3_API', {}))
    self._config['session_backend'].update(app.config.get('PHPBB3_SESSION_BACKEND', {}))

    # Use passed in cache interface (see Flask-Cache extension)
    self._cache = cache

    if self._config['general']['DRIVER'] != 'api':
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

  @property
  def _connection(self):
    """Constructs and returns API connection."""
    ctx = stack.top
    if ctx is not None:
      if not hasattr(ctx, 'phpbb3_api'):
        import jsonrpclib
        ctx.phpbb3_api = jsonrpclib.Server(self._config['api']['URL'])
      return ctx.phpbb3_api

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
      get_membership = "SELECT ug.group_id "
                       "FROM {TABLE_PREFIX}user_group ug "
                       "WHERE ug.user_id = %(user_id)s "
                         "AND ug.group_id = %(group_id)s "
                         "AND ug.user_pending = 0 "
                       "LIMIT 1",
      get_membership_resolve = "SELECT ug.group_id "
                               "FROM {TABLE_PREFIX}user_group ug, {TABLE_PREFIX}groups g "
                               "WHERE ug.user_id = %(user_id)s "
                                 "AND g.group_name = %(group_name)s "
                                 "AND ug.group_id = g.group_id "
                                 "AND ug.user_pending = 0 "
                               "LIMIT 1",
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
      query += ' OFFSET {:d} LIMIT {:d}'.format(skip, limit)

    c.execute(query.format(**self._config['db']), kwargs)

    output = None
    if operation == 'get':
      output = c.fetchone()
      if output is not None:
        output = dict(output)
    elif operation == 'fetch':
      # FIXME a more performant option
      output = [dict(i) for i in c.fetchall()]

    # Finish it
    c.close()
    return output

  def __getattr__(self, name):
    if self._config['general']['DRIVER'] == 'api':
      # Use JSONRPC API - using only first parameter, making sure we use keyworded arguments
      return functools.partial(
        lambda func, **kwargs: func(kwargs),
        getattr(self._connection, name)
      )

    # Here is direct DB access
    if name not in self._functions:
      raise AttributeError("Function {} does not exist, use register_function, to add it.".format(name))
    func = self._functions[name]
    if callable(func):
      return func
    else:
      return functools.partial(self._sql_query, name.split('_')[0], func)

  def register_function(self, name, callable_or_sql):
    """Adds/Overwrites a function with 'name' with 'callable_or_sql'."""
    if not isinstance(callable_or_sql, basestring) or not callable(callable_or_sql):
      raise TypeError("To register a function, you have to specify a SQL query as string, or a callable object.")
    self._functions[name] = callable_or_sql

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
      if group == self.group_id:
        return True

      # Access database
      return bool(current_app.phpbb3.get_membership(user_id  = self.user_id,
                                                    group_id = group))
    else:
      # Use group name
      return bool(self.get_membership_resolve(user_id    = self.user_id,
                                              group_name = group))

  def has_privileges(self, *privileges):
    """Tests if user has any of specified privileges."""
    # TODO Need API
    pass

class PhpBB3SessionInterface(SessionInterface):
  """A read-only session interface to access phpBB3 session."""
  session_class = PhpBB3Session

  def __init__(self, app):
    """Initializes session interface with app and possible cache (Flask-Cache) object for storing additional data."""
    if app.phpbb3._cache is None:
      cache_backend = app.phpbb3._config['session_backend'].get('TYPE', 'simple')
      if cache_backend == 'simple':
        from werkzeug.contrib.cache import SimpleCache
        self.cache = SimpleCache()
      elif cache_backend == 'memcached':
        from werkzeug.contrib.cache import MemcachedCache
        self.cache = MemcachedCache(app.phpbb3._config['session_backend'].get('SERVERS', ['127.0.0.1:11211']))
    else:
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
