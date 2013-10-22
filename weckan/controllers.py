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
import logging
import math
import requests

from datetime import datetime
from urllib import urlencode

from biryani1 import strings
from ckanext.etalab.model import CertifiedPublicService
from sqlalchemy.sql import func, desc, or_, null

from . import templates, urls, wsgihelpers, conf, contexts, auth
from .model import Activity, meta, Package, RelatedDataset, Group, GroupRevision, Member


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


def last_datasets(num=8):
    '''Get the ``num`` latest created datasets'''
    datasets = []
    for package, timestamp in meta.Session.query(Package, func.max(Activity.timestamp).label('timestamp'))\
            .filter(Activity.object_id == Package.id)\
            .filter(Activity.activity_type == 'new package')\
            .filter(~Package.private)\
            .filter(Package.state == 'active')\
            .group_by(Package).order_by(desc('timestamp')).limit(num):

        datasets.append({
            'name': package.name,
            'title': package.title,
            'timestamp': timestamp,
        })

    return datasets


def popular_datasets(num=8):
    '''Get the ``num`` most popular (ie. with the most related) datasets'''
    datasets = []
    for package in meta.Session.query(Package).join(RelatedDataset)\
            .filter(~Package.private)\
            .filter(Package.state == 'active')\
            .filter(RelatedDataset.status == 'active').group_by(Package)\
            .order_by(desc(func.count(RelatedDataset.related_id))).limit(num):

        datasets.append({
            'name': package.name,
            'title': package.title,
            'timestamp': package.metadata_modified,
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
        'sort': 'score desc, metadata_modified desc',
        'fq': '+dataset_type:dataset',
        'rows': page_size,
        'q': u'{0} +_val_:"{1}"^2'.format(
            query,
            dict(
                ArrondissementOfCommuneOfFrance = 'weight_commune',
                CommuneOfFrance = 'weight_commune',
                Country = 'weight',
                DepartmentOfFrance = 'weight_department',
                OverseasCollectivityOfFrance = 'weight_department',
                RegionOfFrance = 'weight_region',
            ).get(territory.get('kind'), 'weight'),
        ),
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

    datasets = []

    datasets_query = meta.Session.query(Package, Group)
    datasets_query = datasets_query.outerjoin(Group, Group.id == Package.owner_org)
    datasets_query = datasets_query.filter(Package.name.in_(query.results))
    datasets_query = datasets_query.filter(~Package.private)
    datasets_query = datasets_query.filter(Package.state == 'active')

    for dataset, organization in datasets_query.all():

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

        datasets.append({
            'name': dataset.name,
            'title': dataset.title,
            'display_name': dataset.display_name,
            'notes': dataset.notes,
            'organization': organization,
            'temporal_coverage': temporal_coverage,
            'territorial_coverage': {
                'name': dataset.extras.get('territorial_coverage', None),
                'granularity': dataset.extras.get('territorial_coverage_granularity', None),
            },
            'periodicity': dataset.extras.get('"dct:accrualPeriodicity"', None),
        })

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

    organizations = meta.Session.query(Group, func.count(Package.owner_org).label('nb_datasets'))
    organizations = organizations.join(GroupRevision)
    organizations = organizations.outerjoin(Package, Group.id == Package.owner_org)
    organizations = organizations.outerjoin(CertifiedPublicService)
    organizations = organizations.group_by(Group.id, CertifiedPublicService.organization_id)
    organizations = organizations.filter(GroupRevision.state == 'active')
    organizations = organizations.filter(GroupRevision.current == True)
    organizations = organizations.filter(or_(
        GroupRevision.name.ilike(like),
        GroupRevision.title.ilike(like),
        # GroupRevision.description.ilike(like),
    ))
    organizations = organizations.filter(GroupRevision.is_organization == True)
    organizations = organizations.filter(~Package.private)
    organizations = organizations.filter(Package.state == 'active')
    organizations = organizations.order_by(
        CertifiedPublicService.organization_id == null(),
        desc('nb_datasets'),
        Group.title
    )

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


def get_page_url_pattern(request):
    '''Get a formattable page url pattern from incoming request URL'''
    url_pattern_params = {}
    for key, value in request.params.iteritems():
        if key != 'page':
            url_pattern_params[key] = unicode(value).encode('utf-8')
    return '?'.join([request.path, urlencode(url_pattern_params)]) + '&page={page}'


def can_edit(user, dataset):
    if user is None:
        return False
    if user.sysadmin or dataset.owner_org is None:
        return True

    query = meta.Session.query(Member).filter(
        Member.capacity.in_(['admin', 'editor']),
        Member.group_id == dataset.owner_org,
        Member.state == 'active',
        Member.table_id == user.id,
        Member.table_name == 'user',
    )
    return query.count() > 0


@wsgihelpers.wsgify
def home(request):
    return templates.render_site('home.html', request,
        last_datasets = last_datasets(),
        popular_datasets = popular_datasets()
    )


@wsgihelpers.wsgify
def display_dataset(request):
    dataset_name = request.urlvars.get('name')

    dataset_and_organization = meta.Session.query(Package, Group)\
        .outerjoin(Group, Group.id == Package.owner_org)\
        .filter(Package.name == dataset_name)\
        .first()
    if dataset_and_organization is None:
        return wsgihelpers.not_found(contexts.Ctx(request))
    dataset, organization = dataset_and_organization

    territorial_coverage = {
        'name': dataset.extras.get('territorial_coverage', None),
        'granularity': dataset.extras.get('territorial_coverage_granularity', None),
    }

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

    periodicity = dataset.extras.get('"dct:accrualPeriodicity"', None)

    if request.cookies.get('territory-infos', '').count('|') == 1:
        territory_key, _ = request.cookies.get('territory-infos').split('|')
        territory = get_territory(*territory_key.split('/')) if territory_key else {}
    else:
        territory = {}

    supplier_id = dataset.extras.get('supplier_id', None)
    supplier = meta.Session.query(Group).filter(Group.id == supplier_id).first() if supplier_id else None

    return templates.render_site('dataset.html', request,
        dataset = dataset,
        organization = organization,
        supplier = supplier,
        territorial_coverage = territorial_coverage,
        temporal_coverage = temporal_coverage,
        periodicity = periodicity,
        groups = dataset.get_groups('group'),
        can_edit = can_edit(auth.get_user_from_request(request), dataset),
        territory = {
            'full_name': territory.get('full_name', ''),
            'full_name_slug': strings.slugify(territory.get('full_name', '')),
            'depcom': territory.get('code', '')
        }
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


def make_router(app):
    """Return a WSGI application that searches requests to controllers """
    global router
    router = urls.make_router(app,
        ('GET', r'^(/(?P<lang>\w{2}))?/?$', home),
        ('GET', r'^(/(?P<lang>\w{2}))?/search/?$', search_results),
        ('GET', r'^(/(?P<lang>\w{2}))?/dataset/?$', search_more_datasets),
        ('GET', r'^(/(?P<lang>\w{2}))?/dataset/autocomplete/?$', autocomplete_datasets),
        ('GET', r'^(/(?P<lang>\w{{2}}))?/dataset/(?!{0}(/|$))(?P<name>[\w_-]+)/?$'.format('|'.join(EXCLUDED_PATTERNS)), display_dataset),
        ('GET', r'^(/(?P<lang>\w{2}))?/organization/?$', search_more_organizations),
        )

    return router
