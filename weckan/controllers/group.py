# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging

from urllib import urlencode

from biryani1 import strings

from ckanext.youckan.models import MembershipRequest

from weckan import templates, urls, wsgihelpers, contexts, auth, forms
from weckan.model import meta, Group, Member, User
from weckan.tools import ckan_api
from weckan.controllers import dataset

_ = lambda s: s
DB = meta.Session
log = logging.getLogger(__name__)

SEARCH_PAGE_SIZE = 20

EXCLUDED_PATTERNS = (
    'activity',
    'delete',
    # 'edit',
    'follow',
    'new_metadata',
)


class GroupForm(forms.Form):
    title = forms.StringField(_('Title'), [forms.validators.required()])
    description = forms.MarkdownField(_('Description'), [forms.validators.required()])
    image_url = forms.URLField(_('Image URL'), [forms.validators.required()])


class GroupExtrasForm(forms.Form):
    key = forms.StringField(_('Key'), [forms.validators.required()])
    value = forms.StringField(_('Value'), [forms.validators.required()])
    old_key = forms.StringField(_('Old key'))


class GroupRoleForm(forms.Form):
    pk = forms.StringField(validators=[forms.validators.required()])
    value = forms.StringField(default='member')


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
    if not group:
        return wsgihelpers.not_found(context)
    form = GroupForm(request.POST, group, i18n=context.translator)

    if request.method == 'POST' and form.validate():
        name = strings.slugify(form.title.data)
        extras = [{'key': key, 'value': value} for key, value in group.extras.items()]
        ckan_api('organization_update' if is_org else 'group_update', user, {
            'id': group.id,
            'name': name,
            'title': form.title.data,
            'description': form.description.data,
            'image_url': form.image_url.data,
            'extras': extras,
        })

        redirect_url = urls.get_url(lang, 'organization' if is_org else 'group', name)
        return wsgihelpers.redirect(context, location=redirect_url)

    group_base_url = urls.get_url(lang, 'organization' if is_org else 'group')
    back_url = urls.get_url(lang, 'group', group.name)
    return templates.render_site('forms/group-edit-form.html', request,
        is_org=is_org, form=form, group_base_url=group_base_url, back_url=back_url, group=group)


def group_or_org_extras(request, is_org):
    context = contexts.Ctx(request)
    lang = request.urlvars.get('lang', templates.DEFAULT_LANG)
    user = auth.get_user_from_request(request)
    if not user:
        return wsgihelpers.unauthorized(context)  # redirect to login/register ?

    group_name = request.urlvars.get('name')
    group = Group.by_name(group_name)
    if not group:
        return wsgihelpers.not_found(context)

    if request.method == 'POST':
        headers = wsgihelpers.handle_cross_origin_resource_sharing(context)
        form = GroupExtrasForm(request.POST)
        if form.validate():
            extras = [
                {'key': key, 'value': value}
                for key, value in group.extras.items()
                if not key == (form.old_key.data or form.key.data)
            ]
            extras.append({'key': form.key.data, 'value': form.value.data})
            data = ckan_api('organization_update' if is_org else 'group_update', user, {
                'id': group.id,
                'name': group.name,
                'title': group.title,
                'description': group.description,
                'image_url': group.image_url,
                'extras': extras,
            })
            if data['success']:
                return wsgihelpers.respond_json(context, {'key': form.key.data, 'value': form.value.data}, headers=headers, code=200)
        return wsgihelpers.respond_json(context, {}, headers=headers, code=400)

    group_base_url = urls.get_url(lang, 'organization' if is_org else 'group')
    back_url = urls.get_url(lang, 'group', group.name)
    return templates.render_site('forms/group-extras-form.html', request,
        is_org=is_org, extras=group.extras.items(), group_base_url=group_base_url, back_url=back_url, group=group)


def group_or_org_delete_extra(request, is_org):
    context = contexts.Ctx(request)
    headers = wsgihelpers.handle_cross_origin_resource_sharing(context)

    user = auth.get_user_from_request(request)
    if not user:
        return wsgihelpers.unauthorized(context)  # redirect to login/register ?

    group_name = request.urlvars.get('name')
    group = Group.by_name(group_name)
    if not group:
        return wsgihelpers.not_found(context)

    extra_key = request.urlvars.get('key', '').strip()
    if not extra_key in group.extras.keys():
        return wsgihelpers.not_found(context)

    extras = [{'key': key, 'value': value} for key, value in group.extras.items() if not key == extra_key]
    extras.append({'key': extra_key, 'value': group.extras.get(extra_key), 'deleted': True})
    data = ckan_api('organization_update' if is_org else 'group_update', user, {
        'id': group.id,
        'name': group.name,
        'title': group.title,
        'description': group.description,
        'image_url': group.image_url,
        'extras': extras,
    })
    if data['success']:
        return wsgihelpers.respond_json(context, {}, headers=headers, code=200)
    return wsgihelpers.respond_json(context, {}, headers=headers, code=400)


def group_or_org_members(request, is_org):
    context = contexts.Ctx(request)
    lang = request.urlvars.get('lang', templates.DEFAULT_LANG)
    user = auth.get_user_from_request(request)
    if not user:
        return wsgihelpers.unauthorized(context)  # redirect to login/register ?

    group_name = request.urlvars.get('name')
    group = Group.by_name(group_name)
    if not group:
        return wsgihelpers.not_found(context)

    if request.method == 'POST':
        form = GroupRoleForm(request.POST)
        headers = wsgihelpers.handle_cross_origin_resource_sharing(context)
        if form.validate():
            data = ckan_api('member_create', user, {
                'id': group.id,
                'object': form.pk.data,
                'object_type': 'user',
                'capacity': form.value.data,
            })
            if data['success']:
                return wsgihelpers.respond_json(context, {}, headers=headers, code=200)
        return wsgihelpers.respond_json(context, {}, headers=headers, code=400)

    members = DB.query(Member, User).filter(
        Member.group == group,
        Member.state == 'active',
        Member.table_id == User.id,
        Member.table_name == 'user',
    )

    roles = {
        'admin': context._('Administrator'),
        'editor': context._('Editor'),
        'member': context._('Member'),
    }

    group_base_url = urls.get_url(lang, 'organization' if is_org else 'group')
    back_url = urls.get_url(group, group.name)
    return templates.render_site('forms/group-members-form.html', request,
        is_org=is_org, members=members, group_base_url=group_base_url, back_url=back_url, group=group, roles=roles)


def group_or_org_delete_member(request, is_org):
    context = contexts.Ctx(request)
    user = auth.get_user_from_request(request)
    if not user:
        return wsgihelpers.unauthorized(context)  # redirect to login/register ?

    group_name = request.urlvars.get('name')
    group = Group.by_name(group_name)
    if not group:
        return wsgihelpers.not_found(context)

    username = request.urlvars.get('username')
    headers = wsgihelpers.handle_cross_origin_resource_sharing(context)
    data = ckan_api('member_delete', user, {
        'id': group.id,
        'object': username,
        'object_type': 'user',
    })
    if data['success']:
        return wsgihelpers.respond_json(context, {}, headers=headers, code=200)
    return wsgihelpers.respond_json(context, {}, headers=headers, code=400)


def group_or_org_membership_requests(request, is_org):
    context = contexts.Ctx(request)
    lang = request.urlvars.get('lang', templates.DEFAULT_LANG)
    user = auth.get_user_from_request(request)
    if not user:
        return wsgihelpers.unauthorized(context)  # redirect to login/register ?

    group_name = request.urlvars.get('name')
    group = Group.by_name(group_name)
    if not group:
        return wsgihelpers.not_found(context)
    pending_requests = MembershipRequest.pending_for(group)

    group_base_url = urls.get_url(lang, 'organization' if is_org else 'group')
    back_url = urls.get_url(group, group.name)
    return templates.render_site('forms/group-membership-requests-form.html', request,
        is_org=is_org, pending_requests=pending_requests, group_base_url=group_base_url, back_url=back_url, group=group)


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
def delete_member(request):
    return group_or_org_delete_member(request, False)


@wsgihelpers.wsgify
def datasets(request):
    return edit_group_or_org(request, False)


@wsgihelpers.wsgify
def extras(request):
    return group_or_org_extras(request, False)


@wsgihelpers.wsgify
def delete_extra(request):
    return group_or_org_delete_extra(request, False)


@wsgihelpers.wsgify
def membership_requests(request):
    return group_or_org_membership_requests(request, False)


@wsgihelpers.wsgify
def display(request):
    context = contexts.Ctx(request)
    group_name = request.urlvars.get('name')
    group = Group.by_name(group_name)
    if not group:
        return wsgihelpers.not_found(context)
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
    (('GET', 'POST'), r'^(/(?P<lang>\w{2}))?/group/extras/(?P<name>[\w_-]+)/?$', extras),
    (('GET', 'POST'), r'^(/(?P<lang>\w{2}))?/group/members/(?P<name>[\w_-]+)/?$', members),
    ('DELETE', r'^(/(?P<lang>\w{2}))?/group/members/(?P<name>[\w_-]+)/(?P<username>[\w_-]+)/?$', delete_member),
    ('DELETE', r'^(/(?P<lang>\w{2}))?/group/extras/(?P<name>[\w_-]+)/(?P<key>.+)/?$', delete_extra),
    ('GET', r'^(/(?P<lang>\w{2}))?/group/requests/(?P<name>[\w_-]+)/?$', membership_requests),
    ('GET', r'^(/(?P<lang>\w{{2}}))?/groups?/(?!{0}(/|$))(?P<name>[\w_-]+)/?$'.format('|'.join(EXCLUDED_PATTERNS)), display),
)
