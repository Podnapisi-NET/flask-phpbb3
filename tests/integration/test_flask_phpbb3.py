from __future__ import absolute_import

import typing
import unittest

import flask

import flask_phpbb3

import psycopg2
import psycopg2.extensions


DB_HOST = '127.0.0.1'
DB_ROOT_USER = 'postgres'
DB_USER = 'phpbb3_test'
DB_NAME = 'phpbb3_test'


class TestWithDatabase(unittest.TestCase):
    def setUp(self):
        # type: () -> None
        self.connection = _create_db()
        self.cursor = self.connection.cursor()\
            # type: psycopg2.extensions.cursor

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
        # Inject connection
        self.ctx.phpbb3_db = self.connection

        # Setup client
        self.client = self.app.test_client()

    def tearDown(self):
        # type: () -> None
        self.ctx.pop()
        self.connection.rollback()

        self.cursor.close()
        self.connection.close()
        _destory_db()


class TestGetUser(TestWithDatabase):
    def test_anonymous_user(self):
        # type: () -> None
        anonymous_user = self.app.phpbb3.get_user(user_id=1)
        self.assertEqual(anonymous_user['username'], 'Anonymous')
        self.assertEqual(anonymous_user['user_id'], 1)

    def test_user(self):
        # type: () -> None
        _create_user(self.cursor)

        user = self.app.phpbb3.get_user(user_id=2)
        self.assertEqual(user['username'], 'test')
        self.assertEqual(user['user_id'], 2)

    def test_unknown_user(self):
        # type: () -> None
        unknown_user = self.app.phpbb3.get_user(user_id=2)
        self.assertEqual(unknown_user, None)


class TestFetch(TestWithDatabase):
    def test_paging(self):
        # type: () -> None
        _create_privilege(self.cursor, 'm_edit')
        _create_privilege(self.cursor, 'm_delete')
        _create_privilege(self.cursor, 'm_some_random')

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


class TestSession(TestWithDatabase):
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
        _create_user(self.cursor)

        data = self.client.get('/?sid=123').data
        self.assertEqual(data, '1,Anonymous')

    def test_user_by_args(self):
        # type: () -> None
        _create_user(self.cursor)
        _create_session(self.cursor, self.session_id, 2)

        data = self.client.get('/?sid=' + self.session_id).data
        self.assertEqual(data, '2,test')

    def test_user_by_cookie(self):
        # type: () -> None
        _create_user(self.cursor)
        _create_session(self.cursor, self.session_id, 2)

        self.client.set_cookie('127.0.0.1', 'phpbb3_sid', self.session_id)
        data = self.client.get('/').data
        self.assertEqual(data, '2,test')
        self.client.delete_cookie('127.0.0.1', 'phpbb3_sid')

    def test_storage(self):
        # type: () -> None
        _create_user(self.cursor)
        _create_session(self.cursor, self.session_id, 2)

        self.client.set_cookie('127.0.0.1', 'phpbb3_sid', self.session_id)
        data = self.client.get('/data').data
        self.assertEqual(data, '')

        self.client.get('/data/something')

        data = self.client.get('/data').data
        self.assertEqual(data, 'something')

    def test_privilege(self):
        # type: () -> None
        _create_user(self.cursor)
        _create_session(self.cursor, self.session_id, 2)
        _create_privilege(self.cursor, 'm_edit')
        _grant_privilege(self.cursor, 2)

        data = self.client.get('/priv_test').data
        self.assertEqual(data, 'False,False,False')

        # We do a login via phpbb3 :P
        self.client.set_cookie('127.0.0.1', 'phpbb3_sid', self.session_id)

        data = self.client.get('/priv_test').data
        self.assertEqual(data, 'True,False,True')


def _create_user(cursor):
    # type: (psycopg2.extensions.cursor) -> None
    cursor.execute(
        "insert into"
        " phpbb_users (username, username_clean)"
        " values ('test', 'test')"
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


def _create_privilege(cursor, privilege):
    # type: (psycopg2.extensions.cursor, str) -> None
    cursor.execute(
        "insert into"
        " phpbb_acl_options (auth_option, is_global)"
        " values (%(privilege)s, 1)", {
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
    # type: () -> psycopg2.extensions.connection
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

    schema_sql = open('./tests/fixtures/postgres/schema.sql', 'r').read()
    connection = _get_connection(DB_HOST, DB_USER, DB_NAME)
    cursor_schema = connection.cursor()  # type: psycopg2.extensions.cursor
    cursor_schema.execute(schema_sql)
    cursor_schema.close()

    return connection


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
        connection_factory=psycopg2.extras.DictConnection,
    )
    return connection
