from __future__ import absolute_import

import psycopg2
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

  def __init__(self, app = None):
    self._functions = {}
    self.app = app
    if app is not None:
      self.init_app(app)

  def init_app(self, app):
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
      )
    }
    # Load configs
    self._config['general'].update(app.config.get('PHPBB3', {}))
    self._config['db'].update(app.config.get('PHPBB3_DATABASE', {}))
    self._config['api'].update(app.config.get('PHPBB3_API', {}))

    if self._config['general']['DRIVER'] != 'api':
      # Setup available SQL functions
      self._prepare_statements()

    # Setup teardown
    app.teardown_appcontext(self.teardown)

    # Add ourselves to the app, so session interface can function
    app.phpbb3 = self

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
      get_autologin = "SELECT u.* "
                      "FROM {TABLE_PREFIX}users u, {TABLE_PREFIX}sessions_keys k "
                      "WHERE u.user_type IN (0, 3)" # FIXME Make it prettier, USER_NORMAL and USER_FOUNDER
                        "AND k.user_id = u.user_id"
                        "AND k.key_id = %(key)s",
      get_session   = "SELECT * "
                      "FROM {TABLE_PREFIX}sessions s, {TABLE_PREFIX}users u "
                      "WHERE s.session_id = %(session_id)s "
                        "AND s.session_user_id = u.user_id",
      get_user      = "SELECT * "
                      "FROM {TABLE_PREFIX}users "
                      "WHERE user_id = %(user_id)s"
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

# Session management
# TODO Split it into package
from flask.sessions import SecureCookieSessionInterface, SessionMixin

class PhpBB3Session(dict, SessionMixin):
  @property
  def is_authenticated(self):
    return 'user_id' in self and self['user_id'] > 1

class PhpBB3SessionInterface(SecureCookieSessionInterface):
  session_class = PhpBB3Session

  def open_session(self, app, request):
    session = super(PhpBB3SessionInterface, self).open_session(app, request)

    cookie_name = app.config.get('PHPBB3_COOKIE_NAME', 'phpbb3_')

    user_id = request.cookies.get(cookie_name + 'u', None)
    session_id = request.args.get('sid', type = str) or request.cookies.get(cookie_name + 'sid', None)
    autologin_key = request.cookies.get(cookie_name + 'key', None)
    if not session_id:
      session_id == None

    if session and session.get('session_id') != session_id:
      # Invalidate our session
      session = None

    if not session:
      session = PhpBB3Session()
      user = None
      if user_id and session_id:
        # Try to fetch session
        user = app.phpbb3.get_session(session_id = session_id)
      if not session and autologin_key:
        # Try autologin
        user = app.phpbb3.get_autologin(key = autologin_key)

      if isinstance(user, dict) and user:
        session.update(user)
      else:
        session['user_id'] = 1
        if session_id:
          session['session_id'] = session_id

    return session
