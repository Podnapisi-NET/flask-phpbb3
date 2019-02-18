from __future__ import absolute_import

import unittest

import flask_phpbb3.backends.base

import mock


class TestSessionHasPrivilege(unittest.TestCase):
    def setUp(self):
        # type: () -> None
        user_acl = {
            '0': ['0'] * 31,
            '5': ['0'] * 31,
        }
        user_acl['0'][0] = '1'
        user_acl['0'][3] = '1'
        user_acl['5'][3] = '1'

        self.user_acl = flask_phpbb3.backends.base.UserAcl([], '')
        self.user_acl._acl_options = {
            'local': {
                'm_edit': 0,
                'm_view': 1,
                'm_review': 3,
                'm_strange': 50,
            },
            'global': {
                'm_edit': 0,
                'm_view': 1,
                'm_delete': 3,
                'm_strange': 50,
            },
        }

        self.user_acl._acl = {
            '0': ''.join(user_acl['0']),
            '5': ''.join(user_acl['5']),
        }

    def test_existing(self):
        # type: () -> None
        actual_result = self.user_acl.has_privilege(
            'm_edit',
        )
        self.assertTrue(actual_result)

        actual_result = self.user_acl.has_privilege(
            'm_view',
        )
        self.assertFalse(actual_result)

    def test_global(self):
        # type: () -> None
        # m_review is not global, and is false (even tho on global the index
        # is set to true)
        actual_result = self.user_acl.has_privilege(
            'm_review'
        )
        self.assertFalse(actual_result)

        # m_delete is global, and is True
        # Do note, both privileges have same index, just on different plains
        actual_result = self.user_acl.has_privilege(
                'm_delete'
            )
        self.assertTrue(actual_result)

    def test_local(self):
        # type: () -> None
        # Now, this is True since we are on local level
        actual_result = self.user_acl.has_privilege(
            'm_review',
            forum_id=5
        )
        self.assertTrue(actual_result)

        # True, because globals are always set
        actual_result = self.user_acl.has_privilege(
            'm_delete',
            forum_id=5
        )
        self.assertTrue(actual_result)

        actual_result = self.user_acl.has_privilege(
            'm_edit',
            forum_id=5
        )
        self.assertTrue(actual_result)

        actual_result = self.user_acl.has_privilege(
            'm_view',
            forum_id=5
        )
        self.assertFalse(actual_result)

    def test_negated(self):
        # type: () -> None
        actual_result = self.user_acl.has_privilege(
            '!m_review',
            forum_id=5
        )
        self.assertFalse(actual_result)

        actual_result = self.user_acl.has_privilege(
            '!m_review'
        )
        self.assertTrue(actual_result)

        actual_result = self.user_acl.has_privilege(
            '!m_edit'
        )
        self.assertFalse(actual_result)

        actual_result = self.user_acl.has_privilege(
            '!m_edit',
            forum_id=5
        )
        self.assertFalse(actual_result)

    def test_out_of_bound(self):
        # type: () -> None
        actual_result = self.user_acl.has_privilege(
            'm_strange'
        )
        self.assertFalse(actual_result)

        actual_result = self.user_acl.has_privilege(
            'm_strange',
            forum_id=5
        )
        self.assertFalse(actual_result)

    def test_unknown(self):
        # type: () -> None
        actual_result = self.user_acl.has_privilege(
            'm_unknown'
        )
        self.assertFalse(actual_result)

        actual_result = self.user_acl.has_privilege(
            'm_unknown',
            forum_id=5
        )
        self.assertFalse(actual_result)

        actual_result = self.user_acl.has_privilege(
            'm_unknown',
            forum_id=2
        )
        self.assertFalse(actual_result)


class TestSessionHasPrivileges(unittest.TestCase):
    def setUp(self):
        # type: () -> None
        self.user_acl = flask_phpbb3.backends.base.UserAcl(
            raw_acl_options=[],
            raw_user_permissions='',
        )

    @mock.patch('flask_phpbb3.backends.base.UserAcl.has_privilege')
    def test_combinations(self, has_privilege_mock):
        # type: (mock.Mock) -> None
        privileges = ('m_edit', 'm_delete', 'm_view')
        has_privilege_mock.return_value = False

        actual_result = self.user_acl.has_privileges(*privileges)
        self.assertFalse(actual_result)

        has_privilege_mock.side_effect = [False, False, True]
        actual_result = self.user_acl.has_privileges(*privileges)
        self.assertTrue(actual_result)

        has_privilege_mock.side_effect = [True, False, False]
        actual_result = self.user_acl.has_privileges(*privileges)
        self.assertTrue(actual_result)

        has_privilege_mock.side_effect = [True, True, True]
        actual_result = self.user_acl.has_privileges(*privileges)
        self.assertTrue(actual_result)

    @mock.patch('flask_phpbb3.backends.base.UserAcl.has_privilege',
                return_value=False)
    def test_per_forum(self, has_privilege_mock):
        # type: (mock.Mock) -> None
        privileges = ('m_edit', 'm_delete', 'm_view')

        self.user_acl.has_privileges(*privileges)
        has_privilege_mock.assert_has_calls([
            mock.call('m_edit', forum_id=0),
            mock.call('m_delete', forum_id=0),
            mock.call('m_view', forum_id=0),
        ], any_order=True)

        has_privilege_mock.reset_mock()
        self.user_acl.has_privileges(*privileges, forum_id=2)
        has_privilege_mock.assert_has_calls([
            mock.call('m_edit', forum_id=2),
            mock.call('m_delete', forum_id=2),
            mock.call('m_view', forum_id=2),
        ], any_order=True)
