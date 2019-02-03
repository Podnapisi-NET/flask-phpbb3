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

        # Setup teardown
        app.teardown_appcontext(self.teardown)

        # Add ourselves to the app, so session interface can function
        app.phpbb3 = self

        # Use our session interface
        # TODO Is it wise to do it here? Should user do it himself?
        app.session_interface =\
            flask_phpbb3.sessions.PhpBB3SessionInterface(app)

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
        ctx = flask._app_ctx_stack.top
        if ctx is not None:
            if not hasattr(ctx, 'phpbb3_backend')\
               or ctx.phpbb3_backend.is_closed:
                backend = PhpBB3._create_backend(
                    self._config['general']['DRIVER'],
                    self._config['db'],
                    self._cache,
                )
                ctx.phpbb3_backend = backend
            else:
                backend = ctx.phpbb3_backend
            return backend
        raise AttributeError('No context available')

    def get_autologin(self, key, cache=False, cache_ttl=None):
        # type: (str, bool, typing.Optional[int]) -> typing.Optional[dict]
        output = self._backend.execute('get_autologin', key=key)\
            # type: typing.Optional[dict]
        return output

    def get_session(self, session_id, cache=False, cache_ttl=None):
        # type: (str, bool, typing.Optional[int]) -> typing.Optional[dict]
        output = self._backend.execute('get_session', session_id=session_id)\
            # type: typing.Optional[dict]
        return output

    def get_user(self, user_id, cache=False, cache_ttl=None):
        # type: (int, bool, typing.Optional[int]) -> typing.Optional[dict]
        output = self._backend.execute('get_user', user_id=user_id)\
            # type: typing.Optional[dict]
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

    def teardown(self, exception):
        # type: (typing.Any) -> None
        ctx = flask._app_ctx_stack.top
        if hasattr(ctx, 'phphbb3_backend'):
            ctx.phpbb3_backend.close()
