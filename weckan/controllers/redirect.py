# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging

from weckan import wsgihelpers, conf, contexts, auth

log = logging.getLogger(__name__)


@wsgihelpers.wsgify
def to_home(request):
    return wsgihelpers.redirect(contexts.Ctx(request), location='/')


@wsgihelpers.wsgify
def to_login(request):
    url = '{0}/login/'.format(conf['sso_url'])
    return wsgihelpers.redirect(contexts.Ctx(request), location=url)


@wsgihelpers.wsgify
def to_logout(request):
    url = '{0}/logout/'.format(conf['sso_url'])
    return wsgihelpers.redirect(contexts.Ctx(request), location=url)


@wsgihelpers.wsgify
def to_profile(request):
    username = request.urlvars.get('username')
    profile_url = '{0}/u/{1}/'.format(conf['sso_url'], username)
    return wsgihelpers.redirect(contexts.Ctx(request), location=profile_url)


@wsgihelpers.wsgify
def to_account(request):
    context = contexts.Ctx(request)
    user = auth.get_user_from_request(request)
    username = request.urlvars.get('username')

    if not user or not username == user.name:
        return wsgihelpers.unauthorized(context)

    account_url = '{0}/my/profile/'.format(conf['sso_url'])
    return wsgihelpers.redirect(context, location=account_url)

routes = (
    # Override some CKAN URLs
    ('GET', r'^(/(?P<lang>\w{2}))?/user/_?logout/?$', to_logout),
    ('GET', r'^(/(?P<lang>\w{2}))?/user/register/?$', to_login),
    ('GET', r'^(/(?P<lang>\w{2}))?/user/login/?$', to_login),
    ('GET', r'^(/(?P<lang>\w{2}))?/register/?$', to_login),
    ('GET', r'^(/(?P<lang>\w{2}))?/login/?$', to_login),
    ('GET', r'^(/(?P<lang>\w{2}))?/user/(?P<username>[\w_-]+)/?$', to_profile),
    ('GET', r'^(/(?P<lang>\w{2}))?/user/edit/(?P<username>[\w_-]+)/?$', to_account),
    ('GET', r'^(/(?P<lang>\w{2}))?/about/?$', to_home),
)
