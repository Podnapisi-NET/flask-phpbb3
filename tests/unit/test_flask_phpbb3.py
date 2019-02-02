from __future__ import absolute_import

import hashlib
import unittest

import flask_phpbb3

import mock


class TestSession(unittest.TestCase):
    def setUp(self):
        # type: () -> None
        self.session = flask_phpbb3.PhpBB3Session()


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


class TestSessionHasPrivileges(TestSession):
    @mock.patch('flask_phpbb3.PhpBB3Session.has_privilege')
    def test_combinations(self, has_privilege_mock):
        # type: (mock.Mock) -> None
        privileges = ('m_edit', 'm_delete', 'm_view')
        has_privilege_mock.return_value = False

        actual_result = self.session.has_privileges(*privileges)
        self.assertFalse(actual_result)

        has_privilege_mock.side_effect = [False, False, True]
        actual_result = self.session.has_privileges(*privileges)
        self.assertTrue(actual_result)

        has_privilege_mock.side_effect = [True, False, False]
        actual_result = self.session.has_privileges(*privileges)
        self.assertTrue(actual_result)

        has_privilege_mock.side_effect = [True, True, True]
        actual_result = self.session.has_privileges(*privileges)
        self.assertTrue(actual_result)

    @mock.patch('flask_phpbb3.PhpBB3Session.has_privilege', return_value=False)
    def test_per_forum(self, has_privilege_mock):
        # type: (mock.Mock) -> None
        privileges = ('m_edit', 'm_delete', 'm_view')

        self.session.has_privileges(*privileges)
        has_privilege_mock.assert_has_calls([
            mock.call('m_edit'),
            mock.call('m_delete'),
            mock.call('m_view'),
        ], any_order=True)

        has_privilege_mock.reset_mock()
        self.session.has_privileges(*privileges, forum_id=2)
        has_privilege_mock.assert_has_calls([
            mock.call('m_edit', forum_id=2),
            mock.call('m_delete', forum_id=2),
            mock.call('m_view', forum_id=2),
        ], any_order=True)


@mock.patch('flask_phpbb3.PhpBB3Session._load_acl')
class TestSessionHasPrivilege(TestSession):
    def setUp(self):
        # type: () -> None
        super(TestSessionHasPrivilege, self).setUp()
        self.session._acl = {
            '0': ['0'] * 31,
            '5': ['0'] * 31,
        }
        self.session._acl['0'][0] = '1'
        self.session._acl['0'][3] = '1'
        self.session._acl['5'][3] = '1'
        self.session._acl['0'] = ''.join(self.session._acl['0'])
        self.session._acl['5'] = ''.join(self.session._acl['5'])

        self.session._acl_options = {
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

    def test_existing(self, _):
        # type: (mock.Mock) -> None
        actual_result = self.session.has_privilege('m_edit')
        self.assertTrue(actual_result)

        actual_result = self.session.has_privilege('m_view')
        self.assertFalse(actual_result)

    def test_global(self, _):
        # type: (mock.Mock) -> None
        # m_review is not global, and is false (even tho on global the index
        # is set to true)
        actual_result = self.session.has_privilege('m_review')
        self.assertFalse(actual_result)

        # m_delete is global, and is True
        # Do note, both privileges have same index, just on different plains
        actual_result = self.session.has_privilege('m_delete')
        self.assertTrue(actual_result)

    def test_local(self, _):
        # type: (mock.Mock) -> None
        # Now, this is True since we are on local level
        actual_result = self.session.has_privilege('m_review', forum_id=5)
        self.assertTrue(actual_result)

        # True, because globals are always set
        actual_result = self.session.has_privilege('m_delete', forum_id=5)
        self.assertTrue(actual_result)

        actual_result = self.session.has_privilege('m_edit', forum_id=5)
        self.assertTrue(actual_result)

        actual_result = self.session.has_privilege('m_view', forum_id=5)
        self.assertFalse(actual_result)

    def test_negated(self, _):
        # type: (mock.Mock) -> None
        actual_result = self.session.has_privilege('!m_review', forum_id=5)
        self.assertFalse(actual_result)

        actual_result = self.session.has_privilege('!m_review')
        self.assertTrue(actual_result)

        actual_result = self.session.has_privilege('!m_edit')
        self.assertFalse(actual_result)

        actual_result = self.session.has_privilege('!m_edit', forum_id=5)
        self.assertFalse(actual_result)

    def test_out_of_bound(self, _):
        # type: (mock.Mock) -> None
        actual_result = self.session.has_privilege('m_strange')
        self.assertFalse(actual_result)

        actual_result = self.session.has_privilege('m_strange', forum_id=5)
        self.assertFalse(actual_result)

    def test_unknown(self, _):
        # type: (mock.Mock) -> None
        actual_result = self.session.has_privilege('m_unknown')
        self.assertFalse(actual_result)

        actual_result = self.session.has_privilege('m_unknown', forum_id=5)
        self.assertFalse(actual_result)

        actual_result = self.session.has_privilege('m_unknown', forum_id=2)
        self.assertFalse(actual_result)


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
