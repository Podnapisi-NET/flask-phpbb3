from __future__ import absolute_import

import functools
import json
import typing

import flask
from flask import _app_ctx_stack as flask_stack

import flask_phpbb3.sessions

import werkzeug.contrib.cache

try:
    import psycopg2
    import psycopg2.extras
except ImportError:
    from psycopg2cffi import compat
    compat.register()
    import psycopg2.extras


class PhpBB3(object):
    KNOWN_OPERATIONS = (
        'fetch',
        'get',
        'has',
        'set',
    )
    KNOWN_DRIVERS = (
        'psycopg2',
    )

    def __init__(
        self,
        app=None,  # type: typing.Optional[flask.Flask]
        cache=None,  # type: werkzeug.contrib.cache.BaseCache
    ):
        # type: (...) -> None
        self._functions = {}  # type: dict

        self._cache = werkzeug.contrib.cache.SimpleCache()\
            # type: werkzeug.contrib.cache.BaseCache

        self.app = app
        if app is not None:
            self.init_app(app, cache)

    def init_app(
        self,
        app,  # type: flask.Flask
        cache=None  # type: werkzeug.contrib.cache.BaseCache
    ):
        # type: (...) -> None
        # Setup default configs
        self._config = {
            'general': dict(
                # TODO Add other drivers and reusability from other extensions
                DRIVER='psycopg2',
                # TODO Currenlty only 3.1 is available
                VERSION='3.1',
            ),
            'db': dict(
                HOST='127.0.0.1',
                DATABASE='phpbb3',
                USER='phpbb3',
                PASSWORD='',
                TABLE_PREFIX='phpbb_',
            ),
            'session_backend': dict(
                TYPE='simple',
            ),
        }
        # Load configs
        self._config['general'].update(app.config.get('PHPBB3', {}))
        self._config['db'].update(app.config.get('PHPBB3_DATABASE', {}))
        self._config['session_backend'].update(
            app.config.get('PHPBB3_SESSION_BACKEND', {})
        )

        # Use passed in cache interface (see Flask-Cache extension)
        if not cache:
            # Setup our own
            cache_backend = self._config['session_backend'].get('TYPE',
                                                                'simple')
            if cache_backend == 'memcached':
                key_prefix = self._config['session_backend'].get('KEY_PREFIX',
                                                                 'phpbb3')
                self._cache = werkzeug.contrib.cache.MemcachedCache(
                    self._config['session_backend'].get('SERVERS',
                                                        ['127.0.0.1:11211']),
                    key_prefix=key_prefix,
                )
            else:
                self._cache = werkzeug.contrib.cache.SimpleCache()
        else:
            self._cache = cache

        # Setup available SQL functions
        self._prepare_statements()

        # Setup teardown
        app.teardown_appcontext(self.teardown)

        # Add ourselves to the app, so session interface can function
        app.phpbb3 = self

        # Use our session interface
        # TODO Is it wise to do it here? Should user do it himself?
        app.session_interface =\
            flask_phpbb3.sessions.PhpBB3SessionInterface(app)

    @property
    def _db(self):
        # type: () -> typing.Any
        """Returns database connection."""
        ctx = flask_stack.top
        if ctx is not None:
            # Connect when there is no connection or we have a closed
            # connection
            if not hasattr(ctx, 'phpbb3_db') or ctx.phpbb3_db.closed:
                ctx.phpbb3_db = psycopg2.connect(
                    'dbname={DATABASE}'
                    ' host={HOST}'
                    ' user={USER}'
                    ' password={PASSWORD}'.format(**self._config['db']),
                    connection_factory=psycopg2.extras.DictConnection
                )
            return ctx.phpbb3_db

    def _prepare_statements(self):
        # type: () -> None
        """
        Initializes prepared SQL statements, depending on version of PHPBB3
        """
        self._functions.update(dict(
            get_autologin=(
                "SELECT u.* "
                "FROM {TABLE_PREFIX}users u,"
                "     {TABLE_PREFIX}sessions_keys k "
                # FIXME Make it prettier, USER_NORMAL and USER_FOUNDER
                "WHERE u.user_type IN (0, 3)"
                "AND k.user_id=u.user_id"
                "AND k.key_id = %(key)s"
            ),
            get_session=(
                "SELECT * "
                "FROM {TABLE_PREFIX}sessions s, {TABLE_PREFIX}users u "
                "WHERE s.session_id = %(session_id)s "
                "AND s.session_user_id=u.user_id"
            ),
            get_user=(
                "SELECT * "
                "FROM {TABLE_PREFIX}users "
                "WHERE user_id = %(user_id)s"),
            has_membership=(
                "SELECT ug.group_id "
                "FROM {TABLE_PREFIX}user_group ug "
                "WHERE ug.user_id = %(user_id)s "
                "  AND ug.group_id = %(group_id)s "
                "  AND ug.user_pending=0 "
                "LIMIT 1"
            ),
            has_membership_resolve=(
                "SELECT ug.group_id "
                "FROM {TABLE_PREFIX}user_group ug,"
                "     {TABLE_PREFIX}groups g "
                "WHERE ug.user_id = %(user_id)s "
                "  AND g.group_name = %(group_name)s "
                "  AND ug.group_id=g.group_id "
                "  AND ug.user_pending=0 "
                "LIMIT 1"
            ),
            fetch_acl_options=(
                "SELECT"
                "   *"
                " FROM"
                "   {TABLE_PREFIX}acl_options"
                " ORDER BY"
                "   auth_option_id"
            ),
            get_unread_notifications_count=(
                "SELECT"
                "   COUNT(n.*) as num"
                " FROM"
                "   {TABLE_PREFIX}notifications n,"
                "   {TABLE_PREFIX}notification_types nt"
                " WHERE"
                "   n.user_id = %(user_id)s "
                "   AND nt.notification_type_id=n.notification_type_id"
                "   AND nt.notification_type_enabled=1 "
                "   AND n.notification_read=0"
            ),
        ))

        # TODO Add/Move to version specific queries

    def _sql_query(
        self,
        operation,  # type: str
        query,  # type: str
        cache_key=None,  # type: typing.Optional[str]
        cache_ttl=None,  # type: typing.Optional[int]
        skip=0,  # type: int
        limit=10,  # type: typing.Optional[int]
        **kwargs  # type: int
    ):
        # type: (...) -> typing.Any
        """Executes a query with values in kwargs."""
        if operation not in self.KNOWN_OPERATIONS:
            raise ValueError("Unknown operation")

        versioned_cache_key = None
        if cache_key and operation != 'set':
            versioned_cache_key = '{name}:{arguments}'.format(
                name=cache_key,
                arguments=':'.join(key + str(value)
                                   for key, value in kwargs.items())
            )
            raw_data = self._cache.get(versioned_cache_key)
            if raw_data and isinstance(raw_data, (str, unicode)):
                try:
                    return json.loads(raw_data)
                except ValueError:
                    # Woops :S
                    pass

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
            if output is not None:
                output = dict(output)
        elif operation == 'has':
            output = bool(c.fetchone())
        elif operation == 'fetch':
            # FIXME a more performant option
            output = [dict(i) for i in c]
        elif operation == 'set':
            # It is an update
            output = c.statusmessage
            self._db.commit()
        c.close()

        if versioned_cache_key:
            try:
                self._cache.set(versioned_cache_key,
                                json.dumps(output),
                                cache_ttl)
            except ValueError:
                # Woops :S
                pass

        return output

    def __getattr__(self, name):
        # type: (str) -> typing.Callable
        parsed_name = name.split('_')
        is_cached = False
        if parsed_name[0] == 'cached':
            is_cached = True
            parsed_name = parsed_name[1:]

        operation = parsed_name[0]
        prepared_statement = '_'.join(parsed_name)
        cache_key = None
        if is_cached:
            cache_key = prepared_statement

        if prepared_statement not in self._functions:
            raise AttributeError("Function {} does not exist.".format(
                prepared_statement
            ))

        func_or_query = self._functions[prepared_statement]
        if callable(func_or_query):
            return functools.partial(func_or_query, self)
        else:
            return functools.partial(
                self._sql_query,
                operation,
                func_or_query,
                cache_key,
            )

    def teardown(self, exception):
        # type: (typing.Any) -> None
        ctx = flask_stack.top
        if hasattr(ctx, 'phphbb3_db'):
            ctx.phpbb3_db.close()
