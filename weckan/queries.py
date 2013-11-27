# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging

from sqlalchemy import orm
from sqlalchemy.sql import func, desc, null, and_, distinct

from ckanext.etalab.model import CertifiedPublicService

from weckan import model
from weckan.model import Package, Member, Group, User, Related, Role
from weckan.model import RelatedDataset, PackageRelationship, PackageRole

DB = model.meta.Session

log = logging.getLogger(__name__)

FORK_COMMENT = 'Fork'


def datasets(private=False):
    '''Query dataset with their organization'''
    query = DB.query(Package, Group)
    query = query.outerjoin(Group, Group.id == Package.owner_org)
    query = query.outerjoin(CertifiedPublicService)
    query = query.filter(Package.state == 'active')
    if private:
        query = query.filter(Package.private == True)
    else:
        query = query.filter(~Package.private)
    query = query.options(orm.joinedload(Group.certified_public_service))
    return query


def organizations_and_counters():
    '''Query organizations with their counters'''
    query = DB.query(Group,
        func.count(distinct(Package.id)).label('nb_datasets'),
        func.count(distinct(Member.id)).label('nb_members')
    )
    query = query.outerjoin(CertifiedPublicService)
    query = query.outerjoin(Package, and_(
        Group.id == Package.owner_org,
        ~Package.private,
        Package.state == 'active',
    ))
    query = query.outerjoin(Member, and_(
        Member.group_id == Group.id,
        Member.state == 'active',
        Member.table_name == 'user'
    ))
    query = query.filter(Group.state == 'active')
    query = query.filter(Group.approval_status == 'approved')
    query = query.filter(Group.is_organization == True)
    query = query.group_by(Group.id, CertifiedPublicService.organization_id)
    query = query.order_by(
        CertifiedPublicService.organization_id == null(),
        desc('nb_datasets'),
        desc('nb_members'),
        Group.title
    )
    query = query.options(orm.joinedload(Group.certified_public_service))
    return query


def last_datasets():
    '''Get the ``num`` latest created datasets'''
    query = datasets()
    query = query.outerjoin(model.PackageRevision, model.PackageRevision.id == Package.id)
    query = query.group_by(Package, Group)
    query = query.order_by(desc(func.min(model.PackageRevision.revision_timestamp)))
    return query


def popular_datasets():
    '''Get the ``num`` most popular (ie. with the most related) datasets'''
    query = datasets()
    query = query.outerjoin(RelatedDataset)
    query = query.group_by(Package, Group)
    query = query.order_by(desc(func.count(RelatedDataset.related_id)))
    return query


def featured_reuses():
    '''Get ``num``featured reuses'''
    query = DB.query(Related)
    query = query.filter(Related.featured > 0)
    query = query.order_by(desc(Related.created))
    return query


def owner(dataset):
    '''Get the user owning a dataset'''
    query = DB.query(User).join(PackageRole)
    query = query.filter(PackageRole.package_id == dataset.id)
    query = query.filter(PackageRole.role == Role.ADMIN)
    return query


def forked_from(dataset):
    '''Get the original dataset from which this dataset is forked'''
    query = PackageRelationship.by_subject(dataset)
    query = query.filter(PackageRelationship.type == 'derives_from')
    query = query.filter(PackageRelationship.comment == FORK_COMMENT)
    return query


def is_fork(dataset):
    '''Is this dataset a fork ?'''
    return forked_from(dataset).count() > 0


def forks(dataset):
    '''Get all the forks froma given dataset'''
    query = PackageRelationship.by_object(dataset)
    query = query.filter(PackageRelationship.type == 'derives_from')
    query = query.filter(PackageRelationship.comment == FORK_COMMENT)
    return query
