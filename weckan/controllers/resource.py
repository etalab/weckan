# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging

from sqlalchemy.sql import func, distinct

from weckan import templates, urls, wsgihelpers, contexts, auth
from weckan.model import meta, Package, Resource

from weckan.forms import ResourceForm, CommunityResourceForm
from weckan.tools import ckan_api

from ckanext.youckan.models import CommunityResource


DB = meta.Session
log = logging.getLogger(__name__)


@wsgihelpers.wsgify
def create_community(request):
    context = contexts.Ctx(request)
    lang = request.urlvars.get('lang', templates.DEFAULT_LANG)
    user = auth.get_user_from_request(request)
    if not user:
        return wsgihelpers.unauthorized(context)  # redirect to login/register ?

    dataset_name = request.urlvars.get('name')
    dataset_url = urls.get_url(lang, 'dataset', dataset_name)

    form = CommunityResourceForm(request.POST, i18n=context.translator)

    if request.method == 'POST' and form.validate():
        dataset = Package.get(dataset_name)
        resource = CommunityResource(dataset.id, user.id)
        form.populate_obj(resource)
        DB.add(resource)
        DB.commit()
        return wsgihelpers.redirect(context, location=dataset_url)

    return templates.render_site('forms/resource-form.html', request, new=True, form=form, back_url=dataset_url)


@wsgihelpers.wsgify
def edit_community(request):
    context = contexts.Ctx(request)
    lang = request.urlvars.get('lang', templates.DEFAULT_LANG)
    user = auth.get_user_from_request(request)
    if not user:
        return wsgihelpers.unauthorized(context)  # redirect to login/register ?

    dataset_name = request.urlvars.get('name')
    dataset_url = urls.get_url(lang, 'dataset', dataset_name)

    resource_id = request.urlvars.get('resource')
    resource = CommunityResource.get(resource_id)
    delete_url = urls.get_url(lang, 'dataset', dataset_name, 'community/resource', resource_id, 'delete')

    form = CommunityResourceForm(request.POST, resource, i18n=context.translator)

    if request.method == 'POST' and form.validate():
        form.populate_obj(resource)
        DB.add(resource)
        DB.commit()
        return wsgihelpers.redirect(context, location=dataset_url)

    return templates.render_site('forms/resource-form.html', request, new=False, form=form,
            back_url=dataset_url, delete_url=delete_url)


@wsgihelpers.wsgify
def delete_community(request):
    context = contexts.Ctx(request)
    lang = request.urlvars.get('lang', templates.DEFAULT_LANG)
    user = auth.get_user_from_request(request)
    if not user:
        return wsgihelpers.unauthorized(context)  # redirect to login/register ?

    dataset_name = request.urlvars.get('name')
    dataset_url = urls.get_url(lang, 'dataset', dataset_name)

    resource_id = request.urlvars.get('resource')
    resource = CommunityResource.get(resource_id)

    if not user.sysadmin and not resource.owner_id == user.id:
        return wsgihelpers.unauthorized(context)  # redirect to login/register ?

    DB.delete(resource)
    DB.commit()

    return wsgihelpers.redirect(context, location=dataset_url)



@wsgihelpers.wsgify
def create(request):
    context = contexts.Ctx(request)
    lang = request.urlvars.get('lang', templates.DEFAULT_LANG)
    user = auth.get_user_from_request(request)
    if not user:
        return wsgihelpers.unauthorized(context)  # redirect to login/register ?

    dataset_name = request.urlvars.get('name')
    dataset_url = urls.get_url(lang, 'dataset', dataset_name)

    form = ResourceForm(request.POST, i18n=context.translator)

    if request.method == 'POST' and form.validate():
        ckan_api('resource_create', user, {
            'package_id': dataset_name,
            'name': form.name.data,
            'description': form.description.data,
            'url': form.url.data,
            'format': form.format.data,
        })
        return wsgihelpers.redirect(context, location=dataset_url)

    return templates.render_site('forms/resource-form.html', request, new=True, form=form, back_url=dataset_url)


@wsgihelpers.wsgify
def edit(request):
    context = contexts.Ctx(request)
    lang = request.urlvars.get('lang', templates.DEFAULT_LANG)
    user = auth.get_user_from_request(request)
    if not user:
        return wsgihelpers.unauthorized(context)  # redirect to login/register ?

    dataset_name = request.urlvars.get('name')
    dataset_url = urls.get_url(lang, 'dataset', dataset_name)

    resource_id = request.urlvars.get('resource')
    resource = Resource.get(resource_id)
    delete_url = urls.get_url(lang, 'dataset', dataset_name, 'resource_delete', resource_id)

    form = ResourceForm(request.POST, resource, i18n=context.translator)

    if request.method == 'POST' and form.validate():
        ckan_api('resource_update', user, {
            'id': resource_id,
            'package_id': dataset_name,
            'name': form.name.data,
            'description': form.description.data,
            'url': form.url.data,
            'format': form.format.data,
        })
        return wsgihelpers.redirect(context, location=dataset_url)

    return templates.render_site('forms/resource-form.html', request, new=False, form=form,
            back_url=dataset_url, delete_url=delete_url)


@wsgihelpers.wsgify
def autocomplete_formats(request):
    context = contexts.Ctx(request)
    pattern = '{0}%'.format(request.params.get('q', ''))
    num = int(request.params.get('num', 0))

    query = DB.query(distinct(func.lower(Resource.format)).label('format'))
    query = query.filter(Resource.format.ilike(pattern))
    query = query.order_by('format')
    if num:
        query = query.limit(num)

    data = [row[0] for row in query]
    headers = wsgihelpers.handle_cross_origin_resource_sharing(context)
    return wsgihelpers.respond_json(context, data, headers=headers)


routes = (
    (('GET', 'POST'), r'^(/(?P<lang>\w{2}))?/dataset/new_resource/(?P<name>[\w_-]+)/?$', create),
    (('GET', 'POST'), r'^(/(?P<lang>\w{2}))?/dataset/(?P<name>[\w_-]+)/resource_edit/(?P<resource>[\w_-]+)/?$', edit),
    (('GET', 'POST'), r'^(/(?P<lang>\w{2}))?/dataset/(?P<name>[\w_-]+)/community/resource/new/?$', create_community),
    (('GET', 'POST'), r'^(/(?P<lang>\w{2}))?/dataset/(?P<name>[\w_-]+)/community/resource/(?P<resource>[\w_-]+)/edit/?$', edit_community),
    ('POST', r'^(/(?P<lang>\w{2}))?/dataset/(?P<name>[\w_-]+)/community/resource/(?P<resource>[\w_-]+)/delete/?$', delete_community),

    ('GET', r'^(/(?P<lang>\w{2}))?/format/autocomplete/?$', autocomplete_formats),
)
