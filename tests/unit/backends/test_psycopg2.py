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
