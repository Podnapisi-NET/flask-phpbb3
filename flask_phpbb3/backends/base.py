from __future__ import absolute_import

import typing

import werkzeug.contrib.cache


class BaseBackend(object):
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
        cache,  # type: werkzeug.contrib.cache.BaseCache
        config  # type: typing.Dict[str, str]
    ):
        # type: (...) -> None
        self._functions = {}  # type: typing.Dict[str, str]
        self._cache = cache
        self._config = config

        self._prepare_statements()
        self._setup_connection()

    def _setup_connection(self):
        # type: () -> None
        raise NotImplementedError

    def _prepare_statements(self):
        # type: () -> None
        raise NotImplementedError

    @property
    def _db(self):
        # type: () -> typing.Any
        raise NotImplementedError

    def execute(
        self,
        command,  # type: str
        cache=False,  # type: bool
        cache_ttl=None,  # type: typing.Optional[int]
        **kwargs  # type: typing.Any
    ):
        # type: (...) -> typing.Any
        raise NotImplementedError

    def close(self):
        # type: () -> None
        raise NotImplementedError

    @property
    def is_closed(self):
        # type: () -> bool
        raise NotImplementedError
