"""
Flask-phpBB3
-------------

Extension to add integration with phpBB3. This extension does not have a session management,
it is strictly a connector to existing phpBB3 board with predefined functions.
"""
from setuptools import setup

setup(
  name = 'Flask-phpBB3',
  version = '0.1.0',
  url = 'https://github.com/MasterMind2k/flask-phpbb3',
  license = 'BSD',
  author = 'Gregor Kalisnik',
  author_email = 'gregor@kalisnik.si',
  description = 'Connector for Flask with phpBB3 board.',
  long_description = __doc__,
  py_modules = ['flask_phpbb3'],
  zip_safe = False,
  include_package_data = True,
  platforms = 'any',
  install_requires = [
    'Flask',
  ],
  extras = {
    'with_psycopg2': ['psycopg2'],
    'with_psycopg2cffi': ['psycopg2cffi'],
  },
  classifiers = [
    'Environment :: Web Environment',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: BSD License',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    'Topic :: Software Development :: Libraries :: Python Modules'
  ]
)
