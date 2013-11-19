# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging


from sqlalchemy.orm import joinedload
from sqlalchemy.sql import func, desc, null

from ckanext.etalab.model import CertifiedPublicService

from sqlalchemy.sql import func, desc, or_, null
from sqlalchemy.orm import joinedload

from weckan import model

DB = model.meta.Session

log = logging.getLogger(__name__)


def datasets_and_organizations():
    '''Query dataset with their organization'''
    query = DB.query(model.Package, model.Group)
    query = query.outerjoin(model.Group, model.Group.id == model.Package.owner_org)
    query = query.outerjoin(CertifiedPublicService)
    query = query.filter(~model.Package.private)
    query = query.filter(model.Package.state == 'active')
    query = query.options(joinedload(model.Group.certified_public_service))
    return query


def organizations_and_counters():
    '''Query organizations with their counters'''
    query = DB.query(model.Group, func.count(model.Package.owner_org).label('nb_datasets'))
    query = query.join(model.GroupRevision)
    query = query.outerjoin(model.Package, model.Group.id == model.Package.owner_org)
    query = query.outerjoin(CertifiedPublicService)
    query = query.group_by(model.Group.id, CertifiedPublicService.organization_id)
    query = query.filter(model.GroupRevision.state == 'active')
    query = query.filter(model.GroupRevision.current == True)
    query = query.filter(model.GroupRevision.is_organization == True)
    query = query.filter(~model.Package.private)
    query = query.filter(model.Package.state == 'active')
    query = query.order_by(
        CertifiedPublicService.organization_id == null(),
        desc('nb_datasets'),
        model.Group.title
    )
    query = query.options(joinedload('certified_public_service'))
    return query


def last_datasets():
    '''Get the ``num`` latest created datasets'''
    query = datasets_and_organizations()
    query = query.outerjoin(model.Activity, model.Activity.object_id == model.Package.id)
    query = query.filter(model.Activity.activity_type == 'new package')
    query = query.group_by(model.Package, model.Group)
    query = query.order_by(desc(func.max(model.Activity.timestamp)))
    return query


def popular_datasets():
    '''Get the ``num`` most popular (ie. with the most related) datasets'''
    query = datasets_and_organizations()
    query = query.outerjoin(model.RelatedDataset)
    query = query.group_by(model.Package, model.Group)
    query = query.order_by(desc(func.count(model.RelatedDataset.related_id)))
    return query


def featured_reuses():
    '''Get ``num``featured reuses'''
    query = DB.query(model.Related, model.User)
    query = query.join(model.User, model.Related.owner_id == model.User.id)
    query = query.filter(model.Related.featured > 0)
    query = query.order_by(desc(model.Related.created))
    return query
