from __future__ import absolute_import

import json
import typing

try:
    import psycopg2
except ImportError:
    from psycopg2cffi import compat
    compat.register()
import psycopg2.extensions
import psycopg2.extras

from . import base


class Psycopg2Backend(base.BaseBackend):
    def _setup_connection(self):
        # type: () -> None
        self._connection = psycopg2.connect(
            'dbname={DATABASE}'
            ' host={HOST}'
            ' user={USER}'
            ' password={PASSWORD}'.format(**self._config),
            connection_factory=psycopg2.extras.DictConnection
        )

    @property
    def _db(self):
        # type: () -> psycopg2.extensions.connection
        if not self._connection:
            self._setup_connection()

        return self._connection

    def _prepare_statements(self):
        # type: () -> None
        """
        Initializes prepared SQL statements, depending on version of PHPBB3
        """
        self._functions.update(dict(
            get_autologin=(
                "SELECT u.* "
                "FROM {TABLE_PREFIX}users u,"
                "     {TABLE_PREFIX}sessions_keys k "
                # FIXME Make it prettier, USER_NORMAL and USER_FOUNDER
                "WHERE u.user_type IN (0, 3)"
                "AND k.user_id=u.user_id"
                "AND k.key_id = %(key)s"
            ),
            get_session=(
                "SELECT * "
                "FROM {TABLE_PREFIX}sessions s, {TABLE_PREFIX}users u "
                "WHERE s.session_id = %(session_id)s "
                "AND s.session_user_id=u.user_id"
            ),
            get_user=(
                "SELECT * "
                "FROM {TABLE_PREFIX}users "
                "WHERE user_id = %(user_id)s"),
            get_user_profile=(
                "SELECT * "
                "FROM {TABLE_PREFIX}profile_fields_data "
                "WHERE user_id = %(user_id)s"),
            has_membership=(
                "SELECT ug.group_id "
                "FROM {TABLE_PREFIX}user_group ug "
                "WHERE ug.user_id = %(user_id)s "
                "  AND ug.group_id = %(group_id)s "
                "  AND ug.user_pending=0 "
                "LIMIT 1"
            ),
            has_membership_resolve=(
                "SELECT ug.group_id "
                "FROM {TABLE_PREFIX}user_group ug,"
                "     {TABLE_PREFIX}groups g "
                "WHERE ug.user_id = %(user_id)s "
                "  AND g.group_name = %(group_name)s "
                "  AND ug.group_id=g.group_id "
                "  AND ug.user_pending=0 "
                "LIMIT 1"
            ),
            fetch_acl_options=(
                "SELECT"
                "   *"
                " FROM"
                "   {TABLE_PREFIX}acl_options"
                " ORDER BY"
                "   auth_option_id"
            ),
            get_unread_notifications_count=(
                "SELECT"
                "   COUNT(n.*) as num"
                " FROM"
                "   {TABLE_PREFIX}notifications n,"
                "   {TABLE_PREFIX}notification_types nt"
                " WHERE"
                "   n.user_id = %(user_id)s "
                "   AND nt.notification_type_id=n.notification_type_id"
                "   AND nt.notification_type_enabled=1 "
                "   AND n.notification_read=0"
            ),
        ))

        self._prepare_custom_fields_statements()

        # TODO Add/Move to version specific queries

    def _prepare_custom_fields_statements(self):
        # type: () -> None
        """
        Prepares statements for custom fields
        """
        # Setters for custom fields
        custom_fields = self._config.get('CUSTOM_USER_FIELDS', [])
        for custom_field in custom_fields:
            self._functions["set_{0}".format(custom_field)] = (
                "UPDATE"
                "   {TABLE_PREFIX}profile_fields_data"
                " SET"
                "   `pf_{field}` = %(value)s"
                " WHERE"
                "   user_id = %(user_id)s"
            ).format(
                TABLE_PREFIX=self._config['TABLE_PREFIX'],
                field=custom_field,
            )

    def _sql_query(
        self,
        operation,  # type: str
        query,  # type: str
        cache_key_prefix=None,  # type: typing.Optional[str]
        cache_ttl=None,  # type: typing.Optional[int]
        skip=0,  # type: int
        limit=10,  # type: typing.Optional[int]
        **kwargs  # type: typing.Union[int, str]
    ):
        # type: (...) -> typing.Any
        """Executes a query with values in kwargs."""
        if operation not in self.KNOWN_OPERATIONS:
            raise ValueError("Unknown operation")

        cache_key = None
        if cache_key_prefix and operation != 'set':
            cache_key = '{name}:{arguments}'.format(
                name=cache_key_prefix,
                arguments=':'.join(key + str(value)
                                   for key, value in kwargs.items())
            )
            raw_data = self._cache.get(cache_key)
            if raw_data and isinstance(raw_data, (str, unicode)):
                try:
                    return json.loads(raw_data)
                except ValueError:
                    # Woops :S
                    pass

        if operation == 'fetch':
            query = self._paginate_query(query, skip, limit)

        output = self._execute_operation(operation, query, kwargs)

        if cache_key:
            try:
                self._cache.set(cache_key,
                                json.dumps(output),
                                cache_ttl)
            except ValueError:
                # Woops :S
                pass

        return output

    def _paginate_query(self, query, skip, limit):
        # type: (str, int, typing.Optional[int]) -> str
        output = query + ' OFFSET {:d}'.format(skip)
        if limit:
            output += ' LIMIT {:d}'.format(limit)
        return output

    def _execute_operation(
        self,
        operation,  # type: str
        query,  # type: str
        params  # type: typing.Dict[str, typing.Union[str, int]]
    ):
        # type: (...) -> typing.Any
        cursor = self._db.cursor()

        cursor.execute(
            query.format(TABLE_PREFIX=self._config['TABLE_PREFIX']),
            params
        )

        if operation == 'get':
            output = cursor.fetchone()
            if output is not None:
                output = dict(output)
        elif operation == 'has':
            output = bool(cursor.fetchone())
        elif operation == 'fetch':
            output = [dict(i) for i in cursor]
        elif operation == 'set':
            # It is an update
            output = cursor.statusmessage
            self._db.commit()
        else:
            output = None
        cursor.close()

        return output

    def execute(
        self,
        command,  # type: str
        cache=False,  # type: bool
        cache_ttl=None,  # type: typing.Optional[int]
        skip=0,  # type: int
        limit=10,  # type: typing.Optional[int]
        **kwargs  # type: typing.Union[int, str]
    ):
        # type: (...) -> typing.Any
        cache_key_prefix = None
        if cache:
            cache_key_prefix = command

        if command not in self._functions:
            raise ValueError("Function {} does not exist.".format(
                command
            ))

        operation = command.split('_')[0]

        func_or_query = self._functions[command]
        if callable(func_or_query):
            return func_or_query(**kwargs)
        else:
            return self._sql_query(
                operation,
                func_or_query,
                cache_key_prefix=cache_key_prefix,
                cache_ttl=cache_ttl,
                skip=skip,
                limit=limit,
                **kwargs
            )

    def close(self):
        # type: () -> None
        self._db.close()

    @property
    def is_closed(self):
        # type: () -> bool
        return bool(self._db.closed)
