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

from ckan.model import User


def get_user_from_request(request):
    '''Simple user fetching from request'''
    auth_tkt = request.cookies.get('auth_tkt', None)

    if not auth_tkt:
        return None

    end = auth_tkt.index('!') if '!' in auth_tkt else len(auth_tkt)
    username = auth_tkt[40:end].decode('utf8')
    return User.by_name(username)