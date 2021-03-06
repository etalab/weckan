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


"""The application's model objects"""

from sqlalchemy.sql import and_

from . import urls

from ckan.model import *


db = None

DB = meta.Session


CkanPackage = Package


class Package(CkanPackage):
    def get_url(self, ctx, *path, **query):
        return urls.get_url(ctx, 'dataset', self.name, *path, **query)

    @property
    def display_name(self):
        return self.title or self.name

    @property
    def active_resources(self):
        if len(self.resource_groups_all) == 0:
            return []

        assert len(self.resource_groups_all) == 1, "can only use resources on packages if there is only one resource_group"
        resource_group_id = self.resource_groups_all[0].id

        resources = meta.Session.query(ResourceRevision)
        resources = resources.filter_by(resource_group_id=resource_group_id)
        resources = resources.filter_by(state='active').filter_by(current=True)
        resources = resources.order_by(ResourceRevision.position)
        return resources.all()

meta.mapper(Package, inherits = CkanPackage)


CkanTag = Tag


class Tag(CkanTag):
    @classmethod
    def slug_to_name(cls, value, state = None):
        if value is None:
            return None, None
        if state is None:
            state = conv.default_state
        return conv.test(
            lambda tag_name: meta.Session.query(cls).filter_by(name = tag_name).first() is not None,
            error = state._("Keyword doesn't exist"),
            )(value, state = state)

meta.mapper(Tag, inherits = CkanTag)


CkanUser = User


class User(CkanUser):
    @property
    def organizations(self):
        query = DB.query(Group)
        query = query.filter(Group.state == 'active')
        query = query.filter(Group.approval_status == 'approved')
        query = query.filter(Group.is_organization == True)
        query = query.order_by(Group.title)
        query = query.join(Member, and_(
            Member.group_id == Group.id,
            Member.table_name == 'user',
            Member.state == 'active',
            Member.table_id == self.id,
        ))
        return query.all()

meta.mapper(User, inherits=CkanUser)
