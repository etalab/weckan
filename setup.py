#! /usr/bin/env python
# -*- coding: utf-8 -*-


# Weckan -- Web application using CKAN model
# By: Emmanuel Raviart <emmanuel@raviart.com>
#
# Copyright (C) 2013 Emmanuel Raviart
# http://gitorious.org/etalab/weckan
#
# This file is part of Weckan.
#
# Weckan is free software; you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# Weckan is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


"""Web application using CKAN model"""


try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages


classifiers = """\
Development Status :: 2 - Pre-Alpha
Environment :: Web Environment
Intended Audience :: Information Technology
License :: OSI Approved :: GNU Affero General Public License v3
Operating System :: POSIX
Programming Language :: Python
Topic :: Scientific/Engineering :: Information Analysis
Topic :: Sociology
Topic :: Internet :: WWW/HTTP :: WSGI :: Server
"""

doc_lines = __doc__.split('\n')


setup(
    name = 'Weckan',
    version = '0.1dev',

    author = 'Emmanuel Raviart',
    author_email = 'emmanuel@raviart.com',
    classifiers = [classifier for classifier in classifiers.split('\n') if classifier],
    description = doc_lines[0],
    keywords = 'form question server web',
    license = 'http://www.fsf.org/licensing/licenses/agpl-3.0.html',
    long_description = '\n'.join(doc_lines[2:]),
    url = 'http://gitorious.org/weckan/weckan',

    data_files = [
        ('share/locale/fr/LC_MESSAGES', ['weckan/i18n/fr/LC_MESSAGES/weckan.mo']),
        ],
    entry_points = {
#        'paste.app_factory': 'main = weckan.application:make_app',
        'paste.filter_app_factory': 'main = weckan.application:make_filter_app',
        },
    include_package_data = True,
    install_requires = [
        'Biryani1 >= 0.9dev',
        'WebError >= 0.10',
#        'WebOb >= 1.1',
        'WebOb >= 1.0.8',
        'Jinja2 >= 2.6',
        'webassets >= 0.8',
        'PyYAML',
        'cssmin',
        ],
    message_extractors = {'weckan': [
        ('**.py', 'python', None),
        ('**/templates/**.html', 'jinja2', {'encoding': 'utf-8'}),
        ('static/**', 'ignore', None)]},
#    package_data = {'weckan': ['i18n/*/LC_MESSAGES/*.mo']},
    packages = find_packages(),
    paster_plugins = ['PasteScript'],
    setup_requires = ['PasteScript >= 1.6.3'],
    zip_safe = False,
    )
