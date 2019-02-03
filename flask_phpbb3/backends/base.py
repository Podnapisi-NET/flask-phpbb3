from __future__ import absolute_import

import typing

import werkzeug.contrib.cache

ACL_OPTIONS_CACHE_TTL = 3600 * 1


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

    def fetch_acl(self):
        # type: () -> dict
        acl_options = self._cache.get('_acl_options')  # type: dict

        if not acl_options:
            # Load ACL options, so we can decode the user ACL
            acl_options = {
                'local': {},
                'global': {}
            }
            local_index = 0
            global_index = 0

            results = self.execute(
                'fetch_acl_options',
                cache=True,
                cache_ttl=ACL_OPTIONS_CACHE_TTL,
                limit=None,
            )
            for opt in results or []:
                if opt['is_local'] == 1:
                    acl_options['local'][opt['auth_option']] =\
                        local_index
                    local_index += 1
                if opt['is_global'] == 1:
                    acl_options['global'][opt['auth_option']] =\
                        global_index
                    global_index += 1
                # TODO By looking phpbb3 code, here also comes translation
                # option <=> id

            # Store it into cache
            self._cache.set('_acl_options', acl_options)

        return acl_options

    def parse_user_acl(self, user_permissions):
        # type: (str) -> typing.Dict[str, str]
        seq_cache = {}  # type: dict
        user_acl = {}

        split_user_permissions = user_permissions\
            .rstrip()\
            .splitlines()
        for f, perms in enumerate(split_user_permissions):
            if not perms:
                continue

            # Do the conversion magic
            user_acl[str(f)] = ''
            for sub in [perms[j:j + 6] for j in range(0, len(perms), 6)]:
                if sub in seq_cache:
                    converted = seq_cache[sub]
                else:
                    converted = bin(int(sub, 36))[2:]
                    converted = seq_cache[sub] = '0'\
                                                 * (31 - len(converted))\
                                                 + converted

                user_acl[str(f)] += converted

        return user_acl

    @classmethod
    def has_user_privilege(self, user_acl, acl_options, privilege, forum_id=0):
        # type: (dict, dict, str, int) -> bool
        # Parse negation
        str_forum_id = str(forum_id)

        negated = privilege.startswith('!')
        if negated:
            option = privilege[1:]
        else:
            option = privilege

        acl_cache = {}  # type: dict
        acl_cache.setdefault(str_forum_id, {})[option] = False

        # Global permissions
        if acl_options\
           and isinstance(user_acl, dict)\
           and option in acl_options['global']\
           and '0' in user_acl:
            try:
                acl_option = acl_options['global'][option]
                permission = user_acl['0'][acl_option]
                acl_cache[str_forum_id][option] =\
                    bool(int(permission))
            except IndexError:
                pass

        # Local permissions
        if str_forum_id != '0'\
           and acl_options\
           and user_acl\
           and option in acl_options['local']:
            try:
                acl_option = acl_options['local'][option]
                permission =\
                    user_acl.get(str_forum_id, '0' * 31)[acl_option]
                acl_cache[str_forum_id][option] |=\
                    bool(int(permission))
            except IndexError:
                pass

        output = negated ^ acl_cache[str_forum_id][option]  # type: bool
        return output
