# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
import math

from urllib import urlencode

from sqlalchemy.sql import and_, or_

from weckan import templates, wsgihelpers, contexts, auth, queries, territories
from weckan.model import meta, Package, Group, Role, UserFollowingGroup
from weckan.controllers import dataset, group

from ckanext.youckan.models import MembershipRequest


DB = meta.Session
log = logging.getLogger(__name__)

SEARCH_MAX_ORGANIZATIONS = 2
SEARCH_PAGE_SIZE = 20

NB_DATASETS = 12

EXCLUDED_PATTERNS = (
    'activity',
    'delete',
    'follow',
    'new_metadata',
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


def search(query, page=1, page_size=SEARCH_MAX_ORGANIZATIONS):
    '''Perform an organization search given a ``query``'''
    likes = ['%{0}%'.format(word) for word in query.split() if word]

    organizations = queries.organizations_and_counters()
    if likes:
        organizations = organizations.filter(or_(
            and_(*(Group.name.ilike(like) for like in likes)),
            and_(*(Group.title.ilike(like) for like in likes)),
            # GroupRevision.description.ilike(like),
        ))

    total = organizations.count()
    start = (page - 1) * page_size
    end = start + page_size
    return 'organizations', {
        'results': organizations[start:end],
        'total': total,
        'page': page,
        'page_size': page_size,
        'total_pages': int(math.ceil(total / float(page_size))),
    }


@wsgihelpers.wsgify
def search_more(request):
    query = request.params.get('q', '')
    page = int(request.params.get('page', 1))
    _, results = search(query, page, SEARCH_PAGE_SIZE)
    return templates.render_site('search-organizations.html', request,
        search_query=query,
        url_pattern=get_page_url_pattern(request),
        organizations=results
    )


@wsgihelpers.wsgify
def display(request):
    user = auth.get_user_from_request(request)
    context = contexts.Ctx(request)
    _ = context.translator.ugettext

    organization_name = request.urlvars.get('name')

    query = queries.organizations_and_counters()
    query = query.filter(Group.name == organization_name)

    if not query.count():
        return wsgihelpers.not_found(context)

    organization, nb_datasets, nb_members = query.first()

    last_datasets = queries.last_datasets()
    last_datasets = last_datasets.filter(Package.owner_org == organization.id)
    last_datasets = last_datasets.limit(NB_DATASETS)

    fake, results = dataset.search(None, request, page_size=NB_DATASETS, organization=organization)

    dataset_tabs = (
        ('popular', _('Most popular'), results['results']),
        ('recents', _('Latest'), dataset.serialize(last_datasets)),
    )

    role = auth.get_role_for(user, organization)
    is_member = user and user.is_in_group(organization.id)
    is_admin = (is_member and role == Role.ADMIN) or (user and user.sysadmin)
    is_editor = is_admin or (is_member and role == Role.EDITOR)

    if is_admin:
        private_datasets = queries.datasets(private=True)
        private_datasets = private_datasets.filter(Package.owner_org == organization.id)
        private_datasets = private_datasets.limit(NB_DATASETS)
        dataset_tabs += (
            ('privates', _('Privates'), dataset.serialize(private_datasets)),
        )

    return templates.render_site('organization.html', context,
        organization=organization,
        nb_members=nb_members,
        nb_datasets=nb_datasets,
        nb_followers=UserFollowingGroup.follower_count(organization.id),
        is_following=UserFollowingGroup.is_following(user.id, organization.id) if organization and user else False,
        is_member=is_member,
        is_admin=is_admin,
        is_editor=is_editor,
        pending=(not is_member and MembershipRequest.is_pending(organization, user)),
        can_edit=auth.can_edit_org(user, organization),
        territory=territories.get_cookie(request),
        dataset_tabs=dataset_tabs,
        pending_requests=MembershipRequest.pending_for(organization) if is_admin else None,
    )


@wsgihelpers.wsgify
def popular_datasets(request):
    organization_name = request.urlvars.get('name')
    page = int(request.params.get('page', 1))
    context = contexts.Ctx(request)

    query = queries.organizations_and_counters()
    query = query.filter(Group.name == organization_name)

    if not query.count():
        return wsgihelpers.not_found(context)

    organization, nb_datasets, nb_members = query.first()

    fake, results = dataset.search(None, request, page=page, page_size=NB_DATASETS, organization=organization)
    return templates.render_site('search-datasets.html', request,
        title = organization.title,
        url_pattern=get_page_url_pattern(request),
        datasets=results,
        )


@wsgihelpers.wsgify
def recent_datasets(request):
    organization_name = request.urlvars.get('name')
    page = int(request.params.get('page', 1))
    context = contexts.Ctx(request)

    query = queries.organizations_and_counters()
    query = query.filter(Group.name == organization_name)

    if not query.count():
        return wsgihelpers.not_found(context)

    organization, nb_datasets, nb_members = query.first()

    last_datasets = queries.last_datasets()
    last_datasets = last_datasets.filter(Package.owner_org == organization.id)

    count = last_datasets.count()
    end = (page * NB_DATASETS) + 1
    start = end - NB_DATASETS

    return templates.render_site('search-datasets.html', request,
        title = organization.title,
        url_pattern=get_page_url_pattern(request),
        datasets={
            'total': count,
            'page': page,
            'page_size': NB_DATASETS,
            'total_pages': count / NB_DATASETS,
            'results': dataset.serialize(last_datasets[start:end])
            }
        )


@wsgihelpers.wsgify
def create(request):
    return group.create_group_or_org(request, True)


@wsgihelpers.wsgify
def edit(request):
    return group.edit_group_or_org(request, True)


@wsgihelpers.wsgify
def members(request):
    return group.group_or_org_members(request, True)


@wsgihelpers.wsgify
def extras(request):
    return group.group_or_org_extras(request, True)


@wsgihelpers.wsgify
def membership_requests(request):
    return group.group_or_org_membership_requests(request, True)


@wsgihelpers.wsgify
def autocomplete(request):
    query = request.params.get('q', '')
    num = int(request.params.get('num', SEARCH_MAX_ORGANIZATIONS))
    _, results = search(query, 1, num)

    context = contexts.Ctx(request)
    headers = wsgihelpers.handle_cross_origin_resource_sharing(context)

    data = [{
            'name': organization.name,
            'title': organization.display_name,
            'image_url': organization.image_url or templates.static('/img/placeholder_producer.png'),
        } for organization, _, _ in results['results']]

    return wsgihelpers.respond_json(context, data, headers=headers)


routes = (
    ('GET', r'^(/(?P<lang>\w{2}))?/organizations?/?$', search_more),
    ('GET', r'^(/(?P<lang>\w{2}))?/organizations?/autocomplete/?$', autocomplete),
    (('GET', 'POST'), r'^(/(?P<lang>\w{2}))?/organization/new/?$', create),
    (('GET', 'POST'), r'^(/(?P<lang>\w{2}))?/organization/edit/(?P<name>[\w_-]+)/?$', edit),
    (('GET', 'POST'), r'^(/(?P<lang>\w{2}))?/organization/extras/(?P<name>[\w_-]+)/?$', extras),
    (('GET', 'POST'), r'^(/(?P<lang>\w{2}))?/organization/members/(?P<name>[\w_-]+)/?$', members),
    ('GET', r'^(/(?P<lang>\w{2}))?/organization/requests/(?P<name>[\w_-]+)/?$', membership_requests),
    ('GET', r'^(/(?P<lang>\w{2}))?/organization/(?P<name>[\w_-]+)/popular?$', popular_datasets),
    ('GET', r'^(/(?P<lang>\w{2}))?/organization/(?P<name>[\w_-]+)/recents?$', recent_datasets),
    ('GET', r'^(/(?P<lang>\w{{2}}))?/organization/(?!{0}(/|$))(?P<name>[\w_-]+)/?$'.format('|'.join(EXCLUDED_PATTERNS)), display),
)
