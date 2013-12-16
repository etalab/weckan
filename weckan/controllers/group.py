# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging

from urllib import urlencode

from biryani1 import strings

from weckan import templates, urls, wsgihelpers, contexts, auth
from weckan.model import meta, Group
from weckan.tools import ckan_api
from weckan.controllers import dataset
from weckan.forms import GroupForm, MembersForm


DB = meta.Session
log = logging.getLogger(__name__)

SEARCH_PAGE_SIZE = 20

EXCLUDED_PATTERNS = (
    'activity',
    'delete',
    'edit',
    'follow',
    'new_metadata',
    'new_resource',
)


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


def create_group_or_org(request, is_org):
    context = contexts.Ctx(request)
    lang = request.urlvars.get('lang', templates.DEFAULT_LANG)
    user = auth.get_user_from_request(request)
    if not user:
        return wsgihelpers.unauthorized(context)  # redirect to login/register ?

    form = GroupForm(request.POST, i18n=context.translator)

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
    return templates.render_site('forms/group-create-form.html', request,
        is_new=True, is_org=is_org, form=form, back_url=back_url)


def edit_group_or_org(request, is_org):
    context = contexts.Ctx(request)
    lang = request.urlvars.get('lang', templates.DEFAULT_LANG)
    user = auth.get_user_from_request(request)
    if not user:
        return wsgihelpers.unauthorized(context)  # redirect to login/register ?

    group_name = request.urlvars.get('name')
    group = Group.by_name(group_name)
    form = GroupForm(request.POST, group, i18n=context.translator)

    if request.method == 'POST' and form.validate():
        name = strings.slugify(form.title.data)
        ckan_api('organization_update' if is_org else 'group_update', user, {
            'id': group.id,
            'name': name,
            'title': form.title.data,
            'description': form.description.data,
            'image_url': form.image_url.data,
        })

        redirect_url = urls.get_url(lang, 'organization' if is_org else 'group', name)
        return wsgihelpers.redirect(context, location=redirect_url)

    group_base_url = urls.get_url(lang, 'organization' if is_org else 'group')
    back_url = urls.get_url(group, group.name)
    return templates.render_site('forms/group-edit-form.html', request,
        is_new=False, is_org=is_org, form=form, group_base_url=group_base_url, back_url=back_url, group=group)


def group_or_org_extras(request, is_org):
    context = contexts.Ctx(request)
    lang = request.urlvars.get('lang', templates.DEFAULT_LANG)
    user = auth.get_user_from_request(request)
    if not user:
        return wsgihelpers.unauthorized(context)  # redirect to login/register ?

    group_name = request.urlvars.get('name')
    group = Group.by_name(group_name)
    form = GroupForm(request.POST, group, i18n=context.translator)

    if request.method == 'POST' and form.validate():
        name = strings.slugify(form.title.data)
        ckan_api('organization_update' if is_org else 'group_update', user, {
            'id': group.id,
            'name': name,
            'title': form.title.data,
            'description': form.description.data,
            'image_url': form.image_url.data,
        })

        redirect_url = urls.get_url(lang, 'organization' if is_org else 'group', name)
        return wsgihelpers.redirect(context, location=redirect_url)

    group_base_url = urls.get_url(lang, 'organization' if is_org else 'group')
    back_url = urls.get_url(group, group.name)
    return templates.render_site('forms/group-extras-form.html', request,
        is_new=False, is_org=is_org, form=form, group_base_url=group_base_url, back_url=back_url, group=group)


def group_or_org_members(request, is_org):
    context = contexts.Ctx(request)
    lang = request.urlvars.get('lang', templates.DEFAULT_LANG)
    user = auth.get_user_from_request(request)
    if not user:
        return wsgihelpers.unauthorized(context)  # redirect to login/register ?

    group_name = request.urlvars.get('name')
    group = Group.by_name(group_name)
    form = GroupForm(request.POST, group, i18n=context.translator)

    if request.method == 'POST' and form.validate():
        name = strings.slugify(form.title.data)
        ckan_api('organization_update' if is_org else 'group_update', user, {
            'id': group.id,
            'name': name,
            'title': form.title.data,
            'description': form.description.data,
            'image_url': form.image_url.data,
        })

        redirect_url = urls.get_url(lang, 'organization' if is_org else 'group', name)
        return wsgihelpers.redirect(context, location=redirect_url)

    group_base_url = urls.get_url(lang, 'organization' if is_org else 'group')
    back_url = urls.get_url(group, group.name)
    return templates.render_site('forms/group-members-form.html', request,
        is_new=False, is_org=is_org, form=form, group_base_url=group_base_url, back_url=back_url, group=group)




@wsgihelpers.wsgify
def create(request):
    return create_group_or_org(request, False)


@wsgihelpers.wsgify
def edit(request):
    return edit_group_or_org(request, False)


@wsgihelpers.wsgify
def members(request):
    return group_or_org_members(request, False)


@wsgihelpers.wsgify
def datasets(request):
    return edit_group_or_org(request, False)


@wsgihelpers.wsgify
def membership_requests(request):
    return edit_group_or_org(request, False)


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


routes = (
    (('GET', 'POST'), r'^(/(?P<lang>\w{2}))?/group/new/?$', create),
    (('GET', 'POST'), r'^(/(?P<lang>\w{2}))?/group/edit/(?P<name>[\w_-]+)/?$', edit),
    (('GET', 'POST'), r'^(/(?P<lang>\w{2}))?/group/members/(?P<name>[\w_-]+)/?$', members),
    (('GET', 'POST'), r'^(/(?P<lang>\w{2}))?/group/requests/(?P<name>[\w_-]+)/?$', membership_requests),
    ('GET', r'^(/(?P<lang>\w{{2}}))?/groups?/(?!{0}(/|$))(?P<name>[\w_-]+)/?$'.format('|'.join(EXCLUDED_PATTERNS)), display),
)
