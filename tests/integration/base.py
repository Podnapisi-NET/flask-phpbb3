from __future__ import absolute_import

import typing
import unittest

import flask

import flask_phpbb3

import psycopg2
import psycopg2.extensions
import psycopg2.extras


DB_HOST = '127.0.0.1'
DB_ROOT_USER = 'postgres'
DB_USER = 'phpbb3_test'
DB_NAME = 'phpbb3_test'


def setUpModule():
    # type: () -> None
    _create_db()
    connection = _get_connection(DB_HOST, DB_USER, DB_NAME)
    _init_schema(connection)
    connection.commit()


def tearDownModule():
    # type: () -> None
    _destory_db()


class TestWithDatabase(unittest.TestCase):
    def setUp(self):
        # type: () -> None
        self.app = flask.Flask('test_app')
        self.app.config.update({
            'PHPBB3': {
                'DRIVER': 'psycopg2',
                'VERSION': '3.2',
            },
            'PHPBB3_DATABASE': {
                'HOST': DB_HOST,
                'DATABASE': DB_NAME,
                'USER': DB_USER,
                'PASSWORD': '',
                'TABLE_PREFIX': 'phpbb_',
            },
        })
        self.phpbb3 = flask_phpbb3.PhpBB3(self.app)

        # From these lines devil is born
        @self.app.route('/')
        def index():
            # type: () -> typing.Any
            return flask.render_template_string(
                '{{ session.user_id}},{{ session.username }}'
            )

        @self.app.route('/data')
        def data():
            # type: () -> typing.Any
            return flask.render_template_string(
                '{{ session.custom_var}}'
            )

        @self.app.route('/data/<package>')
        def set_data(package):
            # type: (str) -> typing.Any
            flask.session['custom_var'] = package
            return flask.render_template_string(
                'Done :o'
            )

        @self.app.route('/priv_test')
        def test_privileges():
            # type: () -> typing.Any
            return flask.render_template_string(
                "{{ session.has_privilege('m_edit') }},"
                "{{ session.has_privilege('m_delete') }},"
                "{{ session.is_authenticated }}"
            )

        self.ctx = self.app.app_context()
        self.ctx.push()

        # Init connection
        self.connection = self.phpbb3._backend._db
        self.cursor = self.connection.cursor()\
            # type: psycopg2.extensions.cursor

        # Setup client
        self.client = self.app.test_client()

    def tearDown(self):
        # type: () -> None
        self.connection.rollback()
        self.cursor.close()

        self.ctx.pop()


def _create_user(cursor):
    # type: (psycopg2.extensions.cursor) -> None
    cursor.execute(
        "insert into"
        " phpbb_users (user_id, username, username_clean)"
        " values (2, 'test', 'test')"
    )


def _create_session(cursor, session_id, user_id):
    # type: (psycopg2.extensions.cursor, str, int) -> None
    cursor.execute(
        "insert into"
        " phpbb_sessions (session_id, session_user_id)"
        " values (%(session_id)s, %(user_id)s)", {
            'session_id': session_id,
            'user_id': user_id,
        }
    )


def _create_privilege(cursor, privilege_id, privilege):
    # type: (psycopg2.extensions.cursor, int, str) -> None
    cursor.execute(
        "insert into"
        " phpbb_acl_options (auth_option_id, auth_option, is_global)"
        " values (%(privilege_id)s, %(privilege)s, 1)", {
            'privilege_id': privilege_id,
            'privilege': privilege,
        }
    )


def _grant_privilege(cursor, user_id):
    # type: (psycopg2.extensions.cursor, int) -> None
    # Cryptic value to  allow only m_edit permission
    permission_set = 'HRA0HS'
    cursor.execute(
        "update phpbb_users"
        " set"
        " user_permissions=%(permission_set)s"
        " where user_id=%(user_id)s", {
            'user_id': user_id,
            'permission_set': permission_set,
        }
    )


def _create_db():
    # type: () -> None
    connection = _get_connection(DB_HOST, DB_ROOT_USER, DB_ROOT_USER)
    connection.set_isolation_level(0)

    cursor = connection.cursor()  # type: psycopg2.extensions.cursor
    cursor.execute('create user {user}'.format(user=DB_USER))
    cursor.execute('create database {db_name} owner {user};'.format(
            user=DB_USER,
            db_name=DB_NAME,
        )
    )
    cursor.close()
    connection.close()


def _init_schema(connection):
    # type: (psycopg2.extensions.connection) -> None
    schema_sql = open('./tests/fixtures/postgres/schema.sql', 'r').read()
    cursor_schema = connection.cursor()  # type: psycopg2.extensions.cursor
    cursor_schema.execute(schema_sql)
    cursor_schema.close()


def _destory_db():
    # type: () -> None
    connection = _get_connection(DB_HOST, DB_ROOT_USER, DB_ROOT_USER)
    connection.set_isolation_level(0)

    cursor = connection.cursor()  # type: psycopg2.extensions.cursor
    cursor.execute('drop database {db_name};'.format(
            db_name=DB_NAME,
        )
    )
    cursor.execute('drop user {user}'.format(user=DB_USER))
    cursor.close()
    connection.close()


def _get_connection(host, user, database):
    # type: (str, str, str) -> psycopg2.extensions.connection
    connection_string = (
        'dbname={db_name}'
        ' user={user}'
    )
    if host:
        connection_string += ' host={db_host}'

    connection = psycopg2.connect(
        connection_string.format(
            db_name=database,
            db_host=host,
            user=user,
        ),
    )
    return connection
