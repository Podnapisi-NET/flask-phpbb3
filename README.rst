Flask-phpBB3
============

Connector for Flask with phpBB3. Do note, this connector does not use any caches
and is *read-only*.

Supported DB APIs
-----------------

  * psycopg2

API
---

Usage of this connector is simple, just create it as any extension
::

  phpbb3 = PhpBB3(app)

And in your views just call the apropriate API call:

::

  @...
  def view(...):
    ...
    latest_posts = phpbb3.fetch_latest_posts()
    ...

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

get_autologin(user_id, key)
+++++++++++++++++++++++++++

Checks if specific user_id - key pair exists and returns user data. It is the
choice of website developer if autologin should be trusted without sending the user
to phpBB3 board.

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
