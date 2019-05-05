from __future__ import absolute_import

import unittest

import flask_phpbb3.backends.psycopg2

import mock

import werkzeug.contrib.cache


@mock.patch('flask_phpbb3.backends.psycopg2.Psycopg2Backend._db')
class TestExecuteOperation(unittest.TestCase):
    def setUp(self):
        # type: () -> None
        self.connection = flask_phpbb3.backends.psycopg2.Psycopg2Backend(
            werkzeug.contrib.cache.SimpleCache(),
            {
                'TABLE_PREFIX': '',
            }
        )

    def test_get_query(self, mocked_db):
        # type: (mock.Mock) -> None
        parameters = mock.Mock()
        cursor = mock.Mock()
        cursor.fetchone.return_value = {'key': 'value'}
        mocked_db.cursor.return_value = cursor

        actual_value = self.connection._execute_operation(
            'get',
            'select * from somewhere',
            parameters
        )

        self.assertEqual(actual_value, {'key': 'value'})
        cursor.execute.assert_called_once_with(
            'select * from somewhere',
            parameters
        )

    def test_has_query_negative(self, mocked_db):
        # type: (mock.Mock) -> None
        cursor = mock.Mock()
        cursor.fetchone.return_value = 0
        mocked_db.cursor.return_value = cursor

        actual_value = self.connection._execute_operation(
            'has',
            'select * from somewhere',
            {}
        )

        self.assertFalse(actual_value)

    def test_has_query_positive(self, mocked_db):
        # type: (mock.Mock) -> None
        cursor = mock.Mock()
        cursor.fetchone.return_value = 1
        mocked_db.cursor.return_value = cursor

        actual_value = self.connection._execute_operation(
            'has',
            'select * from somewhere',
            {}
        )

        self.assertTrue(actual_value)

    def test_fetch_query(self, mocked_db):
        # type: (mock.Mock) -> None
        expected_value = [{'key': 1}, {'key': 2}]
        cursor = mock.Mock()
        cursor.__iter__ = mock.Mock(return_value=iter(expected_value))
        mocked_db.cursor.return_value = cursor

        actual_value = self.connection._execute_operation(
            'fetch',
            'select * from somewhere',
            {}
        )

        self.assertEqual(actual_value, expected_value)

    def test_set_query(self, mocked_db):
        # type: (mock.Mock) -> None
        cursor = mock.Mock()
        mocked_db.cursor.return_value = cursor

        actual_value = self.connection._execute_operation(
            'set',
            'select * from somewhere',
            {}
        )

        self.assertEqual(actual_value, cursor.statusmessage)
        mocked_db.commit.assert_called_once_with()

    def test_unknown_query(self, mocked_db):
        # type: (mock.Mock) -> None
        actual_value = self.connection._execute_operation(
            'unknown_op',
            'select * from somewhere',
            {}
        )

        # Internal function, this should never happen
        self.assertIsNone(actual_value)


@mock.patch('flask_phpbb3.backends.psycopg2.Psycopg2Backend._db')
class TestPreparedCustomFieldsStatements(unittest.TestCase):
    def test_empty(self, mocked_db):
        connection = flask_phpbb3.backends.psycopg2.Psycopg2Backend(
            werkzeug.contrib.cache.SimpleCache(),
            {
                'TABLE_PREFIX': '',
                'CUSTOM_USER_FIELDS': [],
            }
        )

        self.assertListEqual(
            connection._functions.keys(),
            [
                'has_membership_resolve',
                'get_autologin',
                'get_session',
                'has_membership',
                'fetch_acl_options',
                'get_unread_notifications_count',
                'get_user',
                'get_user_profile',
            ]
        )

    def test_valid(self, mocked_db):
        connection = flask_phpbb3.backends.psycopg2.Psycopg2Backend(
            werkzeug.contrib.cache.SimpleCache(),
            {
                'TABLE_PREFIX': '',
                'CUSTOM_USER_FIELDS': ['some_field', 'another_field'],
            }
        )

        self.assertSetEqual(
            set(connection._functions.keys()),
            set([
                'has_membership_resolve',
                'get_autologin',
                'get_session',
                'set_some_field',
                'has_membership',
                'fetch_acl_options',
                'set_another_field',
                'get_unread_notifications_count',
                'get_user',
                'get_user_profile',
            ]),
        )


@mock.patch('flask_phpbb3.backends.psycopg2.Psycopg2Backend._db')
class TestPreparedCustomStatements(unittest.TestCase):
    def test_empty(self, mocked_db):
        connection = flask_phpbb3.backends.psycopg2.Psycopg2Backend(
            werkzeug.contrib.cache.SimpleCache(),
            {
                'TABLE_PREFIX': '',
                'CUSTOM_STATEMENTS': {},
            }
        )

        self.assertListEqual(
            connection._functions.keys(),
            [
                'has_membership_resolve',
                'get_autologin',
                'get_session',
                'has_membership',
                'fetch_acl_options',
                'get_unread_notifications_count',
                'get_user',
                'get_user_profile',
            ]
        )

    def test_addition(self, mocked_db):
        connection = flask_phpbb3.backends.psycopg2.Psycopg2Backend(
            werkzeug.contrib.cache.SimpleCache(),
            {
                'TABLE_PREFIX': '',
                'CUSTOM_STATEMENTS': {
                    'some_custom_statement': 'some query',
                },
            }
        )

        self.assertListEqual(
            connection._functions.keys(),
            [
                'has_membership_resolve',
                'get_autologin',
                'get_session',
                'has_membership',
                'fetch_acl_options',
                'get_unread_notifications_count',
                'some_custom_statement',
                'get_user',
                'get_user_profile',
            ]
        )
        self.assertEqual(
            connection._functions['some_custom_statement'],
            'some query',
        )

    def test_override(self, mocked_db):
        connection = flask_phpbb3.backends.psycopg2.Psycopg2Backend(
            werkzeug.contrib.cache.SimpleCache(),
            {
                'TABLE_PREFIX': '',
                'CUSTOM_STATEMENTS': {
                    'get_autologin': 'overriden',
                },
            }
        )

        self.assertListEqual(
            connection._functions.keys(),
            [
                'has_membership_resolve',
                'get_autologin',
                'get_session',
                'has_membership',
                'fetch_acl_options',
                'get_unread_notifications_count',
                'get_user',
                'get_user_profile',
            ]
        )
        self.assertEqual(
            connection._functions['get_autologin'],
            'overriden',
        )
