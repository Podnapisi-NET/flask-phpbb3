from __future__ import absolute_import

import hashlib
import unittest

import flask_phpbb3.sessions


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
