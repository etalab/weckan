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

import logging
import json

from datetime import datetime

from sqlalchemy.sql import func, desc

from . import templates, urls, wsgihelpers
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


def last_datasets(num=8):
    '''Get the ``num`` latest created datasets'''
    datasets = []
    for package, timestamp in meta.Session.query(Package, func.max(Activity.timestamp).label('timestamp'))\
            .filter(Activity.object_id == Package.id)\
            .filter(Activity.activity_type == 'new package')\
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
            .filter(RelatedDataset.status == 'active').group_by(Package)\
            .order_by(desc(func.count(RelatedDataset.related_id))).limit(num):

        datasets.append({
            'name': package.name,
            'title': package.title,
            'timestamp': package.metadata_modified,
        })

    return datasets


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


def make_router(app):
    """Return a WSGI application that searches requests to controllers """
    global router
    router = urls.make_router(app,
        ('GET', r'^(/(?P<lang>\w{2}))?/?$', home),
        ('GET', r'^(/(?P<lang>\w{{2}}))?/dataset/(?!{0}(/|$))(?P<name>[\w_-]+)/?$'.format('|'.join(EXCLUDED_PATTERNS)), display_dataset),
        )

    return router
