# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import futures
import logging

from weckan import templates, urls, wsgihelpers, contexts, queries, territories

from weckan.controllers import dashboard, dataset, group, organization, redirect, reuse, resource, tags, wiki


log = logging.getLogger(__name__)
router = None

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
            executor.submit(wiki.search, query),
        ]

    results = dict(worker.result() for worker in futures.as_completed(workers))

    return templates.render_site('search.html', request, search_query=query, has_ckan=False, **results)


@wsgihelpers.wsgify
def forbidden(request):
    return wsgihelpers.forbidden(contexts.Ctx(request))


def make_router(app):
    """Return a WSGI application that searches requests to controllers """
    global router
    controllers = group, organization, dashboard, dataset, redirect, resource, reuse, tags
    routes = (controller.routes for controller in controllers)
    routes = sum(routes, tuple())
    router = urls.make_router(app,
        ('GET', r'^(/(?P<lang>\w{2}))?/?$', home),
        ('GET', r'^(/(?P<lang>\w{2}))?/search/?$', search_results),
        ('GET', r'^(/(?P<lang>\w{2}))?/users/?$', forbidden),
        *routes
    )

    return router
