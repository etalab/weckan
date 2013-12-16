# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging

from ckanext.youckan.models import ReuseAsOrganization

from weckan import templates, urls, wsgihelpers, contexts, auth, forms
from weckan.model import meta, Related, Group, User
from weckan.tools import ckan_api


_ = lambda s: s
DB = meta.Session
log = logging.getLogger(__name__)


class ReuseForm(forms.Form):
    title = forms.StringField(_('Title'), [forms.validators.required()])
    url = forms.URLField(_('URL'), [forms.validators.required()])
    image_url = forms.URLField(_('Image URL'), [forms.validators.required()])
    type = forms.SelectField(_('Type'), [forms.validators.required()], choices=(
        ('api', _('API')),
        ('application', _('Application')),
        ('idea', _('Idea')),
        ('news_article', _('News Article')),
        ('paper', _('Paper')),
        ('post', _('Post')),
        ('visualization', _('Visualization')),
    ))
    description = forms.MarkdownField(_('Description'), [forms.validators.required()])
    publish_as = forms.PublishAsField(_('Publish as'))


@wsgihelpers.wsgify
def create(request):
    context = contexts.Ctx(request)
    lang = request.urlvars.get('lang', templates.DEFAULT_LANG)

    dataset_name = request.urlvars.get('name')
    dataset_url = urls.get_url(lang, 'dataset', dataset_name)

    user = auth.get_user_from_request(request)
    if not user:
        return wsgihelpers.unauthorized(context)  # redirect to login/register ?

    form = ReuseForm(request.POST, i18n=context.translator)

    if request.method == 'POST' and form.validate():
        data = ckan_api('related_create', user, {
            'title': form.title.data,
            'description': form.description.data,
            'url': form.url.data,
            'image_url': form.image_url.data,
            'type': form.type.data,
            'dataset_id': dataset_name,
        })

        org_id = request.POST.get('publish_as')
        if org_id:
            reuse = Related.get(data['result']['id'])
            organization = Group.get(org_id)
            reuse_as_org = ReuseAsOrganization(reuse, organization)
            DB.add(reuse_as_org)
            DB.commit()

        return wsgihelpers.redirect(context, location=dataset_url)

    return templates.render_site('forms/reuse-form.html', request, new=True, form=form, back_url=dataset_url)


@wsgihelpers.wsgify
def edit(request):
    context = contexts.Ctx(request)
    lang = request.urlvars.get('lang', templates.DEFAULT_LANG)

    dataset_name = request.urlvars.get('name')
    dataset_url = urls.get_url(lang, 'dataset', dataset_name)

    reuse_id = request.urlvars.get('reuse')
    reuse = Related.get(reuse_id)
    owner = User.get(reuse.owner_id)
    publish_as = ReuseAsOrganization.get(reuse)
    delete_url = urls.get_url(lang, 'dataset', dataset_name, 'related/delete', reuse.id)

    user = auth.get_user_from_request(request)
    if not user:
        return wsgihelpers.unauthorized(context)  # redirect to login/register ?

    form = ReuseForm(request.POST, reuse,
        publish_as=publish_as.organization.id if publish_as else None,
        i18n=context.translator,
    )

    if request.method == 'POST' and form.validate():
        ckan_api('related_update', user, {
            'id': reuse_id,
            'title': form.title.data,
            'description': form.description.data,
            'url': form.url.data,
            'image_url': form.image_url.data,
            'type': form.type.data,
            'owner_id': reuse.owner_id,
            'dataset_id': dataset_name,
        })

        org_id = request.POST.get('publish_as')
        if org_id:
            organization = Group.get(org_id)
            if publish_as:
                publish_as.organization = organization
            else:
                publish_as = ReuseAsOrganization(reuse, organization)
            DB.add(publish_as)
            DB.commit()
        elif publish_as:
            DB.delete(publish_as)
            DB.commit()

        return wsgihelpers.redirect(context, location=dataset_url)

    return templates.render_site('forms/reuse-form.html', request, new=False, form=form, owner=owner,
            back_url=dataset_url, delete_url=delete_url)


@wsgihelpers.wsgify
def toggle_featured(request, value=None, url=None):
    user = auth.get_user_from_request(request)
    context = contexts.Ctx(request)
    if not user or not user.sysadmin:
        return wsgihelpers.unauthorized(context)  # redirect to login/register ?

    reuse_id = request.urlvars.get('reuse')

    reuse = Related.get(reuse_id)
    reuse.featured = value if value is not None else (0 if reuse.featured else 1)
    DB.commit()

    if not url:
        dataset_name = request.urlvars.get('name')
        url = urls.get_url(request.urlvars.get('lang', templates.DEFAULT_LANG), 'dataset', dataset_name)
    return wsgihelpers.redirect(context, location=url)


@wsgihelpers.wsgify
def unfeature(request):
    return toggle_featured(request, 0, urls.get_url(request.urlvars.get('lang', templates.DEFAULT_LANG)))


routes = (
    (('GET', 'POST'), r'^(/(?P<lang>\w{2}))?/dataset/(?P<name>[\w_-]+)/related/new?$', create),
    (('GET', 'POST'), r'^(/(?P<lang>\w{2}))?/dataset/(?P<name>[\w_-]+)/related/edit/(?P<reuse>[\w_-]+)/?$', edit),
    ('GET', r'^(/(?P<lang>\w{2}))?/dataset/(?P<name>[\w_-]+)/reuse/(?P<reuse>[\w_-]+)/featured/?$', toggle_featured),
    ('GET', r'^(/(?P<lang>\w{2}))?/unfeature/(?P<reuse>[\w_-]+)/?$', unfeature),
)
