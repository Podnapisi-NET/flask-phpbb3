from __future__ import absolute_import

import json
import typing

import flask
import flask.sessions
import flask.wrappers

ANONYMOUS_CACHE_TTL = 3600 * 24
ACL_OPTIONS_CACHE_TTL = 3600 * 1


class PhpBB3Session(dict, flask.sessions.SessionMixin):
    def __init__(self):
        # type: () -> None
        # Some session related variables
        self.modified = False
        self.new = False
        self._read_only_properties = set([])  # type: set

        # Some ACL related things
        self._acl_options = None  # type: typing.Optional[dict]
        self._acl = None  # type: typing.Optional[dict]
        self._acl_cache = {}  # type: typing.Dict[str, typing.Dict[str, bool]]

        # Per request cache
        # This should not be cached into session, but per
        # request should not be executed multiple times
        self._request_cache = {}  # type: dict

    def __setitem__(self, key, value):
        # type: (str, str) -> None
        modified = self.get(key) != value
        super(PhpBB3Session, self).__setitem__(key, value)
        if key not in self._read_only_properties:
            self.modified |= modified

    def __delitem__(self, key):
        # type: (str) -> None
        super(PhpBB3Session, self).__delitem__(key)
        self.modified = True

    def pop(self, *args, **kwargs):
        # type: (*typing.Any, **typing.Any) -> typing.Any
        """Wrapper to set modified."""
        self.modified = True
        return super(PhpBB3Session, self).pop(*args, **kwargs)

    def clear(self):
        # type: () -> None
        self.modified = True
        return super(PhpBB3Session, self).clear()

    @property
    def is_authenticated(self):
        # type: () -> bool
        """Helper method to test if user is authenticated."""
        user_id = int(self.get('user_id', 1))
        return user_id > 1

    def is_member(self, group):
        # type: (typing.Union[int, str]) -> bool
        """Tests if user is a member of specified group."""
        from flask import current_app

        if isinstance(group, int):
            # Try with default group
            if group == self['group_id']:
                return True

            # Access database
            return bool(current_app.phpbb3.has_membership(
                user_id=self['user_id'],
                group_id=group
            ))
        else:
            # Use group name
            return bool(current_app.phpbb3.has_membership_resolve(
                user_id=self['user_id'],
                group_name=group
            ))

    def _load_acl(self):
        # type: () -> None
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

            for opt in current_app.phpbb3.cached_fetch_acl_options(
                cache_ttl=ACL_OPTIONS_CACHE_TTL,
                limit=None
            ):
                if opt['is_local'] == 1:
                    self._acl_options['local'][opt['auth_option']] =\
                        local_index
                    local_index += 1
                if opt['is_global'] == 1:
                    self._acl_options['global'][opt['auth_option']] =\
                        global_index
                    global_index += 1
                # TODO By looking phpbb3 code, here also comes translation
                # option <=> id

            # Store it into cache
            current_app.phpbb3._cache.set('_acl_options', self._acl_options)

        if not self._acl:
            # Load/transform user's ACL data
            seq_cache = {}  # type: dict
            self._acl = {}

            split_user_permissions = self['user_permissions']\
                .rstrip()\
                .splitlines()
            for f, perms in enumerate(split_user_permissions):
                if not perms:
                    continue

                # Do the conversion magic
                self._acl[str(f)] = ''
                for sub in [perms[j:j + 6] for j in range(0, len(perms), 6)]:
                    if sub in seq_cache:
                        converted = seq_cache[sub]
                    else:
                        converted = bin(int(sub, 36))[2:]
                        converted = seq_cache[sub] = '0'\
                                                     * (31 - len(converted))\
                                                     + converted

                    self._acl[str(f)] += converted

    def has_privilege(self, option, forum_id=0):
        # type: (str, int) -> bool
        """Test if user has global or local (if forum_id is set) privileges."""
        # We load the ACL
        self._load_acl()

        # Make sure it is int, and convert it into str for mapping purposes
        str_forum_id = str(int(forum_id))

        # Parse negation
        negated = option.startswith('!')
        if negated:
            option = option[1:]

        if str_forum_id not in self._acl_cache\
           or option not in self._acl_cache[str_forum_id]:
            # Default is, no permission
            self._acl_cache.setdefault(str_forum_id, {})[option] = False

            # Global permissions...
            if self._acl_options\
               and isinstance(self._acl, dict)\
               and option in self._acl_options['global']\
               and '0' in self._acl:
                try:
                    acl_option = self._acl_options['global'][option]
                    permission = self._acl['0'][acl_option]
                    self._acl_cache[str_forum_id][option] =\
                        bool(int(permission))
                except IndexError:
                    pass

            # Local permissions...
            if str_forum_id != '0'\
               and self._acl_options\
               and self._acl\
               and option in self._acl_options['local']:
                try:
                    acl_option = self._acl_options['local'][option]
                    permission =\
                        self._acl.get(str_forum_id, '0' * 31)[acl_option]
                    self._acl_cache[str_forum_id][option] |=\
                        bool(int(permission))
                except IndexError:
                    pass

        return negated ^ self._acl_cache[str_forum_id][option]

    def has_privileges(self, *options, **kwargs):
        # type: (*str, **typing.Any) -> bool
        output = False
        for option in options:
            output |= self.has_privilege(option, **kwargs)
        return output

    def get_link_hash(self, link):
        # type: (str) -> str
        """Returns link hash."""
        if not self.is_authenticated:
            return ''

        import hashlib
        return hashlib.sha1(self['user_form_salt'] + link).hexdigest()[:8]

    @property
    def num_unread_notifications(self):
        # type: () -> int
        """Returns number of unread notifications."""
        from flask import current_app
        if 'num_unread_notifications' not in self._request_cache:
            self._request_cache['num_unread_notifications'] =\
                current_app.phpbb3.get_unread_notifications_count(
                    user_id=self['user_id']
                )['num']
        return int(self._request_cache['num_unread_notifications'])


class PhpBB3SessionInterface(flask.sessions.SessionInterface):
    """A read-only session interface to access phpBB3 session."""
    session_class = PhpBB3Session

    def __init__(self, app):
        # type: (flask.Flask) -> None
        """
        Initializes session interface with app
        """
        self.cache = app.phpbb3._cache

    def open_session(self, app, request):
        # type: (flask.Flask, flask.wrappers.Request) -> PhpBB3Session
        cookie_name = app.config.get('PHPBB3_COOKIE_NAME', 'phpbb3_')

        session_id = request.args.get('sid', type=str)\
            or request.cookies.get(cookie_name + 'sid', None)
        if not session_id:
            session_id = None

        user = None
        if session_id:
            # Try to fetch session
            user = app.phpbb3.get_session(session_id=session_id)
            if user and 'username' in user:
                user['username'] = user['username'].decode('utf-8', 'ignore')
        if not user:
            # Use anonymous user
            user = app.phpbb3.cached_get_user(
                user_id=1,
                cache_ttl=ANONYMOUS_CACHE_TTL
            )

        # Create session
        session = self.session_class()

        # Set session data
        if isinstance(user, dict) and user:
            session._read_only_properties = set(user.keys())
            session.update(user)

            # Read from local storage backend
            if 'session_id' in session:
                data = self.cache.get('sessions_' + session['session_id'])
                try:
                    data = json.loads(data or '')
                except ValueError:
                    data = None
                if not isinstance(data, dict):
                    data = {}
            else:
                data = {}
            session.update(data)

        return session

    def save_session(self, app, session, response):
        # type: (flask.Flask, PhpBB3Session, flask.wrappers.Response) -> None
        """Currenlty does nothing."""
        if session.modified and session._read_only_properties:
            # Store all 'storable' properties
            data = dict([(k, v)
                         for k, v in session.items()
                         if k not in session._read_only_properties])

            if 'session_id' in session:
                # TODO Read session validity from phpbb3 config
                self.cache.set(
                    'sessions_' + session['session_id'],
                    json.dumps(data),
                    timeout=int(3600 * 1.5)
                )
