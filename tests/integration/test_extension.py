from __future__ import absolute_import

import mock

from . import base

setUpModule = base.setUpModule
tearDownModule = base.tearDownModule


class TestExtension(base.TestWithDatabase):
    @mock.patch('flask_phpbb3.backends.psycopg2.Psycopg2Backend.close')
    def test_teardown(self, mocked_close):
        # type: (mock.Mock) -> None
        self.ctx.pop()
        mocked_close.assert_called()
        self.ctx.push()


class TestGetUser(base.TestWithDatabase):
    def test_anonymous_user(self):
        # type: () -> None
        anonymous_user = self.app.phpbb3.get_user(user_id=1)
        self.assertEqual(anonymous_user['username'], 'Anonymous')
        self.assertEqual(anonymous_user['user_id'], 1)

    def test_user(self):
        # type: () -> None
        base._create_user(self.cursor)

        user = self.app.phpbb3.get_user(user_id=2)
        self.assertEqual(user['username'], 'test')
        self.assertEqual(user['user_id'], 2)

    def test_unknown_user(self):
        # type: () -> None
        unknown_user = self.app.phpbb3.get_user(user_id=2)
        self.assertEqual(unknown_user, None)


class TestFetch(base.TestWithDatabase):
    def test_paging(self):
        # type: () -> None
        base._create_privilege(self.cursor, 1, 'm_edit')
        base._create_privilege(self.cursor, 2, 'm_delete')
        base._create_privilege(self.cursor, 3, 'm_some_random')

        expected_privileges = [(0, [{
            'auth_option': 'm_edit',
            'auth_option_id': 1,
            'founder_only': 0,
            'is_global': 1,
            'is_local': 0,
        }]), (1, [{
            'auth_option': 'm_delete',
            'auth_option_id': 2,
            'founder_only': 0,
            'is_global': 1,
            'is_local': 0,
        }]), (2, [{
            'auth_option': 'm_some_random',
            'auth_option_id': 3,
            'founder_only': 0,
            'is_global': 1,
            'is_local': 0,
        }]), (3, [])]

        for skip in range(0, 4):
            privilege = self.app.phpbb3.fetch_acl_options(skip=skip, limit=1)
            self.assertEqual((skip, privilege), expected_privileges[skip])


class TestSession(base.TestWithDatabase):
    def setUp(self):
        # type: () -> None
        super(TestSession, self).setUp()
        self.session_id = '123'

    def test_anonymous(self):
        # type: () -> None
        data = self.client.get('/').data
        self.assertEqual(data, '1,Anonymous')

    def test_invalid_session(self):
        # type: () -> None
        base._create_user(self.cursor)

        data = self.client.get('/?sid=123').data
        self.assertEqual(data, '1,Anonymous')

    def test_user_by_args(self):
        # type: () -> None
        base._create_user(self.cursor)
        base._create_session(self.cursor, self.session_id, 2)

        data = self.client.get('/?sid=' + self.session_id).data
        self.assertEqual(data, '2,test')

    def test_user_by_cookie(self):
        # type: () -> None
        base._create_user(self.cursor)
        base._create_session(self.cursor, self.session_id, 2)

        self.client.set_cookie('127.0.0.1', 'phpbb3_sid', self.session_id)
        data = self.client.get('/').data
        self.assertEqual(data, '2,test')
        self.client.delete_cookie('127.0.0.1', 'phpbb3_sid')

    def test_storage(self):
        # type: () -> None
        base._create_user(self.cursor)
        base._create_session(self.cursor, self.session_id, 2)

        self.client.set_cookie('127.0.0.1', 'phpbb3_sid', self.session_id)
        data = self.client.get('/data').data
        self.assertEqual(data, '')

        self.client.get('/data/something')

        data = self.client.get('/data').data
        self.assertEqual(data, 'something')

    def test_storage_invalid_id(self):
        # type: () -> None
        data = self.client.get('/data').data
        self.assertEqual(data, '')

        self.client.get('/data/something')

        data = self.client.get('/data').data
        self.assertEqual(data, '')

    def test_privilege(self):
        # type: () -> None
        base._create_user(self.cursor)
        base._create_session(self.cursor, self.session_id, 2)
        base._create_privilege(self.cursor, 1, 'm_edit')
        base._grant_privilege(self.cursor, 2)

        data = self.client.get('/priv_test').data
        self.assertEqual(data, 'False,False,False')

        # We do a login via phpbb3 :P
        self.client.set_cookie('127.0.0.1', 'phpbb3_sid', self.session_id)

        data = self.client.get('/priv_test').data
        self.assertEqual(data, 'True,False,True')
