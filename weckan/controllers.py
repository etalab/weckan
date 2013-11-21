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

"""Root controllers"""

from __future__ import unicode_literals

import futures
import json
import logging
import math
import requests

from datetime import datetime
from urllib import urlencode
from uuid import uuid1
from collections import OrderedDict

from biryani1 import strings
from sqlalchemy.sql import func, or_

from . import templates, urls, wsgihelpers, conf, contexts, auth, queries
from .model import Activity, meta, Package, Related, Group
from .model import Role, PackageRole, UserFollowingDataset, UserFollowingGroup, User


DB = meta.Session
log = logging.getLogger(__name__)
router = None

EXCLUDED_PATTERNS = (
    'activity',
    'delete',
    'edit',
    'follow',
    'new',
    'new_metadata',
    'new_resource',
)

SEARCH_MAX_ORGANIZATIONS = 2
SEARCH_MAX_TOPICS = 2
SEARCH_MAX_QUESTIONS = 2
SEARCH_PAGE_SIZE = 20

SEARCH_TIMEOUT = 2
POST_TIMEOUT = 3

NB_DATASETS = 12

QA_CEILS = {
    'warning': 10,
    'error': 10,
    'criticals': 1,
}


def build_territorial_coverage(dataset):
    return {
        'name': ', '.join(
            territory.strip().rsplit('/', 1)[-1]
            for territory in dataset.extras.get('territorial_coverage', '').split(',')
        ),
        'granularity': dataset.extras.get('territorial_coverage_granularity', None),
    }


def build_temporal_coverage(dataset):
    temporal_coverage = {
        'from': dataset.extras.get('temporal_coverage_from', None),
        'to': dataset.extras.get('temporal_coverage_to', None),
    }
    try:
        temporal_coverage['from'] = datetime.strptime(temporal_coverage['from'], '%Y-%m-%d')
    except:
        pass
    try:
        temporal_coverage['to'] = datetime.strptime(temporal_coverage['to'], '%Y-%m-%d')
    except:
        pass

    return temporal_coverage


def build_datasets(query):
    '''Build datasets for display from a queryset'''
    datasets = []

    for dataset, organization in query:
        datasets.append({
            'name': dataset.name,
            'title': dataset.title,
            'display_name': dataset.display_name,
            'notes': dataset.notes,
            'organization': organization,
            'temporal_coverage': build_temporal_coverage(dataset),
            'territorial_coverage': build_territorial_coverage(dataset),
            'periodicity': dataset.extras.get('"dct:accrualPeriodicity"', None),
        })

    return datasets


def search_datasets(query, request, page=1, page_size=SEARCH_PAGE_SIZE):
    '''Perform a Dataset search given a ``query``'''
    from ckan.lib import search

    if request.cookies.get('territory-infos', '').count('|') == 1:
        territory_key, _ = request.cookies.get('territory-infos').split('|')
        territory = get_territory(*territory_key.split('/')) if territory_key else {}
    else:
        territory = {}

    page_zero = page - 1
    params = {
        'defType': u'edismax',
        'fq': '+dataset_type:dataset',
        'q': query,
        'qf': u'name title groups^0.5 notes^0.5 tags^0.5 text^0.25 +_val_:"{}"^2'.format(
            dict(
                ArrondissementOfCommuneOfFrance = 'weight_commune',
                CommuneOfFrance = 'weight_commune',
                Country = 'weight',
                DepartmentOfFrance = 'weight_department',
                OverseasCollectivityOfFrance = 'weight_department',
                RegionOfFrance = 'weight_region',
                ).get(territory.get('kind'), 'weight'),
            ),
        'rows': page_size,
        'sort': 'score desc, metadata_modified desc',
        'start': page_zero * page_size,
        }

    # Territory search if specified
    ancestors_kind_code = territory.get('ancestors_kind_code')
    if ancestors_kind_code:
        territories = [
            '{}/{}'.format(ancestor_kind_code['kind'], ancestor_kind_code['code'])
            for ancestor_kind_code in ancestors_kind_code
            ]
        params['fq'] = '{} +covered_territories:({})'.format(params['fq'], ' OR '.join(territories))

    query = search.query_for(Package)
    query.run(params)

    if not query.results:
        return 'datasets', {'results': [], 'total': 0}

    datasets_query = queries.datasets_and_organizations()
    datasets_query = datasets_query.filter(Package.name.in_(query.results))
    datasets = build_datasets(datasets_query.all())

    return 'datasets', {
        'results': sorted(datasets, key=lambda d: query.results.index(d['name'])),
        'total': query.count,
        'page': page,
        'page_size': page_size,
        'total_pages': int(math.ceil(query.count / float(page_size))),
    }


def search_organizations(query, page=1, page_size=SEARCH_MAX_ORGANIZATIONS):
    '''Perform an organization search given a ``query``'''
    like = '%{0}%'.format(query)

    organizations = queries.organizations_and_counters()
    organizations = organizations.filter(or_(
        Group.name.ilike(like),
        Group.title.ilike(like),
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


def search_topics(query):
    '''Perform a topic search given a ``query``'''
    params = {
        'format': 'json',
        'action': 'query',
        'list': 'search',
        'srsearch': query,
        'srprop': 'timestamp',
        'srlimit': SEARCH_MAX_TOPICS,
    }
    try:
        response = requests.get(conf['wiki_api_url'], params=params, timeout=SEARCH_TIMEOUT)
        response.raise_for_status()
    except requests.RequestException:
        log.exception('Unable to fetch topics')
        return 'topics', {'results': [], 'more': False}
    json_response = response.json()
    return 'topics', {
        'results': json_response.get('query', {}).get('search', []),
        'more': 'query-continue' in json_response,
    }


def search_questions(query):
    '''Perform a question search given a ``query``'''
    url = '{0}/api/v1/questions'.format(conf['questions_url'])
    params = {
        'query': query,
        'sort': 'vote-desc',
    }
    try:
        response = requests.get(url, params=params, timeout=SEARCH_TIMEOUT)
        response.raise_for_status()
    except requests.RequestException:
        log.exception('Unable to fetch questions')
        return 'questions', {'results': [], 'total': 0}
    json_response = response.json()
    return 'questions', {
        'results': json_response.get('questions', [])[:SEARCH_MAX_QUESTIONS],
        'total': json_response.get('count', 0),
    }


def get_territory(kind, code):
    '''Perform a Territory API Call'''
    url = '{0}/territory'.format(conf['territory_api_url'])
    params = {
        'kind': kind,
        'code': code,
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
    except requests.RequestException:
        log.exception('Unable to fetch territory')
        return {}
    return response.json().get('data', {})


def get_territory_cookie(request):
    if request.cookies.get('territory-infos', '').count('|') == 1:
        territory_key, _ = request.cookies.get('territory-infos').split('|')
        territory = get_territory(*territory_key.split('/')) if territory_key else {}
    else:
        territory = {}

    return {
        'full_name': territory.get('full_name', ''),
        'full_name_slug': strings.slugify(territory.get('full_name', '')),
        'depcom': territory.get('code', '')
    }


def get_page_url_pattern(request):
    '''Get a formattable page url pattern from incoming request URL'''
    url_pattern_params = {}
    for key, value in request.params.iteritems():
        if key != 'page':
            url_pattern_params[key] = unicode(value).encode('utf-8')
    return '?'.join([request.path, urlencode(url_pattern_params)]) + '&page={page}'


def get_dataset_quality(dataset_name):
    '''Fetch the dataset quality scores from COW'''
    url = '{0}/api/1/datasets/{1}/ranking'.format(conf['cow_url'], dataset_name)
    try:
        response = requests.get(url, timeout=SEARCH_TIMEOUT)
        response.raise_for_status()
    except requests.RequestException:
        log.exception('Unable to fetch quality scores for %s', dataset_name)
        return None
    data = response.json().get('value', {})
    return data


def fork(dataset, user):
    '''
    Fork this package by duplicating it.

    The new owner will be the user parameter.
    The new package is created and the original will have a new related reference to the fork.
    '''
    if not user:
        raise ValueError('Fark requires an user')

    name_width = min(len(dataset.name), 88)
    name = '{name}-fork-{hash}'.format(
        name=dataset.name[:name_width],
        hash=str(uuid1())[:6],
    )

    orgs = user.get_groups('organization')
    resources = [{
            'url': r.url,
            'description': r.description,
            'format': r.format,
            'name': r.name,
            'resource_type': r.resource_type,
            'mimetype': r.mimetype,
        }
        for r in dataset.resources
    ]
    groups = [{'id': g.id} for g in dataset.get_groups()]
    tags = [{'name': t.name, 'vocabulary_id': t.vocabulary_id} for t in dataset.get_tags()]
    extras = [{'key': key, 'value': value} for key, value in dataset.extras.items()]

    url = '{0}/api/3/action/package_create'.format(conf['ckan_url'])
    headers = {
        'content-type': 'application/json',
        'Authorization': user.apikey,
    }
    data = {
        'name': name,
        'title': dataset.title,
        'maintainer': user.fullname,
        'maintainer_email': user.email,
        'license_id': dataset.license_id,
        'notes': dataset.notes,
        'url': dataset.url,
        'version': dataset.version,
        'type': dataset.type,
        'owner_org': orgs[0].id if len(orgs) else None,
        'resources': resources,
        'groups': groups,
        'tags': tags,
        'extras': extras,
    }

    try:
        response = requests.post(url, data=json.dumps(data), headers=headers, timeout=POST_TIMEOUT)
        response.raise_for_status()
    except requests.RequestException:
        log.exception('Unable to create dataset')
        raise
    json_response = response.json()

    if not json_response['success']:
        raise Exception('Unable to create package: {0}'.format(json_response['error']['message']))

    # Add the user as administrator
    forked = DB.query(Package).get(json_response['result']['id'])
    PackageRole.add_user_to_role(user, Role.ADMIN, forked)
    DB.commit()

    # Create the fork relationship
    url = url = '{0}/api/3/action/package_relationship_create'.format(conf['ckan_url'])
    data = {
        'type': 'has_derivation',
        'subject': dataset.id,
        'object': forked.id,
        'comment': 'Fork',
    }
    try:
        response = requests.post(url, data=json.dumps(data), headers=headers, timeout=POST_TIMEOUT)
        response.raise_for_status()
    except requests.RequestException:
        log.exception('Unable to create relationship')
        return forked

    json_response = response.json()
    if not json_response['success']:
        log.error('Unable to create relationship: {0}'.format(json_response['error']['message']))

    return forked


@wsgihelpers.wsgify
def home(request):
    context = contexts.Ctx(request)
    _ = context.translator.ugettext

    popular_datasets = queries.popular_datasets().limit(NB_DATASETS)
    last_datasets = queries.last_datasets().limit(NB_DATASETS)

    dataset_tabs = (
        ('popular', _('Most popular'), build_datasets(popular_datasets)),
        ('recents', _('Latest'), build_datasets(last_datasets)),
    )

    return templates.render_site('home.html', context,
        featured_reuses=queries.featured_reuses().limit(NB_DATASETS),
        territory=get_territory_cookie(request),
        dataset_tabs=dataset_tabs
    )


@wsgihelpers.wsgify
def display_organization(request):
    user = auth.get_user_from_request(request)
    context = contexts.Ctx(request)
    _ = context.translator.ugettext

    organization_name = request.urlvars.get('name')

    query = queries.organizations_and_counters()
    query = query.filter(Group.name == organization_name)

    if not query.count():
        return wsgihelpers.not_found(context)

    organization, nb_datasets, nb_members = query.first()

    is_member = user and user.is_in_group(organization.id)

    last_datasets = queries.last_datasets()
    last_datasets = last_datasets.filter(Package.owner_org == organization.id)
    last_datasets = last_datasets.limit(NB_DATASETS)

    popular_datasets = queries.popular_datasets()
    popular_datasets = popular_datasets.filter(Package.owner_org == organization.id)
    popular_datasets = popular_datasets.limit(NB_DATASETS)

    dataset_tabs = (
        ('popular', _('Most popular'), build_datasets(popular_datasets)),
        ('recents', _('Latest'), build_datasets(last_datasets)),
    )

    if user and (is_member or user.sysadmin):
        private_datasets = queries.datasets_and_organizations(private=True)
        private_datasets = private_datasets.filter(Package.owner_org == organization.id)
        private_datasets = private_datasets.limit(NB_DATASETS)
        dataset_tabs += (
            ('privates', _('Privates'), build_datasets(private_datasets)),
        )

    return templates.render_site('organization.html', context,
        organization=organization,
        nb_members=nb_members,
        nb_datasets=nb_datasets,
        nb_followers=UserFollowingGroup.follower_count(organization.id),
        is_following=UserFollowingGroup.is_following(user.id, organization.id) if organization and user else False,
        is_member=is_member,
        can_edit=auth.can_edit_org(user, organization),
        territory=get_territory_cookie(request),
        dataset_tabs=dataset_tabs,
    )


@wsgihelpers.wsgify
def display_dataset(request):
    user = auth.get_user_from_request(request)

    dataset_name = request.urlvars.get('name')

    query = DB.query(Package, Group, func.min(Activity.timestamp))
    query = query.outerjoin(Group, Group.id == Package.owner_org)
    query = query.outerjoin(Activity, Activity.object_id == Package.id)
    query = query.filter(Package.name == dataset_name)
    query = query.group_by(Package, Group)

    if not query.count():
        return wsgihelpers.not_found(contexts.Ctx(request))

    dataset, organization, timestamp = query.first()

    periodicity = dataset.extras.get('"dct:accrualPeriodicity"', None)

    supplier_id = dataset.extras.get('supplier_id', None)
    supplier = DB.query(Group).filter(Group.id == supplier_id).first() if supplier_id else None

    owner_query = DB.query(User).join(PackageRole)
    owner_query = owner_query.filter(PackageRole.package_id == dataset.id)
    owner_query = owner_query.filter(PackageRole.role == Role.ADMIN)

    return templates.render_site('dataset.html', request,
        dataset=dataset,
        publication_date=timestamp,
        organization=organization,
        is_following_org=UserFollowingGroup.is_following(user.id, organization.id) if organization and user else False,
        supplier=supplier,
        owner=owner_query.first(),
        nb_followers=UserFollowingDataset.follower_count(dataset.id),
        is_following=UserFollowingDataset.is_following(user.id, dataset.id) if user else False,
        territorial_coverage=build_territorial_coverage(dataset),
        temporal_coverage=build_temporal_coverage(dataset),
        periodicity=periodicity,
        groups=dataset.get_groups('group'),
        can_edit=auth.can_edit_dataset(user, dataset),
        quality=get_dataset_quality(dataset.name),
        ceils=QA_CEILS,
        territory=get_territory_cookie(request),
    )


@wsgihelpers.wsgify
def search_results(request):
    query = request.params.get('q', '')

    with futures.ThreadPoolExecutor(max_workers=4) as executor:
        workers = [
            executor.submit(search_datasets, query, request),
            executor.submit(search_organizations, query),
            executor.submit(search_topics, query),
            executor.submit(search_questions, query),
        ]

    results = dict(worker.result() for worker in futures.as_completed(workers))

    return templates.render_site('search.html', request, search_query=query, has_ckan=False, **results)


@wsgihelpers.wsgify
def search_more_datasets(request):
    query = request.params.get('q', '')
    page = int(request.params.get('page', 1))
    _, results = search_datasets(query, request, page, SEARCH_PAGE_SIZE)
    return templates.render_site('search-datasets.html', request,
        search_query=query,
        url_pattern=get_page_url_pattern(request),
        datasets=results
        )


@wsgihelpers.wsgify
def autocomplete_datasets(request):
    query = request.params.get('q', '')
    num = int(request.params.get('num', 8))
    _, results = search_datasets(query, request, 1, num)

    context = contexts.Ctx(request)
    headers = wsgihelpers.handle_cross_origin_resource_sharing(context)
    data = [{
            'name': dataset['name'],
            'title': dataset['display_name'],
            'image_url': dataset['organization'].image_url if dataset['organization'] else None,
        } for dataset in results['results']]

    return wsgihelpers.respond_json(context, data, headers=headers)


@wsgihelpers.wsgify
def search_more_organizations(request):
    query = request.params.get('q', '')
    page = int(request.params.get('page', 1))
    _, results = search_organizations(query, page, SEARCH_PAGE_SIZE)
    return templates.render_site('search-organizations.html', request,
        search_query=query,
        url_pattern=get_page_url_pattern(request),
        organizations=results
        )


@wsgihelpers.wsgify
def fork_dataset(request):
    user = auth.get_user_from_request(request)
    if not user:
        return wsgihelpers.unauthorized(contexts.Ctx(request))  # redirect to login/register ?

    dataset_name = request.urlvars.get('name')

    original = DB.query(Package).filter(Package.name == dataset_name).one()
    forked = fork(original, user)

    edit_url = urls.get_url(request.urlvars.get('lang', templates.DEFAULT_LANG), 'dataset/edit', forked.name)
    return wsgihelpers.redirect(contexts.Ctx(request), location=edit_url)


@wsgihelpers.wsgify
def toggle_featured(request, value=None, url=None):
    user = auth.get_user_from_request(request)
    context = contexts.Ctx(request)
    if not user or not user.sysadmin:
        return wsgihelpers.unauthorized(context)  # redirect to login/register ?

    reuse_id = request.urlvars.get('reuse')

    reuse = Related.get(reuse_id)
    reuse.featured = value if value is not None else (0 if reuse.featured else 1)
    DB.commit()

    if not url:
        dataset_name = request.urlvars.get('name')
        url = urls.get_url(request.urlvars.get('lang', templates.DEFAULT_LANG), 'dataset', dataset_name)
    return wsgihelpers.redirect(context, location=url)


@wsgihelpers.wsgify
def unfeature_reuse(request):
    return toggle_featured(request, 0, urls.get_url(request.urlvars.get('lang', templates.DEFAULT_LANG)))


def make_router(app):
    """Return a WSGI application that searches requests to controllers """
    global router
    router = urls.make_router(app,
        ('GET', r'^(/(?P<lang>\w{2}))?/?$', home),
        ('GET', r'^(/(?P<lang>\w{2}))?/search/?$', search_results),
        ('GET', r'^(/(?P<lang>\w{2}))?/dataset/?$', search_more_datasets),
        ('GET', r'^(/(?P<lang>\w{2}))?/dataset/autocomplete/?$', autocomplete_datasets),
        ('GET', r'^(/(?P<lang>\w{2}))?/dataset/(?P<name>[\w_-]+)/fork/?$', fork_dataset),
        ('GET', r'^(/(?P<lang>\w{2}))?/dataset/(?P<name>[\w_-]+)/reuse/(?P<reuse>[\w_-]+)/featured/?$', toggle_featured),
        ('GET', r'^(/(?P<lang>\w{{2}}))?/dataset/(?!{0}(/|$))(?P<name>[\w_-]+)/?$'.format('|'.join(EXCLUDED_PATTERNS)), display_dataset),
        ('GET', r'^(/(?P<lang>\w{2}))?/organization/?$', search_more_organizations),
        ('GET', r'^(/(?P<lang>\w{{2}}))?/organization/(?!{0}(/|$))(?P<name>[\w_-]+)/?$'.format('|'.join(EXCLUDED_PATTERNS)), display_organization),
        ('GET', r'^(/(?P<lang>\w{2}))?/unfeature/(?P<reuse>[\w_-]+)/?$', unfeature_reuse),
        )

    return router
