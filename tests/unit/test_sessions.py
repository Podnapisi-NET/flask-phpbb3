from __future__ import absolute_import

import hashlib
import unittest

import flask_phpbb3.sessions

import mock


class TestSession(unittest.TestCase):
    def setUp(self):
        # type: () -> None
        self.session = flask_phpbb3.sessions.PhpBB3Session()


class TestSessionMutability(TestSession):
    def test_main(self):
        # type: () -> None
        self.assertFalse(self.session.modified)

        self.session['a_key'] = 'some_value'
        self.assertTrue(self.session.modified)

    def test_double_set(self):
        # type: () -> None
        self.assertFalse(self.session.modified)

        self.session['a_key'] = 'some_value'

        self.session['a_key'] = 'some_value'
        self.assertTrue(self.session.modified)

    def test_same_value(self):
        # type: () -> None
        self.assertFalse(self.session.modified)

        self.session['a_key'] = None  # type: ignore
        self.assertFalse(self.session.modified)

    def test_deletion(self):
        # type: () -> None
        self.session['a_key'] = 'some_value'
        self.session.modified = False

        self.assertFalse(self.session.modified)

        del self.session['a_key']
        self.assertTrue(self.session.modified)

    def test_pop(self):
        # type: () -> None
        self.session['a_key'] = 'some_value'
        self.session.modified = False
        self.assertFalse(self.session.modified)

        actual_result = self.session.pop('a_key')
        self.assertEqual(actual_result, 'some_value')
        self.assertTrue(self.session.modified)

    def test_read_only(self):
        # type: () -> None
        self.session._read_only_properties.add('a_key')
        self.assertFalse(self.session.modified)

        self.session['a_key'] = 'some_value'
        self.assertFalse(self.session.modified)

    def test_clear(self):
        # type: () -> None
        self.assertFalse(self.session.modified)

        self.session.clear()
        self.assertTrue(self.session.modified)


class TestSessionUser(TestSession):
    def test_authenticated(self):
        # type: () -> None
        self.session['user_id'] = '1'
        self.assertFalse(self.session.is_authenticated)

        self.session['user_id'] = '2'
        self.assertTrue(self.session.is_authenticated)

        del self.session['user_id']
        self.assertFalse(self.session.is_authenticated)

        self.session['user_id'] = '-1'
        self.assertFalse(self.session.is_authenticated)

    def test_get_link_hash(self):
        # type: () -> None
        some_link = '/my/link'
        self.session['user_form_salt'] = 'some_salt'

        self.session['user_id'] = '1'
        self.assertEqual(self.session.get_link_hash(some_link), '')

        self.session['user_id'] = '3'
        salted_link = self.session['user_form_salt'] + some_link
        expected_value = hashlib.sha1(salted_link).hexdigest()[:8]
        self.assertEqual(self.session.get_link_hash(some_link), expected_value)


class TestSessionUserMembership(TestSession):
    def setUp(self):
        # type: () -> None
        super(TestSessionUserMembership, self).setUp()

        self.user_id = 2
        self.group_id = 2
        self.session['user_id'] = self.user_id
        self.session['group_id'] = 2

    def test_default_group_id(self):
        # type: () -> None
        self.session.is_member(self.group_id)

    @mock.patch('flask_phpbb3.sessions.PhpBB3Session._phpbb3')
    def test_group_id(self, patched_phpbb3):
        # type: (mock.Mock) -> None
        patched_phpbb3.has_membership.return_value = True

        actual_result = self.session.is_member(5)
        self.assertTrue(actual_result)
        patched_phpbb3.has_membership.assert_called_once_with(
            user_id=self.user_id,
            group_id=5,
        )

    @mock.patch('flask_phpbb3.sessions.PhpBB3Session._phpbb3')
    def test_group_id_failed(self, patched_phpbb3):
        # type: (mock.Mock) -> None
        patched_phpbb3.has_membership.return_value = False

        actual_result = self.session.is_member(5)
        self.assertFalse(actual_result)
        patched_phpbb3.has_membership.assert_called_once_with(
            user_id=self.user_id,
            group_id=5,
        )

    @mock.patch('flask_phpbb3.sessions.PhpBB3Session._phpbb3')
    def test_group_name(self, patched_phpbb3):
        # type: (mock.Mock) -> None
        patched_phpbb3.has_membership_resolve.return_value = True

        actual_result = self.session.is_member('group')
        self.assertTrue(actual_result)
        patched_phpbb3.has_membership_resolve.assert_called_once_with(
            user_id=self.user_id,
            group_name='group',
        )

    @mock.patch('flask_phpbb3.sessions.PhpBB3Session._phpbb3')
    def test_group_name_failed(self, patched_phpbb3):
        # type: (mock.Mock) -> None
        patched_phpbb3.has_membership_resolve.return_value = False

        actual_result = self.session.is_member('group')
        self.assertFalse(actual_result)
        patched_phpbb3.has_membership_resolve.assert_called_once_with(
            user_id=self.user_id,
            group_name='group',
        )

    @mock.patch('flask_phpbb3.sessions.PhpBB3Session._phpbb3')
    def test_nones(self, patched_phpbb3):
        # type: (mock.Mock) -> None
        patched_phpbb3.has_membership_resolve.return_value = None
        patched_phpbb3.has_membership.return_value = None

        actual_result = self.session.is_member(5)
        self.assertFalse(actual_result)

        actual_result = self.session.is_member('group')
        self.assertFalse(actual_result)


@mock.patch('flask_phpbb3.sessions.PhpBB3Session._phpbb3')
class TestSessionUserPrivileges(TestSession):
    def setUp(self):
        # type: () -> None
        super(TestSessionUserPrivileges, self).setUp()

        self.session['user_permissions'] = ''

    def test_load_data_privilege(self, mocked_phpbb3):
        # type: (mock.Mock) -> None
        self.session.has_privilege('m_view')

        mocked_phpbb3.get_user_acl.assert_called_once_with('')

    def test_load_data_privileges(self, mocked_phpbb3):
        # type: (mock.Mock) -> None
        self.session.has_privileges('m_view', 'm_edit')

        mocked_phpbb3.get_user_acl.assert_called_once_with('')

    def test_load_data_single(self, mocked_phpbb3):
        # type: (mock.Mock) -> None
        self.session.has_privilege('m_view')
        self.session.has_privileges('m_view', 'm_edit')

        mocked_phpbb3.get_user_acl.assert_called_once_with('')

    def test_call_privilege(self, mocked_phpbb3):
        # type: (mock.Mock) -> None
        user_acl = mock.Mock()
        mocked_phpbb3.get_user_acl.return_value = user_acl
        forum_id = mock.Mock()

        self.session.has_privilege('m_view', forum_id)

        user_acl.has_privilege.assert_called_once_with('m_view', forum_id)

    def test_call_privileges(self, mocked_phpbb3):
        # type: (mock.Mock) -> None
        user_acl = mock.Mock()
        mocked_phpbb3.get_user_acl.return_value = user_acl
        forum_id = mock.Mock()

        self.session.has_privileges('m_view', 'm_edit', forum_id=forum_id)

        user_acl.has_privileges.assert_called_once_with(
            'm_view',
            'm_edit',
            forum_id=forum_id,
        )


@mock.patch('flask_phpbb3.sessions.PhpBB3Session._phpbb3')
class TestUnreadNotificationsNum(TestSession):
    def setUp(self):
        # type: () -> None
        super(TestUnreadNotificationsNum, self).setUp()

        self.session['user_id'] = 2

    def test_main(self, mocked_phpbb3):
        # type: (mock.Mock) -> None
        mocked_phpbb3.get_unread_notifications_count.return_value = {
            'num': 3,
        }

        actual_result = self.session.num_unread_notifications
        self.assertEqual(actual_result, 3)

    def test_none(self, mocked_phpbb3):
        # type: (mock.Mock) -> None
        mocked_phpbb3.get_unread_notifications_count.return_value = None

        actual_result = self.session.num_unread_notifications
        self.assertEqual(actual_result, 0)

    def test_cache(self, mocked_phpbb3):
        # type: (mock.Mock) -> None
        mocked_phpbb3.get_unread_notifications_count.return_value = {
            'num': 3,
        }
        user_id = mock.Mock()
        self.session['user_id'] = user_id

        _ = self.session.num_unread_notifications
        _ = self.session.num_unread_notifications

        mocked_phpbb3.get_unread_notifications_count.assert_called_once_with(
            user_id=user_id,
        )
