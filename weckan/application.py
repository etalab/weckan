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


"""Middleware initialization"""


import logging
import re
import urllib

from paste.cascade import Cascade
from paste.urlparser import StaticURLParser
import webob
from weberror.errormiddleware import ErrorMiddleware

from . import conf, contexts, controllers, environment, model, urls, wsgihelpers


lang_re = re.compile('^/(?P<lang>en|fr)(?=/|$)')
log = logging.getLogger(__name__)
percent_encoding_re = re.compile('%[\dA-Fa-f]{2}')


def environment_setter(app):
    """WSGI middleware that sets request-dependant environment."""
    def set_environment(environ, start_response):
        req = webob.Request(environ)
        ctx = contexts.Ctx(req)
        urls.application_url = req.application_url
        if conf['host_urls'] is not None:
            host_url = req.host_url + '/'
            if host_url not in conf['host_urls']:
                return wsgihelpers.bad_request(ctx, explanation = ctx._('Web site not found.'))(environ, start_response)
#        model.configure(ctx)
        return app(req.environ, start_response)

    return set_environment


#def language_detector(app):
#    """WSGI middleware that detect language symbol in requested URL or otherwise in Accept-Language header."""
#    def detect_language(environ, start_response):
#        req = webob.Request(environ)
#        ctx = contexts.Ctx(req)
#        match = lang_re.match(req.path_info)
#        if match is None:
#            ctx.lang = [
#                req.accept_language.best_match([('en-US', 1), ('en', 1), ('fr-FR', 1), ('fr', 1)],
#                    default_match = 'en').split('-', 1)[0],
#                ]
#        else:
#            ctx.lang = [match.group('lang')]
#            req.script_name += req.path_info[:match.end()]
#            req.path_info = req.path_info[match.end():]
#        return app(req.environ, start_response)

#    return detect_language


#def make_app(global_conf, **app_conf):
#    """Create a WSGI application and return it

#    ``global_conf``
#        The inherited configuration for this application. Normally from
#        the [DEFAULT] section of the Paste ini file.

#    ``app_conf``
#        The application's local configuration. Normally specified in
#        the [app:<name>] section of the Paste ini file (where <name>
#        defaults to main).
#    """
#    # Configure the environment and fill conf dictionary.
#    environment.load_environment(global_conf, app_conf)

#    # Dispatch request to controllers.
#    app = controllers.make_router()

#    # Init request-dependant environment
#    app = environment_setter(app)
##    app = language_detector(app)

#    # Repair badly encoded query in request URL.
#    app = request_query_encoding_fixer(app)

#    # CUSTOM MIDDLEWARE HERE (filtered by error handling middlewares)

#    # Handle Python exceptions
#    if not conf['debug']:
#        app = ErrorMiddleware(app, global_conf, **conf['errorware'])

#    if conf['static_files']:
#        # Serve static files
#        static_app = StaticURLParser(conf['static_files_dir'])
#        app = Cascade([static_app, app])

#    return app


def make_filter_app(app, global_conf, **app_conf):
    """Create a WSGI filter and return application

    ``global_conf``
        The inherited configuration for this application. Normally from
        the [DEFAULT] section of the Paste ini file.

    ``app_conf``
        The application's local configuration. Normally specified in
        the [app:<name>] section of the Paste ini file (where <name>
        defaults to main).
    """
    # Configure the environment and fill conf dictionary.
    environment.load_environment(global_conf, app_conf)

    # Dispatch request to controllers.
    app = controllers.make_router(app)

    # Init request-dependant environment
    app = environment_setter(app)
##    app = language_detector(app)

#    # Repair badly encoded query in request URL.
#    app = request_query_encoding_fixer(app)

#    # CUSTOM MIDDLEWARE HERE (filtered by error handling middlewares)

#    # Handle Python exceptions
#    if not conf['debug']:
#        app = ErrorMiddleware(app, global_conf, **conf['errorware'])

    if conf['static_files']:
        # Serve static files
        static_app = StaticURLParser(conf['static_files_dir'])
        app = Cascade([static_app, app])

    return app


def request_query_encoding_fixer(app):
    """WSGI middleware that repairs a badly encoded query in request URL."""
    def fix_request_query_encoding(environ, start_response):
        req = webob.Request(environ)
        query_string = req.query_string
        if query_string is not None:
            try:
                urllib.unquote(query_string).decode('utf-8')
            except UnicodeDecodeError:
                req.query_string = percent_encoding_re.sub(
                    lambda match: urllib.quote(urllib.unquote(match.group(0)).decode('iso-8859-1').encode('utf-8')),
                    query_string)
        return app(req.environ, start_response)

    return fix_request_query_encoding
