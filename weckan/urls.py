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


"""Helpers for URLs"""


import re
import urllib
import urlparse

from biryani1 import strings
import webob

from . import conf, contexts, wsgihelpers


SSO_URLS = {
    'user': '/u/{0}/',
    'users': '/users/',
    'settings': '/my/profile/',
    'login': '/login',
    'logout': '/logout',
}


application_url = None  # Set to req.application_url as soon as Weckan application is called.


def get_base_url(ctx, full = False):
    assert not(application_url is None and full), "Can't use full URLs when application_url is not inited."
    base_url = (application_url or u'').rstrip('/')
    if not full:
        # When a full URL is not requested, remove scheme and network location from it.
        base_url = urlparse.urlsplit(base_url).path
    return base_url


def get_full_url(ctx, *path, **query):
    path = [
        urllib.quote(unicode(sub_fragment).encode('utf-8'), safe = ',/:').decode('utf-8')
        for fragment in path
        if fragment
        for sub_fragment in unicode(fragment).split(u'/')
        if sub_fragment
        ]
    query = dict(
        (str(name), strings.deep_encode(value))
        for name, value in sorted(query.iteritems())
        if value not in (None, [], (), '')
        )
    return u'{0}/{1}{2}'.format(get_base_url(ctx, full = True), u'/'.join(path),
        ('?' + urllib.urlencode(query, doseq = True)) if query else '')


def get_url(ctx, *path, **query):
    path = [
        urllib.quote(unicode(sub_fragment).encode('utf-8'), safe = ',/:').decode('utf-8')
        for fragment in path
        if fragment
        for sub_fragment in unicode(fragment).split(u'/')
        if sub_fragment
        ]
    query = dict(
        (str(name), strings.deep_encode(value))
        for name, value in sorted(query.iteritems())
        if value not in (None, [], (), '')
        )
    return u'{0}/{1}{2}'.format(get_base_url(ctx), u'/'.join(path),
        ('?' + urllib.urlencode(query, doseq = True)) if query else '')


def sso_url(url_name, *args):
    if not url_name in SSO_URLS:
        raise ValueError('Unknown URL name')
    return conf['sso_url'] + SSO_URLS[url_name].format(*args)


def iter_full_urls(ctx, *path, **query):
    assert application_url is not None
    host_urls = conf['host_urls']
    if host_urls is None:
        yield get_full_url(ctx, *path, **query)
    else:
        path = [
            urllib.quote(unicode(sub_fragment).encode('utf-8'), safe = ',/:').decode('utf-8')
            for fragment in urlparse.urlsplit(application_url).path.split('/') + path
            if fragment
            for sub_fragment in unicode(fragment).split(u'/')
            if sub_fragment
            ]
        query = dict(
            (str(name), strings.deep_encode(value))
            for name, value in sorted(query.iteritems())
            if value not in (None, [], (), '')
            )
        for host_url in host_urls:
            yield u'{0}{1}{2}'.format(host_url, u'/'.join(path),
                ('?' + urllib.urlencode(query, doseq = True)) if query else '')


# To use in Python 3:
# def make_router(*routings, error_format = None):
def make_router(default_app, *routings, **kwargs):
    """Return a WSGI application that dispatches requests to controllers """
    error_format = kwargs.get('error_format')
    routes = []
    for routing in routings:
        methods, regex, app = routing[:3]
        if isinstance(methods, basestring):
            methods = (methods,)
        vars = routing[3] if len(routing) >= 4 else {}
        routes.append((methods, re.compile(unicode(regex)), app, vars))

    def router(environ, start_response):
        """Dispatch request to controllers."""
        req = webob.Request(environ)
        split_path_info = req.path_info.split('/')
        if split_path_info[0]:
            # When path_info doesn't start with a "/" this is an error or a attack => Reject request.
            # An example of an URL with such a invalid path_info: http://127.0.0.1http%3A//127.0.0.1%3A80/result?...
            ctx = contexts.Ctx(req)
            return wsgihelpers.bad_request(ctx, explanation = ctx._(u"Invalid path: {0}").format(
                req.path_info))(environ, start_response)
        for methods, regex, app, vars in routes:
            if methods is None or req.method in methods:
                match = regex.match(req.path_info)
                if match is not None:
                    if getattr(req, 'urlvars', None) is None:
                        req.urlvars = {}
                    req.urlvars.update(match.groupdict())
                    req.urlvars.update(vars)
                    req.script_name += req.path_info[:match.end()]
                    req.path_info = req.path_info[match.end():]
                    return app(req.environ, start_response)
        ctx = contexts.Ctx(req)
        if error_format == 'json':
            headers = wsgihelpers.handle_cross_origin_resource_sharing(ctx)
            return wsgihelpers.respond_json(ctx,
                dict(
                    apiVersion = '1.0',
                    error = dict(
                        code = 404,  # Not Found
                        message = ctx._(u"Path not found: {0}").format(
                            req.path_info),
                        ),
                    ),
                headers = headers,
                )(environ, start_response)
        return default_app(environ, start_response)

    return router
