Flask-phpBB3
============

Connector for Flask with phpBB3. Do note, this connector does not use any caches
and is *read-only*.

Supported drivers
-----------------

  * Direct access

    + psycopg2 - direct access to PostgreSQL

  * Api access

    + api (not fully implemented, the phpBB3 connector not written yet)

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

  * PHPBB3_API - These settings are used when using API access drivers

    + **URL** - URL of the API export, default is http://127.0.0.1/connector
    + **SECRET** - Secret key to use when invoking API calls

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

get_autologin(key)
++++++++++++++++++

Checks if specific autologin key exists and returns user data. This method does not
contain validity checks if using direct access approach.

get_session(session_id)
+++++++++++++++++++++++

Gets user session. Usable for integrating with phpBB3 sessions.

Remember to check user id and session id! Currenlty only database session storage is
supported.

get_user(user_id)
+++++++++++++++++

Gets user settings and profile.

register_function(function_name, callable_or_sql)
+++++++++++++++++++++++++++++++++++++++++++++++++

If you need a special function, you can specify it with this function. First parameter
is function name, to be accessable as other functions, and the second parameter is a
callable function or SQL query.

Use string named interpolation format (the psycopg one) to specify kwargs of a function.
Do not forget to use {TABLE_PREFFIX} variable, to add specific table prefix. (First, the
python variables from config get evaluated, and then psycopg variables).

Sessions integration
--------------------

This extension also comes with session interface to use phpBB3's own sessions with your
Flask application. Usage is quite simple:

.. code:: python

  from flask import Flask
  from flask.ext.phpbb3 import PhpBB3, PhpBB3SessionInterface

  # Create app and add phpBB3 session interface
  app = Flask(__name__)
  app.session_interface = PhpBB3SessionInterface()

  # Do not forget to initialize phpBB3 extension
  phpbb3 = PhpBB3(app)

And you can use session's **is_authenticated** property to test if user is authenticated.

.. code:: python

  from flask import session

  # ...

  if session.is_authenticated:
    print 'User is authenticated!'
