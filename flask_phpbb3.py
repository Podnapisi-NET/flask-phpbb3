from __future__ import absolute_import

import psycopg2
import psycopg2.extras
import functools

from flask import _app_ctx_stack as stack

class PhpBB3(object):
  KNOWN_OPERATIONS = (
    'fetch',
    'get'
  )

  def __init__(self, app = None):
    self._functions = {}
    self.app = app
    if app is not None:
      self.init_app(app)

  def init_app(self, app):
    # Load config
    self._config = dict(
      DRIVER       = 'psycopg2', # TODO Add other drivers and reusability from other extensions
      HOST         = '127.0.0.1',
      DATABASE     = 'phpbb3',
      USER         = 'phpbb3',
      PASSWORD     = '',
      TABLE_PREFIX = 'phpbb_',
      VERSION      = '3.1', # TODO Currenlty only 3.1 is available
    )
    self._config.update(app.config.get('PHPBB3', {}))

    # Setup available SQL functions
    self._prepare_statements()

    # Setup teardown
    app.teardown_appcontext(self.teardown)

  @property
  def _db(self):
    """Returns database connection."""
    ctx = stack.top
    if ctx is not None:
      if not hasattr(ctx, 'phpbb3_db'):
        ctx.phpbb3_db = psycopg2.connect(
          'dbname={DATABASE} host={HOST} user={USER} password={PASSWORD}'.format(self._config),
          connection_factory = psycopg2.extras.DictConnection
        )
      return ctx.phpbb3_db

  def _prepare_statements(self):
    """Initializes prepared SQL statements, depending on version of PHPBB3."""
    self._functions.update(dict(
      get_autologin = "SELECT u.* "
                      "FROM {TABLE_PREFIX}users u, {TABLE_PREFIX}sessions_keys k "
                      "WHERE u.user_type IN (0, 3)" # FIXME Make it prettier, USER_NORMAL and USER_FOUNDER
                        "AND k.user_id = u.user_id"
                        "AND k.key_id = %(key)s",
      get_session   = "SELECT * "
                      "FROM {TABLE_PREFIX}sessions "
                      "WHERE session_id = %(session_id)s",
      get_user      = "SELECT * "
                      "FROM {TABLE_PREFIX}users "
                      "WHERE user_id = %(user_id)d"
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

    c.execute(query.format(self._config), kwargs)

    output = None
    if operation == 'get':
      output = c.fetchone()
    elif operation == 'fetch':
      output = c.fetchall()

    # Finish it
    c.close()
    return output

  def __getattribute__(self, name):
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
