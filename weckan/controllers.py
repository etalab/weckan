# -*- coding: utf-8 -*-


# Weckan -- Web application using CKAN model
# By: Emmanuel Raviart <emmanuel@raviart.com>
#
# Copyright (C) 2013 Emmanuel Raviart
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
import requests

from datetime import datetime

from sqlalchemy.sql import func, desc

from . import templates, urls, wsgihelpers, conf
from .model import Activity, meta, Package, RelatedDataset, Group


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
SEARCH_MAX_DATASETS = 20


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


def search_datasets(query):
    '''Perform a Dataset search given a ``query``'''
    from ckan.lib import search
    dataset_params = {
        'sort': 'score desc, metadata_modified desc',
        'fq': '+dataset_type:dataset',
        'rows': SEARCH_MAX_DATASETS,
        'facet.field': ['organization', 'groups', 'tags', 'res_format', 'license_id'],
        'q': query,
        'start': 0,
        'extras': {}
    }
    dataset_query = search.query_for(Package)
    dataset_query.run(dataset_params)

    datasets = []

    for dataset, organization in meta.Session.query(Package, Group)\
            .outerjoin(Group, Group.id == Package.owner_org)\
            .filter(Package.name.in_(dataset_query.results))\
            .filter(~Package.private)\
            .filter(Package.state == 'active')\
            .all():
        datasets.append({
                'name': dataset.name,
                'title': dataset.title,
                'display_name': dataset.display_name,
                'notes': dataset.notes,
                'organization': organization
            })

    return 'datasets', datasets


def search_organizations(query):
    '''Perform an organization search given a ``query``'''
    organizations = meta.Session.query(Group).filter(Group.type == 'organization')\
        .filter(Group.name.like('%{0}%'.format(query)))\
        .limit(SEARCH_MAX_ORGANIZATIONS).all()
    return 'organizations', organizations


def search_topics(query):
    '''Perform a topic search given a ``query``'''
    url = '{0}/api.php'.format(conf['wiki_url'])
    params = {
        'format': 'json',
        'action': 'query',
        'list': 'search',
        'srsearch': query,
        'srprop': 'timestamp',
        'limit': SEARCH_MAX_TOPICS,
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
    except requests.exceptions.RequestException:
        log.exception('Unable to fetch topics')
        return 'topics', []
    return 'topics', response.json().get('query', {}).get('search', [])


def search_questions(query):
    '''Perform a question search given a ``query``'''
    url = '{0}/api/v1/questions'.format(conf['questions_url'])
    params = {
        'query': query,
        'sort': 'vote-desc',
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
    except requests.exceptions.RequestException:
        log.exception('Unable to fetch questions')
        return 'questions', []
    return 'questions', response.json().get('questions', [])[:SEARCH_MAX_QUESTIONS]


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
        return wsgihelpers.not_found(ctx)
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

    try:
        territory = json.loads(request.cookies.get('territory', '{}'))
    except ValueError:  # No JSON object could be decoded
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
        territory = {
            'full_name': territory.get('full_name', ''),
            'full_name_slug': territory.get('full_name_slug', ''),
            'depcom': territory.get('code', '')
        }
    )


@wsgihelpers.wsgify
def search_results(request):
    query = request.params.get('q', '')

    with futures.ThreadPoolExecutor(max_workers=4) as executor:
        workers = [
            executor.submit(search_datasets, query),
            executor.submit(search_organizations, query),
            executor.submit(search_topics, query),
            executor.submit(search_questions, query),
        ]

    results = dict(worker.result() for worker in futures.as_completed(workers))

    return templates.render_site('search.html', request, search_query=query, **results)


def make_router(app):
    """Return a WSGI application that searches requests to controllers """
    global router
    router = urls.make_router(app,
        ('GET', r'^(/(?P<lang>\w{2}))?/?$', home),
        ('GET', r'^(/(?P<lang>\w{2}))?/dataset/?$', search_results),
        ('GET', r'^(/(?P<lang>\w{{2}}))?/dataset/(?!{0}(/|$))(?P<name>[\w_-]+)/?$'.format('|'.join(EXCLUDED_PATTERNS)), display_dataset),
        )

    return router
