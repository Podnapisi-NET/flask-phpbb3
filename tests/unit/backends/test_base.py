from __future__ import absolute_import

import unittest

import flask_phpbb3.backends.base


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
        self.user_acl = {
            '0': ''.join(user_acl['0']),
            '5': ''.join(user_acl['5']),
        }

        self.acl_options = {
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

    def test_existing(self):
        # type: () -> None
        actual_result =\
            flask_phpbb3.backends.base.BaseBackend.has_user_privilege(
                self.user_acl,
                self.acl_options,
                'm_edit',
            )
        self.assertTrue(actual_result)

        actual_result =\
            flask_phpbb3.backends.base.BaseBackend.has_user_privilege(
                self.user_acl,
                self.acl_options,
                'm_view',
            )
        self.assertFalse(actual_result)

    def test_global(self):
        # type: () -> None
        # m_review is not global, and is false (even tho on global the index
        # is set to true)
        actual_result =\
            flask_phpbb3.backends.base.BaseBackend.has_user_privilege(
                self.user_acl,
                self.acl_options,
                'm_review'
            )
        self.assertFalse(actual_result)

        # m_delete is global, and is True
        # Do note, both privileges have same index, just on different plains
        actual_result =\
            flask_phpbb3.backends.base.BaseBackend.has_user_privilege(
                self.user_acl,
                self.acl_options,
                'm_delete'
            )
        self.assertTrue(actual_result)

    def test_local(self):
        # type: () -> None
        # Now, this is True since we are on local level
        actual_result =\
            flask_phpbb3.backends.base.BaseBackend.has_user_privilege(
                self.user_acl,
                self.acl_options,
                'm_review',
                forum_id=5
            )
        self.assertTrue(actual_result)

        # True, because globals are always set
        actual_result =\
            flask_phpbb3.backends.base.BaseBackend.has_user_privilege(
                self.user_acl,
                self.acl_options,
                'm_delete',
                forum_id=5
            )
        self.assertTrue(actual_result)

        actual_result =\
            flask_phpbb3.backends.base.BaseBackend.has_user_privilege(
                self.user_acl,
                self.acl_options,
                'm_edit',
                forum_id=5
            )
        self.assertTrue(actual_result)

        actual_result =\
            flask_phpbb3.backends.base.BaseBackend.has_user_privilege(
                self.user_acl,
                self.acl_options,
                'm_view',
                forum_id=5
            )
        self.assertFalse(actual_result)

    def test_negated(self):
        # type: () -> None
        actual_result =\
            flask_phpbb3.backends.base.BaseBackend.has_user_privilege(
                self.user_acl,
                self.acl_options,
                '!m_review',
                forum_id=5
            )
        self.assertFalse(actual_result)

        actual_result =\
            flask_phpbb3.backends.base.BaseBackend.has_user_privilege(
                self.user_acl,
                self.acl_options,
                '!m_review'
            )
        self.assertTrue(actual_result)

        actual_result =\
            flask_phpbb3.backends.base.BaseBackend.has_user_privilege(
                self.user_acl,
                self.acl_options,
                '!m_edit'
            )
        self.assertFalse(actual_result)

        actual_result =\
            flask_phpbb3.backends.base.BaseBackend.has_user_privilege(
                self.user_acl,
                self.acl_options,
                '!m_edit',
                forum_id=5
            )
        self.assertFalse(actual_result)

    def test_out_of_bound(self):
        # type: () -> None
        actual_result =\
            flask_phpbb3.backends.base.BaseBackend.has_user_privilege(
                self.user_acl,
                self.acl_options,
                'm_strange'
            )
        self.assertFalse(actual_result)

        actual_result =\
            flask_phpbb3.backends.base.BaseBackend.has_user_privilege(
                self.user_acl,
                self.acl_options,
                'm_strange',
                forum_id=5
            )
        self.assertFalse(actual_result)

    def test_unknown(self):
        # type: () -> None
        actual_result =\
            flask_phpbb3.backends.base.BaseBackend.has_user_privilege(
                self.user_acl,
                self.acl_options,
                'm_unknown'
            )
        self.assertFalse(actual_result)

        actual_result =\
            flask_phpbb3.backends.base.BaseBackend.has_user_privilege(
                self.user_acl,
                self.acl_options,
                'm_unknown',
                forum_id=5
            )
        self.assertFalse(actual_result)

        actual_result =\
            flask_phpbb3.backends.base.BaseBackend.has_user_privilege(
                self.user_acl,
                self.acl_options,
                'm_unknown',
                forum_id=2
            )
        self.assertFalse(actual_result)
