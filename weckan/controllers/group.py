# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging

from urllib import urlencode

from biryani1 import strings

from weckan import templates, urls, wsgihelpers, contexts, auth
from weckan.model import meta, Group
from weckan.tools import ckan_api
from weckan.controllers import dataset
from weckan.forms import GroupCreateForm


DB = meta.Session
log = logging.getLogger(__name__)

SEARCH_PAGE_SIZE = 20


def get_page_url_pattern(request):
    '''Get a formattable page url pattern from incoming request URL'''
    url_pattern_params = {}
    for key, value in request.params.iteritems():
        if key != 'page':
            url_pattern_params[key] = unicode(value).encode('utf-8')
    if url_pattern_params:
        return '?'.join([request.path, urlencode(url_pattern_params)]) + '&page={page}'
    else:
        return '?'.join([request.path, 'page={page}'])


@wsgihelpers.wsgify
def create_group_or_org(request, is_org):
    context = contexts.Ctx(request)
    lang = request.urlvars.get('lang', templates.DEFAULT_LANG)
    user = auth.get_user_from_request(request)
    if not user:
        return wsgihelpers.unauthorized(context)  # redirect to login/register ?

    form = GroupCreateForm(request.POST, i18n=context.translator)

    if request.method == 'POST' and form.validate():
        name = strings.slugify(form.title.data)
        ckan_api('organization_create' if is_org else 'group_create', user, {
            'name': name,
            'title': form.title.data,
            'description': form.description.data,
            'image_url': form.image_url.data,
        })

        redirect_url = urls.get_url(lang, 'organization' if is_org else 'group', name)
        return wsgihelpers.redirect(context, location=redirect_url)

    back_url = urls.get_url(lang, 'organizations' if is_org else 'groups')
    return templates.render_site('forms/group-create-form.html', request, new=True, is_org=is_org, form=form, back_url=back_url)


@wsgihelpers.wsgify
def create(request):
    return create_group_or_org(request, False)


@wsgihelpers.wsgify
def display(request):
    group_name = request.urlvars.get('name')
    group = Group.by_name(group_name)
    page = int(request.params.get('page', 1))
    _, results = dataset.search('', request, page, SEARCH_PAGE_SIZE, group)
    main_groups = [t['name'] for t in templates.main_topics()]
    return templates.render_site('group.html', request,
        group=group,
        url_pattern=get_page_url_pattern(request),
        datasets=results,
        group_class='topic-{0}'.format(main_groups.index(group_name) + 1) if group_name in main_groups else None,
    )
