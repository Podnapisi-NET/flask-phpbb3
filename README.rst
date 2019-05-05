Flask-phpBB3
============

Connector for Flask with phpBB3. Do note, this connector does not use any caches
and is *read-only*.

Supported drivers
-----------------

  * Direct access

    + psycopg2 - direct access to PostgreSQL

Supported phpBB3 versions
-------------------------

  * 3.1.x

Configuration
-------------

To configure this extension, you have to specify PHPBB3 and one of access modes
configs. All of them are dicts.

Settings
++++++++++++++++

  * PHPBB3

    + **DRIVER** - Which driver to use (see `Supported drivers`_)
    + **VERSION** - Which version of phpBB3 (see `Supported phpBB3 versions`_)

  * PHPBB3_DATABASE - These settings are used when using direct access drivers

    + **HOST** - Database host, default is 127.0.0.1
    + **DATABASE** - Database name, default is phpbb3
    + **USER** - User for connecting to database, default is phpbb3
    + **PASSWORD** - Database user's password, default is empty
    + **TABLE_PREFIX** - Table prefix of phpBB3 tables, default is phpbb\_
    + **CUSTOM_USER_FIELDS** - List of custom fields setup in phpBB3 forum
    + **CUSTOM_STATEMENTS** - Dictionary of prepared statements to add or
                              override. **Careful** with raw queries, use
                              `{TABLE_PREFIX}` to re-use configured prefix

  * PHPBB3_SESSION_BACKEND - Setting up session backend, it configures the werkzeug cache subsystem

    + **TYPE** - Type of the cache, *simple* or *memcached*
    + **SERVERS** - A list/tuple of Memcached servers ('host:pair', ...)
    + **KEY_PREFIX** - Key prefix used with all keys

  * **PHPBB3_COOKIE_NAME** - Sets prefix of session cookie names, default is
                             phpbb3\_

Example
+++++++

.. code:: python

  PHPBB3 = {
    'DRIVER': 'psycopg2',
  }
  PHPBB3_DATABASE = {
    'DATABASE': 'mydb',
    'USER': 'myuser',
  }

API
---

Usage of this connector is simple, just create it as any extension
::

  phpbb3 = PhpBB3(app)

And in your views just call the apropriate API call:

.. code:: python

  @app.route('/my/view')
  def view(...):
    # ...
    latest_posts = phpbb3.fetch_latest_posts()
    # ...

**IMPORTANT:** Use only keyword paramaters!

Predefined prefixes
-------------------

A prefix of a function can define it's behaviour if declared with SQL query.

get\_
+++++

It will return only one value or None.

fetch\_
+++++++

Returns a list. If defining your own functions, do not use OFFSET and LIMIT, it will
be appended by the extension.

List of functions
-----------------

get_session(session_id)
+++++++++++++++++++++++

Gets user session. Usable for integrating with phpBB3 sessions.

Remember to check user id and session id! Currenlty only database session storage is
supported.

get_user(user_id)
+++++++++++++++++

Gets user settings and profile.

Use string named interpolation format (the psycopg one) to specify kwargs of a function.
Do not forget to use {TABLE_PREFIX} variable, to add specific table prefix. (First, the
python variables from config get evaluated, and then psycopg variables).

Sessions integration
--------------------

When using this extension, it will install it's own session interface. Also, all properties
not present in phpBB3 session, will be stored in session backend.

And you can use session's **is_authenticated** property to test if user is authenticated.

.. code:: python

  from flask import session

  # ...

  if session.is_authenticated:
    print 'User is authenticated!'

Caching
-------

By default, it configures werkzeug's cache using the configuration set in PHPBB3_SESSION_BACKEND.
If you are using Flask-cache extension, you may pass it along when instantiating this extension
to use the common cache using the keyword parameter **cache**.
