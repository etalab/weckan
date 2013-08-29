# -*- coding: utf-8 -*-


# Weckan -- Web application using CKAN model
# By: Emmanuel Raviart <emmanuel@raviart.com>
#
# Copyright (C) 2013 Emmanuel Raviart
# http://gitorious.org/etalab/weckan
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

from . import contexts, templates, urls, wsgihelpers

from .model import Activity, meta, Package, RelatedDataset
from sqlalchemy.sql import func, desc


log = logging.getLogger(__name__)
router = None

groups = (
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
def index(req):
    ctx = contexts.Ctx(req)
    return templates.render(ctx, '/index-demo.mako')


@wsgihelpers.wsgify
def home(req):
    from .jinja import env
    template = env.get_template('home.html')
    return template.render(
        lang='fr',
        groups=groups,
        last_datasets=last_datasets(),
        popular_datasets=popular_datasets()
    )


def make_router(app):
    """Return a WSGI application that searches requests to controllers """
    global router
    router = urls.make_router(app,
        ('GET', '^/?$', index),
        ('GET', '^/fr/?$', index),
        ('GET', '^/bootstrap/?$', home),

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
