# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging

from sqlalchemy.sql import func, distinct

from weckan import wsgihelpers, contexts
from weckan.model import meta, Tag, PackageTag


DB = meta.Session
log = logging.getLogger(__name__)


@wsgihelpers.wsgify
def autocomplete(request):
    context = contexts.Ctx(request)
    pattern = '{0}%'.format(request.params.get('q', ''))
    num = int(request.params.get('num', 0))

    query = DB.query(distinct(func.lower(Tag.name)).label('name'), func.count(PackageTag.package_id).label('total'))
    query = query.join(PackageTag)
    query = query.filter(Tag.name.ilike(pattern))
    query = query.order_by('total desc', 'name').group_by('name')
    if num:
        query = query.limit(num)

    data = [row[0] for row in query]
    headers = wsgihelpers.handle_cross_origin_resource_sharing(context)
    return wsgihelpers.respond_json(context, data, headers=headers)


routes = (
    ('GET', r'^(/(?P<lang>\w{2}))?/tags/autocomplete/?$', autocomplete),
)
