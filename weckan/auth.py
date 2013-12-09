# -*- coding: utf-8 -*-

# Weckan -- Web application using CKAN model
# By: Axel Haustant <axel@haustant.fr>
#
# Copyright (C) 2013 Axel Haustant
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

from weckan.model import User, Member, Role, Group, Package, meta

DB = meta.Session


def get_user_from_request(request):
    '''Simple user fetching from request'''
    username = request.environ.get('repoze.who.identity', {}).get('repoze.who.userid')
    return User.get(username) if username else None


def can_edit_dataset(user, dataset):
    '''Returns True if a given user can edit a given dataset'''
    if user is None:
        return False
    if user.sysadmin or dataset.owner_org is None:
        return True

    query = DB.query(Member).filter(
        Member.capacity.in_(['admin', 'editor']),
        Member.group_id == dataset.owner_org,
        Member.state == 'active',
        Member.table_id == user.id,
        Member.table_name == 'user',
    )
    return query.count() > 0


def can_edit_org(user, organization):
    '''Returns True if a given user can edit a given organization'''
    if user is None:
        return False
    if user.sysadmin:
        return True

    query = DB.query(Member).filter(
        Member.capacity == 'admin',
        Member.group_id == organization.id,
        Member.state == 'active',
        Member.table_id == user.id,
        Member.table_name == 'user',
    )
    return query.count() > 0


def get_role_for(user, target):
    if user is None:
        return None
    if user.sysadmin:
        return Role.ADMIN

    if isinstance(target, Group):
        group_id = target.id
    elif isinstance(target, Package):
        group_id = target.owner_org
    else:
        raise ValueError('Unhandled type {0}'.format(type(target)))
    query = DB.query(Member.capacity).filter(
        Member.group_id == group_id,
        Member.state == 'active',
        Member.table_id == user.id,
        Member.table_name == 'user',
    )

    result = query.first()
    return result[0] if result else None
