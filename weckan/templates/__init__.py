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
from __future__ import unicode_literals

import urllib
import json

from os.path import join, dirname, abspath
from pkg_resources import resource_stream

from jinja2 import Environment, PackageLoader
from webassets import Environment as AssetsEnvironment
from webassets.ext.jinja2 import AssetsExtension
from webassets.loaders import YAMLLoader

from babel import dates

from .. import conf, contexts, auth

env = None

# Langugages definitions: language code => (Display name, flag)
LANGUAGES = {
    'fr': u'Français',
    'en': u'English',
    'de': u'Deutsch',
}
DEFAULT_LANG = 'fr'

DEFAULT_STATIC = abspath(join(dirname(__file__), '..', 'static'))

GRAVATAR_DEFAULTS = ('404', 'mm', 'identicon', 'monsterid', 'wavatar', 'retro')

GROUPS = (
    (u'Culture et communication', 'culture', None),
    (u'Développement durable', 'wind', '{wiki}/Le_D%C3%A9veloppement_Durable'),
    (u'Éducation et recherche', 'education', None),
    (u'Justice', 'justice', None),
    (u'Santé et solidarité', 'heart', None),
    (u'Sécurité et défense', 'shield', None),
    (u'Société', 'people', None),
    (u'Travail, économie, emploi', 'case', None),
)

MAIN_TOPICS = None


def format_group_url(row):
    url = row[2].format(
        home=conf['home_url'], wiki=conf['wiki_url'], questions=conf['questions_url']
    ) if row[2] else None
    return (row[0], row[1], url)


def url(*args, **kwargs):
    '''Get an URL from parts'''
    from .. import urls
    return urls.get_url(None, *args, **kwargs)


def static(*args, **kwargs):
    '''Get a static asset path'''
    return url(*args, **kwargs)


def format_datetime(value, format='short', locale='fr'):
    '''Format a datetime given a locale'''
    try:
        return dates.format_datetime(value, format, locale=locale)
    except:
        return value


def format_date(value, format='display', locale='fr'):
    '''Format a date given a locale'''
    if format == 'display':
        _ = contexts.Ctx().translator.gettext
        # TRANSLATORS: Short date format with full year (4-digits)
        format = _('MM-dd-yyyy')
    try:
        return dates.format_date(value, format, locale=locale)
    except:
        return value


def gravatar(email_hash, size=100, default=None):
    '''Display a gravatar from an email'''
    if default is None:
        default = conf.get('ckan.gravatar_default', 'identicon')

    if not default in GRAVATAR_DEFAULTS:
        # treat the default as a url
        default = urllib.quote(default, safe='')

    return (
        '<img src="//gravatar.com/avatar/{hash}?s={size}&amp;d={default}"'
        'class="gravatar" width="{size}" height="{size}" />'
        ).format(hash=email_hash, size=size, default=default)


def swig(value):
    '''Transform a string into a swig variable'''
    return ''.join(['{{', value, '}}'])


def user_by_id(user_id):
    '''Get a user from its id'''
    from weckan.model import User
    return User.get(user_id)


def tooltip_ellipsis(source, length=0):
    ''' return the plain text representation of markdown encoded text.  That
    is the texted without any html tags.  If ``length`` is 0 then it
    will not be truncated.'''
    try:
        length = int(length)
    except ValueError:  # invalid literal for int()
        return source  # Fail silently.
    ellipsis = '<a href rel="tooltip" data-container="body" title="{0}">...</a>'.format(source)
    return (source[:length] + ellipsis) if len(source) > length and length > 0 else source


def get_webassets_env(conf):
    '''Get a preconfigured WebAssets environment'''
    # Configure webassets
    assets_environment = AssetsEnvironment(conf.get('static_files_dir', DEFAULT_STATIC), '/')
    assets_environment.debug = conf.get('debug', False)
    assets_environment.auto_build = conf.get('debug', False)
    assets_environment.config['less_paths'] = ('bower/bootstrap/less', 'bower/etalab-assets/less')

    # Load bundle from yaml file
    loader = YAMLLoader(resource_stream(__name__, '../assets.yaml'))
    bundles = loader.load_bundles()
    for name, bundle in bundles.items():
        assets_environment.register(name, bundle)

    return assets_environment


def get_jinja_env():
    '''
    Get a preconfigured jinja environment including:

     - WebAssets
     - i18n
     - global functions
     - filters
    '''
    global env

    if not env:
        from biryani1 import strings
        from ckan.lib.helpers import markdown, markdown_extract
        from weckan.urls import sso_url

        # Configure Jinja Environment with webassets
        env = Environment(
            loader = PackageLoader('weckan', 'templates'),
            extensions = (AssetsExtension, 'jinja2.ext.i18n')
            )
        env.assets_environment = get_webassets_env(conf)

        # Custom global functions
        env.globals['url'] = url
        env.globals['sso'] = sso_url
        env.globals['static'] = static
        env.globals['slugify'] = strings.slugify
        env.globals['ifelse'] = lambda condition, first, second: first if condition else second
        env.globals['gravatar'] = gravatar
        env.globals['markdown'] = markdown
        env.globals['markdown_extract'] = markdown_extract
        env.globals['user_by_id'] = user_by_id

        # Custom filters
        env.filters['datetime'] = format_datetime
        env.filters['date'] = format_date
        env.filters['swig'] = swig
        env.filters['tooltip_ellipsis'] = tooltip_ellipsis

    return env


def format_topic(topic):
    url = topic['url'].format(
        group='{0}/{{lang}}/groups'.format(conf['home_url']),
        wiki=conf['wiki_url']
    )
    return {'title': topic['title'], 'url': url}


def main_topics():
    global MAIN_TOPICS
    if not MAIN_TOPICS:
        static_root = conf.get('static_files_dir', DEFAULT_STATIC)
        topics_file = join(static_root, 'bower', 'etalab-assets', 'data', 'main_topics.json')
        with open(topics_file) as f:
            MAIN_TOPICS = map(format_topic, json.load(f))
    return MAIN_TOPICS


def render(context, name, **kwargs):
    '''Render a localized template using Jinja'''
    env = get_jinja_env()
    env.install_gettext_translations(context.translator)
    template = env.get_template(name)
    lang = kwargs.pop('lang', DEFAULT_LANG)
    return template.render(lang=lang, languages=LANGUAGES, **kwargs)


def render_site(name, request_or_context, **kwargs):
    '''
    Render a template with a common site behavior.

    - handle language choice and fallback
    - inject user
    - inject sidebar items
    '''
    context = request_or_context if isinstance(request_or_context, contexts.Ctx) else contexts.Ctx(request_or_context)
    lang = context.req.urlvars.get('lang', None)

    # Locale-less location
    current_location = context.req.path_qs
    base_location = current_location.replace('/{0}'.format(lang), '')

    # Override browser language
    if lang in LANGUAGES:
        context.lang = lang
    elif lang is None:
        lang = DEFAULT_LANG
    else:
        from weckan import wsgihelpers
        return wsgihelpers.redirect(context, location=base_location)

    return render(context, name,
        full_url = context.req.url,
        current_location = current_location,
        current_base_location = base_location,
        query_string = context.req.query_string,
        user = auth.get_user_from_request(context.req),
        lang = lang,
        main_topics = main_topics(),
        DOMAIN = conf['domain'],
        HOME_URL = conf['home_url'],
        WIKI_URL = conf['wiki_url'],
        WIKI_API_URL = conf['wiki_api_url'],
        QUESTIONS_URL = conf['questions_url'],
        CKAN_URL = conf['ckan_url'],
        COW_URL = conf['cow_url'],
        SSO_URL = conf['sso_url'],
        **kwargs
    )
