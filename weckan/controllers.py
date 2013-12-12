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

"""Root controllers"""

from __future__ import unicode_literals

import futures
import json
import logging
import math
import requests

from datetime import datetime
from urllib import urlencode

from biryani1 import strings
from sqlalchemy.sql import func, and_, or_, distinct

from . import templates, urls, wsgihelpers, conf, contexts, auth, queries
from .model import Activity, meta, Package, Related, Group, Resource
from .model import Role, UserFollowingDataset, UserFollowingGroup, User

from weckan.forms import ReuseForm, ResourceForm, GroupCreateForm

from ckanext.etalab.model import CertifiedPublicService
from ckanext.youckan.models import MembershipRequest, ReuseAsOrganization, CommunityResource


DB = meta.Session
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

SEARCH_MAX_ORGANIZATIONS = 2
SEARCH_MAX_TOPICS = 2
SEARCH_MAX_QUESTIONS = 2
SEARCH_PAGE_SIZE = 20

SEARCH_TIMEOUT = 2
POST_TIMEOUT = 3

NB_DATASETS = 12

QA_CEILS = {
    'warning': 10,
    'error': 10,
    'criticals': 1,
}


def build_territorial_coverage(dataset):
    return {
        'name': ', '.join(
            territory.strip().rsplit('/', 1)[-1].title()
            for territory in dataset.extras.get('territorial_coverage', '').split(',')
        ),
        'granularity': dataset.extras.get('territorial_coverage_granularity', '').title() or None,
    }


def build_temporal_coverage(dataset):
    temporal_coverage = {
        'from': dataset.extras.get('temporal_coverage_from', None),
        'to': dataset.extras.get('temporal_coverage_to', None),
    }
    try:
        temporal_coverage['from'] = datetime.strptime(temporal_coverage['from'], '%Y-%m-%d')
    except:
        pass
    try:
        temporal_coverage['to'] = datetime.strptime(temporal_coverage['to'], '%Y-%m-%d')
    except:
        pass

    return temporal_coverage


def build_datasets(query):
    '''Build datasets for display from a queryset'''
    datasets = []

    for dataset, organization in query:
        datasets.append({
            'name': dataset.name,
            'title': dataset.title,
            'display_name': dataset.display_name,
            'notes': dataset.notes,
            'organization': organization,
            'temporal_coverage': build_temporal_coverage(dataset),
            'territorial_coverage': build_territorial_coverage(dataset),
            'periodicity': dataset.extras.get('"dct:accrualPeriodicity"', None),
            'original': queries.forked_from(dataset).first(),
            'nb_reuses': len(dataset.related),
        })

    return datasets


def ckan_api(action, user, data, timeout=None):
    '''Perform a CKAN Action API call'''
    url = '{0}/api/3/action/{1}'.format(conf['ckan_url'], action)
    headers = {
        'content-type': 'application/json',
        'Authorization': user.apikey,
    }
    try:
        response = requests.post(url, headers=headers, data=json.dumps(data), timeout=timeout)
        response.raise_for_status()
    except requests.RequestException:
        log.exception('Error on CKAN API for action %s', action)
        raise
    return response.json()


def search_datasets(query, request, page=1, page_size=SEARCH_PAGE_SIZE, group=None, organization=None):
    '''Perform a Dataset search given a ``query``'''
    from ckan.lib import search

    if request.cookies.get('territory-infos', '').count('|') == 1:
        territory_key, _ = request.cookies.get('territory-infos').split('|')
        territory = get_territory(*territory_key.split('/')) if territory_key else {}
    else:
        territory = {}

    page_zero = page - 1
    params = {
        'bf': u'{}^2'.format(
            dict(
                ArrondissementOfCommuneOfFrance = 'weight_commune',
                CommuneOfFrance = 'weight_commune',
                Country = 'weight',
                DepartmentOfFrance = 'weight_department',
                OverseasCollectivityOfFrance = 'weight_department',
                RegionOfFrance = 'weight_region',
                ).get(territory.get('kind'), 'weight'),
            ),
        'defType': u'edismax',
        'fq': '+dataset_type:dataset',
        'q': query or '',
        'qf': u'name title groups^0.5 notes^0.5 tags^0.5 text^0.25',
        'rows': page_size,
        'sort': 'score desc, metadata_modified desc',
        'start': page_zero * page_size,
        }

    if group:
        group_name = group.name if isinstance(group, Group) else group
        params['fq'] = ' '.join([params['fq'], '+groups:{0}'.format(group_name)])

    if organization:
        org_name = organization.name if isinstance(organization, Group) else organization
        params['fq'] = ' '.join([params['fq'], '+organization:{0}'.format(org_name)])

    # Territory search if specified
    ancestors_kind_code = territory.get('ancestors_kind_code')
    if ancestors_kind_code:
        territories = [
            '{}/{}'.format(ancestor_kind_code['kind'], ancestor_kind_code['code'])
            for ancestor_kind_code in ancestors_kind_code
            ]
        params['fq'] = '{} +covered_territories:({})'.format(params['fq'], ' OR '.join(territories))

    query = search.query_for(Package)
    query.run(params)

    if not query.results:
        return 'datasets', {'results': [], 'total': 0}

    datasets_query = queries.datasets()
    datasets_query = datasets_query.filter(Package.name.in_(query.results))
    datasets = build_datasets(datasets_query.all())

    return 'datasets', {
        'results': sorted(datasets, key=lambda d: query.results.index(d['name'])),
        'total': query.count,
        'page': page,
        'page_size': page_size,
        'total_pages': int(math.ceil(query.count / float(page_size))),
    }


def search_organizations(query, page=1, page_size=SEARCH_MAX_ORGANIZATIONS):
    '''Perform an organization search given a ``query``'''
    likes = ['%{0}%'.format(word) for word in query.split() if word]

    organizations = queries.organizations_and_counters()
    if likes:
        organizations = organizations.filter(or_(
            and_(*(Group.name.ilike(like) for like in likes)),
            and_(*(Group.title.ilike(like) for like in likes)),
            # GroupRevision.description.ilike(like),
        ))

    total = organizations.count()
    start = (page - 1) * page_size
    end = start + page_size
    return 'organizations', {
        'results': organizations[start:end],
        'total': total,
        'page': page,
        'page_size': page_size,
        'total_pages': int(math.ceil(total / float(page_size))),
    }


def search_topics(query):
    '''Perform a topic search given a ``query``'''
    params = {
        'format': 'json',
        'action': 'query',
        'list': 'search',
        'srsearch': query,
        'srprop': 'timestamp',
        'srlimit': SEARCH_MAX_TOPICS,
    }
    try:
        response = requests.get(conf['wiki_api_url'], params=params, timeout=SEARCH_TIMEOUT)
        response.raise_for_status()
    except requests.RequestException:
        log.exception('Unable to fetch topics')
        return 'topics', {'results': [], 'more': False}
    json_response = response.json()
    return 'topics', {
        'results': json_response.get('query', {}).get('search', []),
        'more': 'query-continue' in json_response,
    }


def get_territory(kind, code):
    '''Perform a Territory API Call'''
    url = '{0}/territory'.format(conf['territory_api_url'])
    params = {
        'kind': kind,
        'code': code,
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
    except requests.RequestException:
        log.exception('Unable to fetch territory')
        return {}
    return response.json().get('data', {})


def get_territory_cookie(request):
    if request.cookies.get('territory-infos', '').count('|') == 1:
        territory_key, _ = request.cookies.get('territory-infos').split('|')
        territory = get_territory(*territory_key.split('/')) if territory_key else {}
    else:
        territory = {}

    return {
        'full_name': territory.get('full_name', ''),
        'full_name_slug': strings.slugify(territory.get('full_name', '')),
        'depcom': territory.get('code', '')
    }


def get_page_url_pattern(request):
    '''Get a formattable page url pattern from incoming request URL'''
    url_pattern_params = {}
    for key, value in request.params.iteritems():
        if key != 'page':
            url_pattern_params[key] = unicode(value).encode('utf-8')
    if url_pattern_params:
        return '?'.join([request.path, urlencode(url_pattern_params)]) + '&page={page}'
    else:
        return '?'.join([request.path, 'page={page}'])


def get_dataset_quality(dataset_name):
    '''Fetch the dataset quality scores from COW'''
    url = '{0}/api/1/datasets/{1}/ranking'.format(conf['cow_url'], dataset_name)
    try:
        response = requests.get(url, timeout=SEARCH_TIMEOUT)
        response.raise_for_status()
    except requests.RequestException as request_exception:
        log.warning('Unable to fetch quality scores for %s: %s', dataset_name, request_exception)
        return None
    data = response.json().get('value', {})
    return data


@wsgihelpers.wsgify
def home(request):
    context = contexts.Ctx(request)
    _ = context.translator.ugettext

    fake, results = search_datasets(None, request, page_size=NB_DATASETS)
    last_datasets = queries.last_datasets().limit(NB_DATASETS)

    dataset_tabs = (
        ('popular', _('Most popular'), results['results']),
        ('recents', _('Latest'), build_datasets(last_datasets)),
    )

    return templates.render_site('home.html', context,
        featured_reuses=queries.featured_reuses().limit(NB_DATASETS),
        territory=get_territory_cookie(request),
        dataset_tabs=dataset_tabs,
    )


@wsgihelpers.wsgify
def display_organization(request):
    user = auth.get_user_from_request(request)
    context = contexts.Ctx(request)
    _ = context.translator.ugettext

    organization_name = request.urlvars.get('name')

    query = queries.organizations_and_counters()
    query = query.filter(Group.name == organization_name)

    if not query.count():
        return wsgihelpers.not_found(context)

    organization, nb_datasets, nb_members = query.first()

    last_datasets = queries.last_datasets()
    last_datasets = last_datasets.filter(Package.owner_org == organization.id)
    last_datasets = last_datasets.limit(NB_DATASETS)

    fake, results = search_datasets(None, request, page_size=NB_DATASETS, organization=organization)

    dataset_tabs = (
        ('popular', _('Most popular'), results['results']),
        ('recents', _('Latest'), build_datasets(last_datasets)),
    )

    role = auth.get_role_for(user, organization)
    is_member = user and user.is_in_group(organization.id)
    is_admin = (is_member and role == Role.ADMIN) or (user and user.sysadmin)
    is_editor = is_admin or (is_member and role == Role.EDITOR)

    if is_admin:
        private_datasets = queries.datasets(private=True)
        private_datasets = private_datasets.filter(Package.owner_org == organization.id)
        private_datasets = private_datasets.limit(NB_DATASETS)
        dataset_tabs += (
            ('privates', _('Privates'), build_datasets(private_datasets)),
        )

    return templates.render_site('organization.html', context,
        organization=organization,
        nb_members=nb_members,
        nb_datasets=nb_datasets,
        nb_followers=UserFollowingGroup.follower_count(organization.id),
        is_following=UserFollowingGroup.is_following(user.id, organization.id) if organization and user else False,
        is_member=is_member,
        is_admin=is_admin,
        is_editor=is_editor,
        pending=(not is_member and MembershipRequest.is_pending(organization, user)),
        can_edit=auth.can_edit_org(user, organization),
        territory=get_territory_cookie(request),
        dataset_tabs=dataset_tabs,
        pending_requests=MembershipRequest.pending_for(organization) if is_admin else None,
    )


@wsgihelpers.wsgify
def display_dataset(request):
    user = auth.get_user_from_request(request)

    dataset_name = request.urlvars.get('name')

    query = DB.query(Package, Group, func.min(Activity.timestamp))
    query = query.outerjoin(Group, Group.id == Package.owner_org)
    query = query.outerjoin(Activity, Activity.object_id == Package.id)
    query = query.filter(Package.name == dataset_name)
    query = query.group_by(Package, Group)

    if not query.count():
        return wsgihelpers.not_found(contexts.Ctx(request))

    dataset, organization, timestamp = query.first()

    periodicity = dataset.extras.get('"dct:accrualPeriodicity"', None)

    supplier_id = dataset.extras.get('supplier_id', None)
    supplier = DB.query(Group).filter(Group.id == supplier_id).first() if supplier_id else None

    return templates.render_site('dataset.html', request,
        dataset=dataset,
        publication_date=timestamp,
        organization=organization,
        is_following_org=UserFollowingGroup.is_following(user.id, organization.id) if organization and user else False,
        supplier=supplier,
        owner=queries.owner(dataset).first(),
        nb_followers=UserFollowingDataset.follower_count(dataset.id),
        is_following=UserFollowingDataset.is_following(user.id, dataset.id) if user else False,
        territorial_coverage=build_territorial_coverage(dataset),
        temporal_coverage=build_temporal_coverage(dataset),
        periodicity=periodicity,
        groups=dataset.get_groups('group'),
        can_edit=auth.can_edit_dataset(user, dataset),
        is_fork=queries.is_fork(dataset),
        quality=get_dataset_quality(dataset.name),
        ceils=QA_CEILS,
        territory=get_territory_cookie(request),
        bot_name=conf['bot_name'],
    )


@wsgihelpers.wsgify
def create_reuse(request):
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
def edit_reuse(request):
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
def create_community_resource(request):
    context = contexts.Ctx(request)
    lang = request.urlvars.get('lang', templates.DEFAULT_LANG)
    user = auth.get_user_from_request(request)
    if not user:
        return wsgihelpers.unauthorized(context)  # redirect to login/register ?

    dataset_name = request.urlvars.get('name')
    dataset_url = urls.get_url(lang, 'dataset', dataset_name)

    form = ResourceForm(request.POST, i18n=context.translator)

    if request.method == 'POST' and form.validate():
        dataset = Package.get(dataset_name)
        resource = CommunityResource(dataset.id, user.id)
        form.populate_obj(resource)
        DB.add(resource)
        DB.commit()
        return wsgihelpers.redirect(context, location=dataset_url)

    return templates.render_site('forms/resource-form.html', request, new=True, form=form, back_url=dataset_url)


@wsgihelpers.wsgify
def edit_community_resource(request):
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

    form = ResourceForm(request.POST, resource, i18n=context.translator)

    if request.method == 'POST' and form.validate():
        form.populate_obj(resource)
        DB.add(resource)
        DB.commit()
        return wsgihelpers.redirect(context, location=dataset_url)

    return templates.render_site('forms/resource-form.html', request, new=False, form=form,
            back_url=dataset_url, delete_url=delete_url)


@wsgihelpers.wsgify
def delete_community_resource(request):
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
def create_group_or_org(request, is_org):
    context = contexts.Ctx(request)
    lang = request.urlvars.get('lang', templates.DEFAULT_LANG)
    user = auth.get_user_from_request(request)
    if not user:
        return wsgihelpers.unauthorized(context)  # redirect to login/register ?

    form = GroupCreateForm(request.POST, i18n=context.translator)

    if request.method == 'POST' and form.validate():
        name = strings.slugify(form.title.data)
        ckan_api('organization_create' if is_org else 'group_create', user, {
            'name': name,
            'title': form.title.data,
            'description': form.description.data,
            'image_url': form.image_url.data,
        })

        redirect_url = urls.get_url(lang, 'organization' if is_org else 'group', name)
        return wsgihelpers.redirect(context, location=redirect_url)

    back_url = urls.get_url(lang, 'organizations' if is_org else 'groups')
    return templates.render_site('forms/group-create-form.html', request, new=True, is_org=is_org, form=form, back_url=back_url)


@wsgihelpers.wsgify
def create_group(request):
    return create_group_or_org(request, False)


@wsgihelpers.wsgify
def create_organization(request):
    return create_group_or_org(request, True)


@wsgihelpers.wsgify
def display_search_results(request):
    query = request.params.get('q', '')

    with futures.ThreadPoolExecutor(max_workers=3) as executor:
        workers = [
            executor.submit(search_datasets, query, request),
            executor.submit(search_organizations, query),
            executor.submit(search_topics, query),
        ]

    results = dict(worker.result() for worker in futures.as_completed(workers))

    return templates.render_site('search.html', request, search_query=query, has_ckan=False, **results)


@wsgihelpers.wsgify
def search_more_datasets(request):
    query = request.params.get('q', '')
    page = int(request.params.get('page', 1))
    _, results = search_datasets(query, request, page, SEARCH_PAGE_SIZE)
    return templates.render_site('search-datasets.html', request,
        search_query=query,
        url_pattern=get_page_url_pattern(request),
        datasets=results
        )


@wsgihelpers.wsgify
def autocomplete_datasets(request):
    query = request.params.get('q', '')
    num = int(request.params.get('num', NB_DATASETS))
    _, results = search_datasets(query, request, 1, num)

    context = contexts.Ctx(request)
    headers = wsgihelpers.handle_cross_origin_resource_sharing(context)
    data = [{
            'name': dataset['name'],
            'title': dataset['display_name'],
            'image_url': (
                (dataset['organization'].image_url if dataset['organization'] else None)
                or templates.static('/img/placeholder_producer.png')
            ),
        } for dataset in results['results']]

    return wsgihelpers.respond_json(context, data, headers=headers)


@wsgihelpers.wsgify
def autocomplete_organizations(request):
    query = request.params.get('q', '')
    num = int(request.params.get('num', SEARCH_MAX_ORGANIZATIONS))
    _, results = search_organizations(query, 1, num)

    context = contexts.Ctx(request)
    headers = wsgihelpers.handle_cross_origin_resource_sharing(context)

    data = [{
            'name': organization.name,
            'title': organization.display_name,
            'image_url': organization.image_url or templates.static('/img/placeholder_producer.png'),
        } for organization, _, _ in results['results']]

    return wsgihelpers.respond_json(context, data, headers=headers)


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


@wsgihelpers.wsgify
def search_more_organizations(request):
    query = request.params.get('q', '')
    page = int(request.params.get('page', 1))
    _, results = search_organizations(query, page, SEARCH_PAGE_SIZE)
    return templates.render_site('search-organizations.html', request,
        search_query=query,
        url_pattern=get_page_url_pattern(request),
        organizations=results
        )


@wsgihelpers.wsgify
def display_group(request):
    group_name = request.urlvars.get('name')
    group = Group.by_name(group_name)
    page = int(request.params.get('page', 1))
    _, results = search_datasets('', request, page, SEARCH_PAGE_SIZE, group)
    main_groups = [t['name'] for t in templates.main_topics()]
    return templates.render_site('group.html', request,
        group=group,
        url_pattern=get_page_url_pattern(request),
        datasets=results,
        group_class='topic-{0}'.format(main_groups.index(group_name) + 1) if group_name in main_groups else None,
    )


@wsgihelpers.wsgify
def metrics(request):
    context = contexts.Ctx(request)
    _ = context._

    datasets = DB.query(Package).filter(Package.state == 'active', ~Package.private).count()

    reuses = DB.query(Related).count()

    resources = DB.query(Resource).filter(Resource.state == 'active').count()

    file_formats = DB.query(distinct(Resource.format)).count()

    organizations = DB.query(Group).filter(Group.is_organization == True, Group.state == 'active').count()

    certified_organizations = DB.query(CertifiedPublicService).join(Group).filter(Group.state == 'active').count()

    users = DB.query(User).count()

    return templates.render_site('metrics.html', request, ws_url=conf['ws_url'], metrics=(
        ('datasets_count', _('Datasets'), datasets),
        ('related_count', _('Reuses'), reuses),
        ('resources_count', _('Resources'), resources),
        ('organizations_count', _('Organizations'), organizations),
        ('certifieds', _('Certified organizations'), certified_organizations),
        ('users', _('Users'), users),
        ('datasets_total_weight', _('Total quality'), '...'),
        ('datasets_average_weight', _('Average quality'), '...'),
        ('datasets_median_weight', _('Median quality'), '...'),
        ('formats_count', _('File formats'), file_formats),
    ))


@wsgihelpers.wsgify
def fork_dataset(request):
    context = contexts.Ctx(request)

    user = auth.get_user_from_request(request)
    if not user:
        return wsgihelpers.unauthorized(context)  # redirect to login/register ?

    dataset_name = request.urlvars.get('name')

    url = '{0}/youckan/dataset/{1}/fork'.format(conf['ckan_url'], dataset_name)
    headers = {
        'content-type': 'application/json',
        'Authorization': user.apikey,
    }

    try:
        response = requests.post(url, headers=headers)
        response.raise_for_status()
    except requests.RequestException:
        log.exception('Unable to fork dataset')
        raise
    forked = response.json()

    lang = request.urlvars.get('lang', templates.DEFAULT_LANG)
    fork_url = urls.get_url(lang, 'dataset', forked['name'])
    # fork_url = urls.get_url(rlang, 'dataset/edit', forked['name'])

    return wsgihelpers.redirect(context, location=fork_url)


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
def unfeature_reuse(request):
    return toggle_featured(request, 0, urls.get_url(request.urlvars.get('lang', templates.DEFAULT_LANG)))


@wsgihelpers.wsgify
def redirect_to_home(request):
    return wsgihelpers.redirect(contexts.Ctx(request), location='/')


@wsgihelpers.wsgify
def redirect_to_login(request):
    url = '{0}/login/'.format(conf['sso_url'])
    return wsgihelpers.redirect(contexts.Ctx(request), location=url)


@wsgihelpers.wsgify
def redirect_to_logout(request):
    url = '{0}/logout/'.format(conf['sso_url'])
    return wsgihelpers.redirect(contexts.Ctx(request), location=url)


@wsgihelpers.wsgify
def redirect_to_profile(request):
    username = request.urlvars.get('username')
    profile_url = '{0}/u/{1}/'.format(conf['sso_url'], username)
    return wsgihelpers.redirect(contexts.Ctx(request), location=profile_url)


@wsgihelpers.wsgify
def redirect_to_account(request):
    context = contexts.Ctx(request)
    user = auth.get_user_from_request(request)
    username = request.urlvars.get('username')

    if not user or not username == user.name:
        return wsgihelpers.unauthorized(context)

    account_url = '{0}/my/profile/'.format(conf['sso_url'])
    return wsgihelpers.redirect(context, location=account_url)


@wsgihelpers.wsgify
def forbidden(request):
    return wsgihelpers.forbidden(contexts.Ctx(request))


def make_router(app):
    """Return a WSGI application that searches requests to controllers """
    global router
    router = urls.make_router(app,
        ('GET', r'^(/(?P<lang>\w{2}))?/?$', home),
        ('GET', r'^(/(?P<lang>\w{2}))?/search/?$', display_search_results),
        ('GET', r'^(/(?P<lang>\w{2}))?/metrics/?$', metrics),

        ('GET', r'^(/(?P<lang>\w{2}))?/dataset/?$', search_more_datasets),

        ('GET', r'^(/(?P<lang>\w{2}))?/dataset/autocomplete/?$', autocomplete_datasets),
        ('GET', r'^(/(?P<lang>\w{2}))?/dataset/(?P<name>[\w_-]+)/fork/?$', fork_dataset),
        ('GET', r'^(/(?P<lang>\w{2}))?/dataset/(?P<name>[\w_-]+)/reuse/(?P<reuse>[\w_-]+)/featured/?$', toggle_featured),
        ('GET', r'^(/(?P<lang>\w{{2}}))?/dataset/(?!{0}(/|$))(?P<name>[\w_-]+)/?$'.format('|'.join(EXCLUDED_PATTERNS)), display_dataset),

        (('GET', 'POST'), r'^(/(?P<lang>\w{2}))?/dataset/(?P<name>[\w_-]+)/related/new?$', create_reuse),
        (('GET', 'POST'), r'^(/(?P<lang>\w{2}))?/dataset/(?P<name>[\w_-]+)/related/edit/(?P<reuse>[\w_-]+)/?$', edit_reuse),


        (('GET', 'POST'), r'^(/(?P<lang>\w{2}))?/dataset/(?P<name>[\w_-]+)/community/resource/new/?$', create_community_resource),
        (('GET', 'POST'), r'^(/(?P<lang>\w{2}))?/dataset/(?P<name>[\w_-]+)/community/resource/(?P<resource>[\w_-]+)/edit/?$', edit_community_resource),
        ('POST', r'^(/(?P<lang>\w{2}))?/dataset/(?P<name>[\w_-]+)/community/resource/(?P<resource>[\w_-]+)/delete/?$', delete_community_resource),

        ('GET', r'^(/(?P<lang>\w{2}))?/organizations?/?$', search_more_organizations),
        ('GET', r'^(/(?P<lang>\w{2}))?/organizations?/autocomplete/?$', autocomplete_organizations),
        (('GET', 'POST'), r'^(/(?P<lang>\w{2}))?/organization/new/?$', create_organization),
        ('GET', r'^(/(?P<lang>\w{{2}}))?/organization/(?!{0}(/|$))(?P<name>[\w_-]+)/?$'.format('|'.join(EXCLUDED_PATTERNS)), display_organization),

        (('GET', 'POST'), r'^(/(?P<lang>\w{2}))?/group/new/?$', create_group),
        ('GET', r'^(/(?P<lang>\w{{2}}))?/groups?/(?!{0}(/|$))(?P<name>[\w_-]+)/?$'.format('|'.join(EXCLUDED_PATTERNS)), display_group),

        ('GET', r'^(/(?P<lang>\w{2}))?/unfeature/(?P<reuse>[\w_-]+)/?$', unfeature_reuse),

        ('GET', r'^(/(?P<lang>\w{2}))?/format/autocomplete/?$', autocomplete_formats),

        # Override some CKAN URLs
        ('GET', r'^(/(?P<lang>\w{2}))?/user/_?logout/?$', redirect_to_logout),
        ('GET', r'^(/(?P<lang>\w{2}))?/user/register/?$', redirect_to_login),
        ('GET', r'^(/(?P<lang>\w{2}))?/user/login/?$', redirect_to_login),
        ('GET', r'^(/(?P<lang>\w{2}))?/register/?$', redirect_to_login),
        ('GET', r'^(/(?P<lang>\w{2}))?/login/?$', redirect_to_login),
        ('GET', r'^(/(?P<lang>\w{2}))?/user/(?P<username>[\w_-]+)/?$', redirect_to_profile),
        ('GET', r'^(/(?P<lang>\w{2}))?/user/edit/(?P<username>[\w_-]+)/?$', redirect_to_account),
        ('GET', r'^(/(?P<lang>\w{2}))?/users/?$', forbidden),
        ('GET', r'^(/(?P<lang>\w{2}))?/about/?$', redirect_to_home),
    )

    return router
