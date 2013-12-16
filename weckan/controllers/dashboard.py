# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging

from sqlalchemy.sql import distinct

from weckan import templates, wsgihelpers, conf, contexts
from weckan.model import meta, Package, Related, Group, Resource
from weckan.model import User

from ckanext.etalab.model import CertifiedPublicService


DB = meta.Session
log = logging.getLogger(__name__)


@wsgihelpers.wsgify
def metrics(request):
    context = contexts.Ctx(request)
    _ = context._

    datasets = DB.query(Package).filter(Package.state == 'active', ~Package.private).count()

    reuses = DB.query(Related).count()

    resources = DB.query(Resource).filter(Resource.state == 'active').count()

    file_formats = DB.query(distinct(Resource.format)).count()

    organizations = DB.query(Group).filter(Group.is_organization == True, Group.state == 'active').count()

    certified_organizations = DB.query(CertifiedPublicService).join(Group).filter(Group.state == 'active').count()

    users = DB.query(User).count()

    return templates.render_site('metrics.html', request, ws_url=conf['ws_url'], metrics=(
        ('datasets_count', _('Datasets'), datasets),
        ('related_count', _('Reuses'), reuses),
        ('resources_count', _('Resources'), resources),
        ('organizations_count', _('Organizations'), organizations),
        ('certifieds', _('Certified organizations'), certified_organizations),
        ('users', _('Users'), users),
        ('datasets_total_weight', _('Total quality'), '...'),
        ('datasets_average_weight', _('Average quality'), '...'),
        ('datasets_median_weight', _('Median quality'), '...'),
        ('formats_count', _('File formats'), file_formats),
    ))


routes = (
    ('GET', r'^(/(?P<lang>\w{2}))?/metrics/?$', metrics),
)
