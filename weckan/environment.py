# -*- coding: utf-8 -*-


# Weckan -- Web application using CKAN model
# By: Emmanuel Raviart <emmanuel@raviart.com>
#
# Copyright (C) 2013 Etalab
# http://github.com/etalab/weckan
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


"""Environment configuration"""


import collections
from ConfigParser import SafeConfigParser
import logging
import os
import sys
import urlparse

from biryani1 import strings
import pkg_resources
import sqlalchemy

import weckan
from . import conv, model, templates


app_dir = os.path.dirname(os.path.abspath(__file__))
project_entry_point_by_name = dict(
    (entry_point.name, entry_point)
    for entry_point in pkg_resources.iter_entry_points('weckan.projects')
    )


def load_environment(global_conf, app_conf):
    """Configure the application environment."""
    conf = weckan.conf  # Empty dictionary
    conf.update(strings.deep_decode(global_conf))
    conf.update(strings.deep_decode(app_conf))
    conf.update(conv.check(conv.struct(
        {
            'app_conf': conv.set_value(app_conf),
            'app_dir': conv.set_value(app_dir),
            'cache_dir': conv.default(os.path.join(os.path.dirname(app_dir), 'cache')),
            'cdn': conv.pipe(
                conv.make_input_to_url(),
                conv.default('//localhost:7000'),
                ),
            'cookie': conv.default('weckan'),
            'custom_templates_dir': conv.pipe(
                conv.empty_to_none,
                conv.test(os.path.exists),
                ),
            'customs_dir': conv.default(None),
            'debug': conv.pipe(conv.guess_bool, conv.default(False)),
            'global_conf': conv.set_value(global_conf),
            'host_urls': conv.pipe(
                conv.function(lambda host_urls: host_urls.split()),
                conv.uniform_sequence(
                    conv.make_input_to_url(error_if_fragment = True, error_if_path = True, error_if_query = True,
                        full = True, schemes = (u'ws', u'wss')),
                    constructor = lambda host_urls: sorted(set(host_urls)),
                    ),
                ),
            'log_level': conv.pipe(
                conv.default('WARNING'),
                conv.function(lambda log_level: getattr(logging, log_level.upper())),
                ),
            'package_name': conv.default('weckan'),
            'realm': conv.default(u'Weckan'),
            'sqlalchemy.url': conv.default('postgresql://ckan_default:password@localhost/ckan_default'),
            # Whether this application serves its own static files.
            'static_files': conv.pipe(conv.guess_bool, conv.default(True)),
            'static_files_dir': conv.default(os.path.join(app_dir, 'static')),
            'domain': conv.default('data.gouv.fr'),
            'home_url': conv.default('http://www.data.gouv.fr'),
            'wiki_url': conv.default('http://wiki.data.gouv.fr/wiki'),
            'wiki_api_url': conv.default('http://wiki.data.gouv.fr/api.php'),
            'questions_url': conv.default('http://questions.data.gouv.fr'),
            'ckan_url': conv.default('http://ckan.data.gouv.fr'),
            'cow_url': conv.default('http://cow.data.gouv.fr'),
            'sso_url': conv.default('http://id.data.gouv.fr'),
            'ws_url': conv.default('http://log.data.gouv.fr'),
            'territory_api_url': conv.default('http://ou.comarquage.fr/api/v1'),
            'bot_name': conv.default('bot-at-data-gouv-fr'),
            'https': conv.pipe(conv.guess_bool, conv.default(False)),
            'sentry.dsn': conv.default(False),
            },
        default = 'drop',
        ))(conf))

    # CDN configuration
    conf.update(conv.check(conv.struct(
        {
            'bootstrap': conv.pipe(
                conv.make_input_to_url(),
                conv.default(urlparse.urljoin(conf['cdn'], '/bootstrap/latest/')),
                conv.function(lambda url: url.rstrip(u'/') + u'/')
                ),
            'jquery.js': conv.pipe(
                conv.make_input_to_url(),
                conv.default(urlparse.urljoin(conf['cdn'], '/jquery/jquery.min.js')),
                ),
#            'select2': conv.pipe(
#                conv.make_input_to_url(),
#                conv.default(urlparse.urljoin(conf['cdn'], '/select2/latest/')),
#                conv.function(lambda url: url.rstrip(u'/') + u'/')
#                ),
            },
        default = conv.noop,
        ))(conf))

    # Configure logging.
    logging.basicConfig(level = conf['log_level'], stream = sys.stderr)

#    errorware = conf.setdefault('errorware', {})
#    errorware['debug'] = conf['debug']
#    if not errorware['debug']:
#        errorware['error_email'] = conf['email_to']
#        errorware['error_log'] = conf.get('error_log', None)
#        errorware['error_message'] = conf.get('error_message', 'An internal server error occurred')
#        errorware['error_subject_prefix'] = conf.get('error_subject_prefix', 'Weckan Error: ')
#        errorware['from_address'] = conf['from_address']
#        errorware['smtp_server'] = conf.get('smtp_server', 'localhost')

    # Intialize CKAN model
    # For PostgreSQL we want to enforce utf-8.
    sqlalchemy_url = conf.get('sqlalchemy.url', '')
    if sqlalchemy_url.startswith('postgresql://'):
        extras = {'client_encoding': 'utf8'}
    else:
        extras = {}
    sql_engine = sqlalchemy.engine_from_config(conf, 'sqlalchemy.', **extras)
    model.init_model(sql_engine)

    # Create the Mako TemplateLookup, with the default auto-escaping.
    templates.dirs = templates_dirs = []
    if conf['custom_templates_dir']:
        templates_dirs.append(conf['custom_templates_dir'])
    templates_dirs.append(os.path.join(app_dir, 'templates'))
