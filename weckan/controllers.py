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

from sqlalchemy.sql import func, desc

from . import contexts, templates, urls, wsgihelpers, auth

from .model import Activity, meta, Package, RelatedDataset, Group


log = logging.getLogger(__name__)
router = None

GROUPS = (
    (u'Culture et communication', 'culture'),
    (u'Développement durable', 'wind'),
    (u'Éducation et recherche', 'education'),
    (u'État et collectivités', 'france'),
    (u'Europe', 'europe'),
    (u'Justice', 'justice'),
    (u'Monde', 'world'),
    (u'Santé et solidarité', 'hearth'),
    (u'Sécurité et défense', 'shield'),
    (u'Société', 'people'),
    (u'Travail, économie, emploi', 'case'),
)


def render_site_template(name, request, **kwargs):
    '''
    Render a template with a common site behavior.

    - handle language choice and fallback
    - inject user
    - inject sidebar items
    '''
    from .jinja import render_template, LANGUAGES, DEFAULT_LANG

    context = contexts.Ctx(request)
    lang = request.urlvars.get('lang', None)

    # Locale-less location
    base_location = request.uscript_name.replace('/{0}'.format(lang), '')

    # Override browser language
    if lang in LANGUAGES:
        context.lang = lang
    elif lang is None:
        lang = DEFAULT_LANG
    else:
        return wsgihelpers.redirect(context, location=base_location)

    return render_template(context, name,
        current_location = request.uscript_name,
        current_base_location = base_location,
        user = auth.get_user_from_request(request),
        lang = lang,
        sidebar_groups = GROUPS,
        **kwargs
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
    return render_site_template('home.html', request,
        last_datasets = last_datasets(),
        popular_datasets = popular_datasets()
    )


@wsgihelpers.wsgify
def display_dataset(request):
    dataset_name = request.urlvars.get('name')

    dataset, organization = meta.Session.query(Package, Group)\
        .filter(Package.name == dataset_name)\
        .filter(Group.id == Package.owner_org)\
        .filter(Group.is_organization == True)\
        .first()


    territorial_coverage = {
        'name': dataset.extras.get('territorial_coverage', None),
        'granularity': dataset.extras.get('territorial_coverage_granularity', None),
    }

    temporal_coverage = {
        'from': dataset.extras.get('temporal_coverage_from', None),
        'to': dataset.extras.get('temporal_coverage_to', None),
    }

    periodicity = dataset.extras.get('"dct:accrualPeriodicity"', None)

    return render_site_template('dataset.html', request,
        dataset = dataset,
        organization = organization,
        territorial_coverage = territorial_coverage,
        temporal_coverage = temporal_coverage,
        periodicity = periodicity,
        groups = dataset.get_groups('group')
    )


def make_router(app):
    """Return a WSGI application that searches requests to controllers """
    global router
    router = urls.make_router(app,
        # ('GET', r'^/?$', home),
        ('GET', r'^(/(?P<lang>\w{2}))?/?$', home),
        ('GET', r'^(/(?P<lang>\w{2}))?/dataset/(?P<name>[\w_-]+)/?$', display_dataset),

#        (None, '^/admin/accounts(?=/|$)', accounts.route_admin_class),
#        (None, '^/admin/forms(?=/|$)', forms.route_admin_class),
#        (None, '^/admin/projects(?=/|$)', projects.route_admin_class),
#        (None, '^/admin/sessions(?=/|$)', sessions.route_admin_class),
#        (None, '^/admin/subscriptions(?=/|$)', subscriptions.route_admin_class),
#        ('POST', '^/api/1/forms/fill_out?$', forms.api1_fill_out),
#        ('POST', '^/api/1/forms/start?$', forms.api1_start),
#        ('POST', '^/api/1/forms/stop?$', forms.api1_stop),
#        ('GET', '^/api/1/protos/autocomplete/?$', protos.api1_autocomplete),
#        ('GET', '^/api/1/protos/get/?$', protos.api1_get),
#        ('GET', '^/confirm/(?P<secret>[^/]+)/?$', forms.confirm),
#        (None, '^/forms(?=/|$)', projects.route_class),
#        ('GET', '^/google/authorize_done/?$', google.authorize_done),
#        ('GET', '^/login/?$', accounts.login),
#        ('GET', '^/login_done/?$', accounts.login_done),
#        ('GET', '^/logout/?$', accounts.logout),
        )
    return router
