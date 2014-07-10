# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import futures
import logging

from weckan import redirections, templates, urls, wsgihelpers, contexts, queries, territories

from weckan.controllers import dashboard, dataset, group, organization, redirect, reuse, resource, tags, wiki


log = logging.getLogger(__name__)
router = None

NB_DATASETS = 12


@wsgihelpers.wsgify
def home(request):
    context = contexts.Ctx(request)
    _ = context.translator.ugettext

    fake, results = dataset.search(None, request, page_size=NB_DATASETS)
    last_datasets = queries.last_datasets(False).limit(NB_DATASETS)

    dataset_tabs = (
        ('popular', _('Most popular'), results['results']),
        ('recent', _('Latest'), dataset.serialize(last_datasets)),
    )

    return templates.render_site('home.html', context,
        featured_reuses=queries.featured_reuses().limit(NB_DATASETS),
        territory=territories.get_cookie(request),
        dataset_tabs=dataset_tabs,
    )


@wsgihelpers.wsgify
def redevances(request):
    return templates.render_site('redevances.html', contexts.Ctx(request))


@wsgihelpers.wsgify
def search_results(request):
    query = request.params.get('q', '')

    with futures.ThreadPoolExecutor(max_workers=3) as executor:
        workers = [
            executor.submit(dataset.search, query, request),
            executor.submit(organization.search, query),
            executor.submit(wiki.search, query),
        ]

    results = dict(worker.result() for worker in futures.as_completed(workers))

    return templates.render_site('search.html', request, search_query=query, has_ckan=False, **results)


@wsgihelpers.wsgify
def forbidden(request):
    return wsgihelpers.forbidden(contexts.Ctx(request))


@wsgihelpers.wsgify
def error404(request):
    return wsgihelpers.error(contexts.Ctx(request), 404)


@wsgihelpers.wsgify
def error(request):
    context = contexts.Ctx(request)
    code = int(request.urlvars.get('code', 500) or 500)
    return wsgihelpers.error(context, code)


@wsgihelpers.wsgify
def redirect_old_dataset(request):
    context = contexts.Ctx(request)
    dataset_name = redirections.dataset_name_by_old_id.get(request.urlvars['id'])
    if dataset_name is None:
        return wsgihelpers.not_found(context)
    return wsgihelpers.redirect(context, location = urls.get_url(context, 'fr', 'dataset', dataset_name))


def make_router(app):
    """Return a WSGI application that searches requests to controllers """
    global router
    controllers = group, organization, dashboard, dataset, redirect, resource, reuse, tags
    routes = (controller.routes for controller in controllers)
    routes = sum(routes, tuple())
    catchall = (
        ('GET', r'^(/(?P<lang>\w{2}))?/[\w\d_-]+/?$', error404),
    )
    routes = routes + catchall
    router = urls.make_router(app,
        ('GET', r'^/DataSet/(?P<id>\d+)/?$', redirect_old_dataset),
        ('GET', r'^/Redevances/?$', redevances),
        ('GET', r'^(/(?P<lang>\w{2}))?/?$', home),
        ('GET', r'^(/(?P<lang>\w{2}))?/error(/(?P<code>\d{3}))?/?$', error),
        ('GET', r'^(/(?P<lang>\w{2}))?/search/?$', search_results),
        ('GET', r'^(/(?P<lang>\w{2}))?/users/?$', forbidden),
        *routes
    )

    return router
