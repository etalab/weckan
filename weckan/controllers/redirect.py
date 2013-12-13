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
