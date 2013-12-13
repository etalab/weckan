# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
import math
import requests

from datetime import datetime
from urllib import urlencode

from sqlalchemy.sql import func

from weckan import templates, urls, wsgihelpers, conf, contexts, auth, queries, territories
from weckan.model import Activity, meta, Package, Group, UserFollowingDataset, UserFollowingGroup


DB = meta.Session
log = logging.getLogger(__name__)

SEARCH_PAGE_SIZE = 20
SEARCH_TIMEOUT = 2

NB_DATASETS = 12

QA_CEILS = {
    'warning': 10,
    'error': 10,
    'criticals': 1,
}


def build_territorial_coverage(dataset):
    return {
        'name': ', '.join(
            name.strip().rsplit('/', 1)[-1].title()
            for name in dataset.extras.get('territorial_coverage', '').split(',')
        ),
        'granularity': dataset.extras.get('territorial_coverage_granularity', '').title() or None,
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


def serialize(query):
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
            'original': queries.forked_from(dataset).first(),
            'nb_reuses': len(dataset.related),
        })

    return datasets


def search(query, request, page=1, page_size=SEARCH_PAGE_SIZE, group=None, organization=None):
    '''Perform a Dataset search given a ``query``'''
    from ckan.lib import search

    if request.cookies.get('territory-infos', '').count('|') == 1:
        territory_key, _ = request.cookies.get('territory-infos').split('|')
        territory = territories.fetch(*territory_key.split('/')) if territory_key else {}
    else:
        territory = {}

    page_zero = page - 1
    params = {
        'bf': u'{}^2'.format(
            dict(
                ArrondissementOfCommuneOfFrance='weight_commune',
                CommuneOfFrance='weight_commune',
                Country='weight',
                DepartmentOfFrance='weight_department',
                OverseasCollectivityOfFrance='weight_department',
                RegionOfFrance='weight_region',
                ).get(territory.get('kind'), 'weight'),
            ),
        'defType': u'edismax',
        'fq': '+dataset_type:dataset',
        'q': query or '',
        'qf': u'name title groups^0.5 notes^0.5 tags^0.5 text^0.25',
        'rows': page_size,
        'sort': 'score desc, metadata_modified desc',
        'start': page_zero * page_size,
        }

    if group:
        group_name = group.name if isinstance(group, Group) else group
        params['fq'] = ' '.join([params['fq'], '+groups:{0}'.format(group_name)])

    if organization:
        org_name = organization.name if isinstance(organization, Group) else organization
        params['fq'] = ' '.join([params['fq'], '+organization:{0}'.format(org_name)])

    # Territory search if specified
    ancestors_kind_code = territory.get('ancestors_kind_code')
    if ancestors_kind_code:
        kind_codes = [
            '{}/{}'.format(ancestor_kind_code['kind'], ancestor_kind_code['code'])
            for ancestor_kind_code in ancestors_kind_code
            ]
        params['fq'] = '{} +covered_territories:({})'.format(params['fq'], ' OR '.join(kind_codes))

    query = search.query_for(Package)
    query.run(params)

    if not query.results:
        return 'datasets', {'results': [], 'total': 0}

    datasets_query = queries.datasets()
    datasets_query = datasets_query.filter(Package.name.in_(query.results))
    datasets = serialize(datasets_query.all())

    return 'datasets', {
        'results': sorted(datasets, key=lambda d: query.results.index(d['name'])),
        'total': query.count,
        'page': page,
        'page_size': page_size,
        'total_pages': int(math.ceil(query.count / float(page_size))),
    }


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


def get_quality(dataset_name):
    '''Fetch the dataset quality scores from COW'''
    url = '{0}/api/1/datasets/{1}/ranking'.format(conf['cow_url'], dataset_name)
    try:
        response = requests.get(url, timeout=SEARCH_TIMEOUT)
        response.raise_for_status()
    except requests.RequestException as request_exception:
        log.warning('Unable to fetch quality scores for %s: %s', dataset_name, request_exception)
        return None
    data = response.json().get('value', {})
    return data


@wsgihelpers.wsgify
def display(request):
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

    return templates.render_site('dataset.html', request,
        dataset=dataset,
        publication_date=timestamp,
        organization=organization,
        is_following_org=UserFollowingGroup.is_following(user.id, organization.id) if organization and user else False,
        supplier=supplier,
        owner=queries.owner(dataset).first(),
        nb_followers=UserFollowingDataset.follower_count(dataset.id),
        is_following=UserFollowingDataset.is_following(user.id, dataset.id) if user else False,
        territorial_coverage=build_territorial_coverage(dataset),
        temporal_coverage=build_temporal_coverage(dataset),
        periodicity=periodicity,
        groups=dataset.get_groups('group'),
        can_edit=auth.can_edit_dataset(user, dataset),
        is_fork=queries.is_fork(dataset),
        quality=get_quality(dataset.name),
        ceils=QA_CEILS,
        territory=territories.get_cookie(request),
        bot_name=conf['bot_name'],
    )


@wsgihelpers.wsgify
def search_more(request):
    query = request.params.get('q', '')
    page = int(request.params.get('page', 1))
    _, results = search(query, request, page, SEARCH_PAGE_SIZE)
    return templates.render_site('search-datasets.html', request,
        search_query=query,
        url_pattern=get_page_url_pattern(request),
        datasets=results
        )


@wsgihelpers.wsgify
def autocomplete(request):
    query = request.params.get('q', '')
    num = int(request.params.get('num', NB_DATASETS))
    _, results = search(query, request, 1, num)

    context = contexts.Ctx(request)
    headers = wsgihelpers.handle_cross_origin_resource_sharing(context)
    data = [{
            'name': dataset['name'],
            'title': dataset['display_name'],
            'image_url': (
                (dataset['organization'].image_url if dataset['organization'] else None)
                or templates.static('/img/placeholder_producer.png')
            ),
        } for dataset in results['results']]

    return wsgihelpers.respond_json(context, data, headers=headers)


@wsgihelpers.wsgify
def fork(request):
    context = contexts.Ctx(request)

    user = auth.get_user_from_request(request)
    if not user:
        return wsgihelpers.unauthorized(context)  # redirect to login/register ?

    dataset_name = request.urlvars.get('name')

    url = '{0}/youckan/dataset/{1}/fork'.format(conf['ckan_url'], dataset_name)
    headers = {
        'content-type': 'application/json',
        'Authorization': user.apikey,
    }

    try:
        response = requests.post(url, headers=headers)
        response.raise_for_status()
    except requests.RequestException:
        log.exception('Unable to fork dataset')
        raise
    forked = response.json()

    lang = request.urlvars.get('lang', templates.DEFAULT_LANG)
    fork_url = urls.get_url(lang, 'dataset', forked['name'])
    # fork_url = urls.get_url(rlang, 'dataset/edit', forked['name'])

    return wsgihelpers.redirect(context, location=fork_url)