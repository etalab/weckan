# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging

from sqlalchemy.orm import joinedload
from sqlalchemy.sql import func, desc, null, and_

from ckanext.etalab.model import CertifiedPublicService

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
    query = DB.query(model.Group,
        func.count(model.Package.owner_org).label('nb_datasets'),
        func.count(model.Member.id).label('nb_members')
    )
    query = query.outerjoin(CertifiedPublicService)
    query = query.outerjoin(model.Package, and_(
        model.Group.id == model.Package.owner_org,
        ~model.Package.private,
        model.Package.state == 'active',
    ))
    query = query.outerjoin(model.Member, and_(
        model.Member.group_id == model.Group.id,
        model.Member.state == 'active',
        model.Member.table_name == 'user'
    ))
    query = query.filter(model.Group.state == 'active')
    query = query.filter(model.Group.approval_status == 'approved')
    query = query.filter(model.Group.is_organization == True)
    query = query.group_by(model.Group.id, CertifiedPublicService.organization_id)
    query = query.order_by(
        CertifiedPublicService.organization_id == null(),
        desc('nb_datasets'),
        desc('nb_members'),
        model.Group.title
    )
    return query


def last_datasets():
    '''Get the ``num`` latest created datasets'''
    query = datasets_and_organizations()
    query = query.outerjoin(model.PackageRevision, model.PackageRevision.id == model.Package.id)
    query = query.group_by(model.Package, model.Group)
    query = query.order_by(desc(func.min(model.PackageRevision.revision_timestamp)))
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
