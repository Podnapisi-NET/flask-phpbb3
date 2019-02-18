from __future__ import absolute_import

import json
import typing

import flask
import flask.sessions
import flask.wrappers

import flask_phpbb3
import flask_phpbb3.backends.base

import werkzeug.contrib.cache

ANONYMOUS_CACHE_TTL = 3600 * 24


class PhpBB3Session(dict, flask.sessions.SessionMixin):
    def __init__(self):
        # type: () -> None
        # Some session related variables
        self.modified = False
        self.new = False
        self._read_only_properties = set([])  # type: set

        # Some ACL related things
        self._acl = None\
            # type: typing.Optional[flask_phpbb3.backends.base.UserAcl]

        # Per request cache
        # This should not be cached into session, but per
        # request should not be executed multiple times
        self._request_cache = {}  # type: dict

    def __setitem__(self, key, value):
        # type: (str, typing.Union[str, int]) -> None
        modified = self.get(key) != value
        super(PhpBB3Session, self).__setitem__(key, value)
        if key not in self._read_only_properties:
            self.modified |= modified

    def __delitem__(self, key):
        # type: (str) -> None
        super(PhpBB3Session, self).__delitem__(key)
        self.modified = True

    @property
    def _phpbb3(self):
        # type: () -> flask_phpbb3.PhpBB3
        output = flask.current_app.phpbb3  # type: flask_phpbb3.PhpBB3
        return output

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
        if isinstance(group, int):
            # Try with default group
            if group == self['group_id']:
                return True

            # Access database
            output = self._phpbb3.has_membership(
                user_id=self['user_id'],
                group_id=group
            )
        else:
            # Use group name
            output = self._phpbb3.has_membership_resolve(
                user_id=self['user_id'],
                group_name=group
            )

        if output is None:
            return False
        return output

    def has_privilege(self, option, forum_id=0):
        # type: (str, int) -> bool
        """Test if user has global or local (if forum_id is set) privileges."""
        if not self._acl:
            self._acl = self._phpbb3.get_user_acl(self['user_permissions'])

        return self._acl.has_privilege(option, forum_id)

    def has_privileges(self, *options, **kwargs):
        # type: (*str, **int) -> bool
        forum_id = kwargs.get('forum_id', 0)

        if not self._acl:
            self._acl = self._phpbb3.get_user_acl(self['user_permissions'])
        return self._acl.has_privileges(*options, forum_id=forum_id)

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
        if 'num_unread_notifications' not in self._request_cache:
            result = self._phpbb3.get_unread_notifications_count(
                user_id=self['user_id']
            )
            if result:
                unread_count = int(result['num'])
            else:
                unread_count = 0

            self._request_cache['num_unread_notifications'] = unread_count
        else:
            unread_count = self._request_cache['num_unread_notifications']

        return unread_count


class PhpBB3SessionInterface(flask.sessions.SessionInterface):
    """A read-only session interface to access phpBB3 session."""
    session_class = PhpBB3Session

    @classmethod
    def _cache(cls, app):
        # type: (flask.Flask) -> werkzeug.contrib.cache.BaseCache
        output = app.phpbb3_cache  # type: werkzeug.contrib.cache.BaseCache
        return output

    def open_session(self, app, request):
        # type: (flask.Flask, flask.wrappers.Request) -> PhpBB3Session
        cookie_name = app.config.get('PHPBB3_COOKIE_NAME', 'phpbb3_')

        if not hasattr(app, 'phpbb3'):
            raise ValueError('App not properly configured, phpbb3 is missing!')
        phpbb3 = app.phpbb3  # type: flask_phpbb3.PhpBB3

        session_id = request.args.get('sid', type=str)\
            or request.cookies.get(cookie_name + 'sid', None)
        if not session_id:
            session_id = None

        user = None
        if session_id:
            # Try to fetch session
            user = phpbb3.get_session(session_id=session_id)
            if user and 'username' in user:
                user['username'] = user['username'].decode('utf-8', 'ignore')
        if not user:
            # Use anonymous user
            user = phpbb3.get_user(
                user_id=1,
                cache=True,
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
                cache = self._cache(app)
                data = cache.get('sessions_' + session['session_id'])
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
                self._cache(app).set(
                    'sessions_' + session['session_id'],
                    json.dumps(data),
                    timeout=int(3600 * 1.5)
                )
