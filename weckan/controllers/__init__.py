# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import futures
import logging

from weckan import templates, urls, wsgihelpers, contexts, queries, territories

from weckan.controllers import dashboard, dataset, group, organization, redirect, reuse, resource, wiki


log = logging.getLogger(__name__)
router = None

EXCLUDED_PATTERNS = (
    'activity',
    'delete',
    'edit',
    'follow',
    'new',
    'new_metadata',
    'new_resource',
)

NB_DATASETS = 12


@wsgihelpers.wsgify
def home(request):
    context = contexts.Ctx(request)
    _ = context.translator.ugettext

    fake, results = dataset.search(None, request, page_size=NB_DATASETS)
    last_datasets = queries.last_datasets().limit(NB_DATASETS)

    dataset_tabs = (
        ('popular', _('Most popular'), results['results']),
        ('recents', _('Latest'), dataset.serialize(last_datasets)),
    )

    return templates.render_site('home.html', context,
        featured_reuses=queries.featured_reuses().limit(NB_DATASETS),
        territory=territories.get_cookie(request),
        dataset_tabs=dataset_tabs,
    )


@wsgihelpers.wsgify
def search_results(request):
    query = request.params.get('q', '')

    with futures.ThreadPoolExecutor(max_workers=3) as executor:
        workers = [
            executor.submit(dataset.search, query, request),
            executor.submit(organization.search, query),
            executor.submit(wiki.searck, query),
        ]

    results = dict(worker.result() for worker in futures.as_completed(workers))

    return templates.render_site('search.html', request, search_query=query, has_ckan=False, **results)


@wsgihelpers.wsgify
def forbidden(request):
    return wsgihelpers.forbidden(contexts.Ctx(request))


def make_router(app):
    """Return a WSGI application that searches requests to controllers """
    global router
    router = urls.make_router(app,
        ('GET', r'^(/(?P<lang>\w{2}))?/?$', home),
        ('GET', r'^(/(?P<lang>\w{2}))?/search/?$', search_results),
        ('GET', r'^(/(?P<lang>\w{2}))?/metrics/?$', dashboard.metrics),

        ('GET', r'^(/(?P<lang>\w{2}))?/dataset/?$', dataset.search_more),

        ('GET', r'^(/(?P<lang>\w{2}))?/dataset/autocomplete/?$', dataset.autocomplete),
        ('GET', r'^(/(?P<lang>\w{2}))?/dataset/(?P<name>[\w_-]+)/fork/?$', dataset.fork),
        ('GET', r'^(/(?P<lang>\w{2}))?/dataset/(?P<name>[\w_-]+)/reuse/(?P<reuse>[\w_-]+)/featured/?$', reuse.toggle_featured),
        ('GET', r'^(/(?P<lang>\w{{2}}))?/dataset/(?!{0}(/|$))(?P<name>[\w_-]+)/?$'.format('|'.join(EXCLUDED_PATTERNS)), dataset.display),

        (('GET', 'POST'), r'^(/(?P<lang>\w{2}))?/dataset/(?P<name>[\w_-]+)/related/new?$', reuse.create),
        (('GET', 'POST'), r'^(/(?P<lang>\w{2}))?/dataset/(?P<name>[\w_-]+)/related/edit/(?P<reuse>[\w_-]+)/?$', reuse.edit),

        # (('GET', 'POST'), r'^(/(?P<lang>\w{2}))?/dataset/new_resource/(?P<name>[\w_-]+)/?$', resource.create),
        # (('GET', 'POST'), r'^(/(?P<lang>\w{2}))?/dataset/(?P<name>[\w_-]+)/resource_edit/(?P<resource>[\w_-]+)/?$', resource.edit),
        (('GET', 'POST'), r'^(/(?P<lang>\w{2}))?/dataset/(?P<name>[\w_-]+)/community/resource/new/?$', resource.create_community),
        (('GET', 'POST'), r'^(/(?P<lang>\w{2}))?/dataset/(?P<name>[\w_-]+)/community/resource/(?P<resource>[\w_-]+)/edit/?$', resource.edit_community),
        ('POST', r'^(/(?P<lang>\w{2}))?/dataset/(?P<name>[\w_-]+)/community/resource/(?P<resource>[\w_-]+)/delete/?$', resource.delete_community),

        ('GET', r'^(/(?P<lang>\w{2}))?/organizations?/?$', organization.search_more),
        ('GET', r'^(/(?P<lang>\w{2}))?/organizations?/autocomplete/?$', organization.autocomplete),
        (('GET', 'POST'), r'^(/(?P<lang>\w{2}))?/organization/new/?$', organization.create),
        # (('GET', 'POST'), r'^(/(?P<lang>\w{2}))?/organization/edit/(?P<name>[\w_-]+)/?$', organization.edit),
        ('GET', r'^(/(?P<lang>\w{{2}}))?/organization/(?!{0}(/|$))(?P<name>[\w_-]+)/?$'.format('|'.join(EXCLUDED_PATTERNS)), organization.display),

        (('GET', 'POST'), r'^(/(?P<lang>\w{2}))?/group/new/?$', group.create),
        # (('GET', 'POST'), r'^(/(?P<lang>\w{2}))?/group/edit/(?P<name>[\w_-]+)/?$', group.edit),
        ('GET', r'^(/(?P<lang>\w{{2}}))?/groups?/(?!{0}(/|$))(?P<name>[\w_-]+)/?$'.format('|'.join(EXCLUDED_PATTERNS)), group.display),

        ('GET', r'^(/(?P<lang>\w{2}))?/unfeature/(?P<reuse>[\w_-]+)/?$', reuse.unfeature),

        ('GET', r'^(/(?P<lang>\w{2}))?/format/autocomplete/?$', resource.autocomplete_formats),

        # Override some CKAN URLs
        ('GET', r'^(/(?P<lang>\w{2}))?/user/_?logout/?$', redirect.to_logout),
        ('GET', r'^(/(?P<lang>\w{2}))?/user/register/?$', redirect.to_login),
        ('GET', r'^(/(?P<lang>\w{2}))?/user/login/?$', redirect.to_login),
        ('GET', r'^(/(?P<lang>\w{2}))?/register/?$', redirect.to_login),
        ('GET', r'^(/(?P<lang>\w{2}))?/login/?$', redirect.to_login),
        ('GET', r'^(/(?P<lang>\w{2}))?/user/(?P<username>[\w_-]+)/?$', redirect.to_profile),
        ('GET', r'^(/(?P<lang>\w{2}))?/user/edit/(?P<username>[\w_-]+)/?$', redirect.to_account),
        ('GET', r'^(/(?P<lang>\w{2}))?/users/?$', forbidden),
        ('GET', r'^(/(?P<lang>\w{2}))?/about/?$', redirect.to_home),
    )

    return router
