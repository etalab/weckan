# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging

from sqlalchemy.sql import func, distinct

from weckan import templates, urls, wsgihelpers, contexts, auth, forms
from weckan.model import meta, Package, Resource

from weckan.tools import ckan_api

from ckanext.youckan.models import CommunityResource


_ = lambda s: s
DB = meta.Session
log = logging.getLogger(__name__)


class ResourceForm(forms.Form):
    name = forms.StringField(_('Name'), [forms.validators.required()])
    resource_type = forms.RadioField(_('Type'), [forms.validators.required()], choices=(
        ('file', _('Link to a file')),
        ('api', _('Link to an API')),
        ('file.upload', _('Upload a file from your computer')),
    ))
    url = forms.URLField(_('URL'), [forms.RequiredIfVal('resource_type', ['file', 'api'])])
    file = forms.FileField(_('File'), [forms.RequiredIfVal('resource_type', 'file.upload')])
    format = forms.StringField(_('Format'), widget=forms.FormatAutocompleter())
    description = forms.MarkdownField(_('Description'), [forms.validators.required()])


class CommunityResourceForm(forms.Form):
    name = forms.StringField(_('Name'), [forms.validators.required()])
    url = forms.URLField(_('URL'), [forms.validators.required()])
    format = forms.StringField(_('Format'), widget=forms.FormatAutocompleter())
    description = forms.MarkdownField(_('Description'), [forms.validators.required()])
    publish_as = forms.PublishAsField(_('Publish as'))


@wsgihelpers.wsgify
def create_community(request):
    context = contexts.Ctx(request)
    lang = request.urlvars.get('lang', templates.DEFAULT_LANG)
    user = auth.get_user_from_request(request)
    if not user:
        return wsgihelpers.unauthorized(context)  # redirect to login/register ?

    dataset_name = request.urlvars.get('name')
    dataset_url = urls.get_url(lang, 'dataset', dataset_name)

    dataset = Package.get(dataset_name)
    if not dataset:
        return wsgihelpers.not_found(context)

    form = CommunityResourceForm(request.POST, i18n=context.translator)

    if request.method == 'POST' and form.validate():
        resource = CommunityResource(dataset.id, user.id)
        form.populate_obj(resource)
        DB.add(resource)
        DB.commit()
        return wsgihelpers.redirect(context, location=dataset_url)

    return templates.render_site('forms/resource-form.html', request, form=form, back_url=dataset_url)


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
    if not resource:
        return wsgihelpers.not_found(context)

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
        url = forms.handle_upload(request, form.file, user)
        ckan_api('resource_create', user, {
            'package_id': dataset_name,
            'name': form.name.data,
            'description': form.description.data,
            'url': url or form.url.data,
            'format': form.format.data,
            'resource_type': form.resource_type.data,
        })
        if 'add_another' in request.POST:
            return wsgihelpers.redirect(context, location=urls.get_url(lang, 'dataset/new_resource', dataset_name))
        return wsgihelpers.redirect(context, location=dataset_url)

    return templates.render_site('forms/resource-form.html', request, form=form, back_url=dataset_url)


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
        url = forms.handle_upload(request, form.file, user)
        ckan_api('resource_update', user, {
            'id': resource_id,
            'package_id': dataset_name,
            'name': form.name.data,
            'description': form.description.data,
            'url': url or form.url.data,
            'format': form.format.data,
        })
        return wsgihelpers.redirect(context, location=dataset_url)

    return templates.render_site('forms/resource-form.html', request, form=form, resource=resource,
            back_url=dataset_url, delete_url=delete_url)


@wsgihelpers.wsgify
def autocomplete_formats(request):
    context = contexts.Ctx(request)
    pattern = request.params.get('q', '')
    headers = wsgihelpers.handle_cross_origin_resource_sharing(context)

    if not pattern:
        return wsgihelpers.respond_json(context, [], headers=headers)

    pattern = '{0}%'.format(pattern)
    num = int(request.params.get('num', 0))

    query = DB.query(distinct(func.lower(Resource.format)).label('format'), func.count(Resource.id).label('count'))
    query = query.filter(Resource.format.ilike(pattern))
    query = query.order_by('count', 'format').group_by('format')
    if num:
        query = query.limit(num)

    data = [row[0] for row in query]
    return wsgihelpers.respond_json(context, data, headers=headers)


routes = (
    (('GET', 'POST'), r'^(/(?P<lang>\w{2}))?/dataset/new_resource/(?P<name>[\w_-]+)/?$', create),
    (('GET', 'POST'), r'^(/(?P<lang>\w{2}))?/dataset/(?P<name>[\w_-]+)/resource_edit/(?P<resource>[\w_-]+)/?$', edit),
    (('GET', 'POST'), r'^(/(?P<lang>\w{2}))?/dataset/(?P<name>[\w_-]+)/community/resource/new/?$', create_community),
    (('GET', 'POST'), r'^(/(?P<lang>\w{2}))?/dataset/(?P<name>[\w_-]+)/community/resource/(?P<resource>[\w_-]+)/edit/?$', edit_community),
    ('POST', r'^(/(?P<lang>\w{2}))?/dataset/(?P<name>[\w_-]+)/community/resource/(?P<resource>[\w_-]+)/delete/?$', delete_community),

    ('GET', r'^(/(?P<lang>\w{2}))?/format/autocomplete/?$', autocomplete_formats),
)
