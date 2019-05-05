from __future__ import absolute_import

import typing

import flask

import flask_phpbb3.backends.base
import flask_phpbb3.sessions

import werkzeug.contrib.cache


class PhpBB3(object):
    def __init__(
        self,
        app=None,  # type: typing.Optional[flask.Flask]
        cache=None,  # type: werkzeug.contrib.cache.BaseCache
    ):
        # type: (...) -> None
        self.app = app
        if app is not None:
            self.init_app(app, cache)

    def init_app(
        self,
        app,  # type: flask.Flask
        cache=None  # type: typing.Optional[werkzeug.contrib.cache.BaseCache]
    ):
        # type: (...) -> None
        self._ensure_default_config(app)

        # Use passed in cache interface (see Flask-Cache extension)
        if not cache:
            # Setup our own
            cache_backend = app.config['PHPBB3_SESSION_BACKEND']['TYPE']
            if cache_backend == 'memcached':
                key_prefix = app.config['PHPBB3_SESSION_BACKEND']['KEY_PREFIX']
                cache_driver = werkzeug.contrib.cache.MemcachedCache(
                    app.config['PHPBB3_SESSION_BACKEND']['SERVERS'],
                    key_prefix=key_prefix,
                )  # type: werkzeug.contrib.cache.BaseCache
            else:
                cache_driver = werkzeug.contrib.cache.SimpleCache()
        else:
            cache_driver = cache

        # Setup teardown
        app.teardown_appcontext(self.teardown)

        # Add ourselves to the app, so session interface can function
        app.phpbb3 = self
        app.phpbb3_cache = cache_driver

        # Use our session interface
        # TODO Is it wise to do it here? Should user do it himself?
        app.session_interface =\
            flask_phpbb3.sessions.PhpBB3SessionInterface()

    @classmethod
    def _ensure_default_config(cls, app):
        # type: (flask.Flask) -> None
        app.config.setdefault('PHPBB3', {})
        app.config['PHPBB3'].setdefault('DRIVER', 'psycopg2')
        app.config['PHPBB3'].setdefault('VERSION', '3.1')
        app.config.setdefault('PHPBB3_DATABASE', {})
        app.config['PHPBB3_DATABASE'].setdefault('HOST', '127.0.0.1')
        app.config['PHPBB3_DATABASE'].setdefault('DATABASE', 'phpbb3')
        app.config['PHPBB3_DATABASE'].setdefault('USER', 'phpbb3')
        app.config['PHPBB3_DATABASE'].setdefault('PASSWORD', '')
        app.config['PHPBB3_DATABASE'].setdefault('TABLE_PREFIX', 'phpbb_')
        app.config['PHPBB3_DATABASE'].setdefault('CUSTOM_USER_FIELDS', [])
        app.config['PHPBB3_DATABASE'].setdefault('CUSTOM_STATEMENTS', {})
        app.config.setdefault('PHPBB3_SESSION_BACKEND', {})
        app.config['PHPBB3_SESSION_BACKEND'].setdefault('TYPE', 'simple')

        # Conditional defaults
        if app.config['PHPBB3_SESSION_BACKEND']['TYPE'] == 'memcached':
            app.config['PHPBB3_SESSION_BACKEND'].setdefault(
                'KEY_PREFIX',
                'phpbb3'
            )
            app.config['PHPBB3_SESSION_BACKEND'].setdefault(
                'SERVERS',
                ['127.0.0.1:11211']
            )

    @classmethod
    def _create_backend(
        cls,
        backend_type,  # type: str
        config,  # type: dict
        cache  # type: werkzeug.contrib.cache.BaseCache
    ):
        # type: (...) -> flask_phpbb3.backends.base.BaseBackend
        if backend_type == 'psycopg2':
            import flask_phpbb3.backends.psycopg2
            return flask_phpbb3.backends.psycopg2.Psycopg2Backend(
                cache,
                config,
            )
        else:
            raise ValueError('Unsupported driver {}'.format(backend_type))

    @property
    def _backend(self):
        # type: () -> flask_phpbb3.backends.base.BaseBackend
        """Returns phpbb3 backend"""
        current_app = self.app or flask.current_app

        ctx = flask._app_ctx_stack.top
        if ctx is not None:
            if not hasattr(ctx, 'phpbb3_backend')\
               or ctx.phpbb3_backend.is_closed:
                backend = PhpBB3._create_backend(
                    current_app.config['PHPBB3']['DRIVER'],
                    current_app.config['PHPBB3_DATABASE'],
                    current_app.phpbb3_cache,
                )
                ctx.phpbb3_backend = backend
            else:
                backend = ctx.phpbb3_backend
            return backend
        raise AttributeError('No context available')

    def get_autologin(self, key, cache=False, cache_ttl=None):
        # type: (str, bool, typing.Optional[int]) -> typing.Optional[dict]
        output = self._backend.execute(
            'get_autologin',
            key=key,
            cache=cache,
            cache_ttl=cache_ttl,
        )  # type: typing.Optional[dict]
        return output

    def get_session(self, session_id, cache=False, cache_ttl=None):
        # type: (str, bool, typing.Optional[int]) -> typing.Optional[dict]
        output = self._backend.execute(
            'get_session',
            session_id=session_id,
            cache=cache,
            cache_ttl=cache_ttl,
        )  # type: typing.Optional[dict]
        return output

    def get_user(self, user_id, cache=False, cache_ttl=None):
        # type: (int, bool, typing.Optional[int]) -> typing.Optional[dict]
        output = self._backend.execute(
            'get_user',
            user_id=user_id,
            cache=cache,
            cache_ttl=cache_ttl,
        )  # type: typing.Optional[dict]
        return output

    def get_user_profile(self, user_id, cache=False, cache_ttl=None):
        # type: (int, bool, typing.Optional[int]) -> typing.Optional[dict]
        output = self._backend.execute(
            'get_user_profile',
            user_id=user_id,
            cache=cache,
            cache_ttl=cache_ttl,
        )  # type: typing.Optional[dict]
        return output

    def has_membership(
        self,
        user_id,  # type: int
        group_id,  # type: int
        cache=False,  # type: bool
        cache_ttl=None,  # type: typing.Optional[int]
    ):
        # type: (...) -> typing.Optional[bool]
        output = self._backend.execute(
            'has_membership',
            user_id=user_id,
            group_id=group_id,
            cache=cache,
            cache_ttl=cache_ttl,
        )  # type: typing.Optional[bool]
        return output

    def has_membership_resolve(
        self,
        user_id,  # type: int
        group_name,  # type: str
        cache=False,  # type: bool
        cache_ttl=None,  # type: typing.Optional[int]
    ):
        # type: (...) -> typing.Optional[bool]
        output = self._backend.execute(
            'has_membership_resolve',
            user_id=user_id,
            group_name=group_name,
            cache=cache,
            cache_ttl=cache_ttl,
        )  # type: typing.Optional[bool]
        return output

    def fetch_acl_options(
        self,
        skip=0,  # type: int
        limit=10,  # type: typing.Optional[int]
        cache=False,  # type: bool
        cache_ttl=None,  # type: typing.Optional[int]
    ):
        # type: (...) -> typing.Optional[typing.List[dict]]
        output = self._backend.execute(
            'fetch_acl_options',
            skip=skip,
            limit=limit,
            cache=cache,
            cache_ttl=cache_ttl,
        )  # type: typing.Optional[typing.List[dict]]
        return output

    def get_unread_notifications_count(
        self,
        user_id,  # type: int
        cache=False,  # type: bool
        cache_ttl=None,  # type: typing.Optional[int]
    ):
        # type: (...) -> typing.Optional[dict]
        output = self._backend.execute(
            'get_unread_notifications_count',
            user_id=user_id,
            cache=cache,
            cache_ttl=cache_ttl,
        )  # type: typing.Optional[dict]
        return output

    def get_user_acl(self, raw_user_permissions):
        # type: (str) -> flask_phpbb3.backends.base.UserAcl
        return self._backend.get_user_acl(raw_user_permissions)

    def execute_custom(
        self,
        command,  # type: str
        cache=False,  # type: bool
        cache_ttl=None,  # type: typing.Optional[int]
        **kwargs  # type: typing.Any
    ):
        # type: (...) -> typing.Any
        output = self._backend.execute(
            command,
            cache=cache,
            cache_ttl=cache_ttl,
            **kwargs
        )  # type: typing.Any
        return output

    def teardown(self, exception):
        # type: (typing.Any) -> None
        ctx = flask._app_ctx_stack.top
        if hasattr(ctx, 'phpbb3_backend'):
            ctx.phpbb3_backend.close()
