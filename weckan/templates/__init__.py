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
import os
import urllib

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
    'fr': (u'Français', 'fr'),
    'en': (u'English', 'us'),
}
DEFAULT_LANG = 'fr'

GRAVATAR_DEFAULTS = ('404', 'mm', 'identicon', 'monsterid', 'wavatar', 'retro')

GROUPS = (
    (u'Culture et communication', 'culture', None),
    (u'Développement durable', 'wind', '{wiki}/Le_D%C3%A9veloppement_Durable'),
    (u'Éducation et recherche', 'education', None),
    (u'État et collectivités', 'france', None),
    (u'Europe', 'europe', None),
    (u'Justice', 'justice', None),
    (u'Monde', 'world', None),
    (u'Santé et solidarité', 'hearth', None),
    (u'Sécurité et défense', 'shield', None),
    (u'Société', 'people', None),
    (u'Travail, économie, emploi', 'case', None),
)


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


def format_date(value, format='short', locale='fr'):
    '''Format a date given a locale'''
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


def get_webassets_env(conf):
    '''Get a preconfigured WebAssets environment'''
    # Configure webassets
    default_static = abspath(join(dirname(__file__), '..', 'static'))
    assets_environment = AssetsEnvironment(conf.get('static_files_dir', default_static), '/')
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

        # Configure Jinja Environment with webassets
        env = Environment(
            loader = PackageLoader('weckan', 'templates'),
            extensions = (AssetsExtension, 'jinja2.ext.i18n')
            )
        env.assets_environment = get_webassets_env(conf)

        # Custom global functions
        env.globals['url'] = url
        env.globals['static'] = static
        env.globals['slugify'] = strings.slugify
        env.globals['ifelse'] = lambda condition, first, second: first if condition else second
        env.globals['gravatar'] = gravatar
        env.globals['markdown'] = markdown
        env.globals['markdown_extract'] = markdown_extract

        # Custom filters
        env.filters['datetime'] = format_datetime
        env.filters['date'] = format_date

    return env


def render(context, name, **kwargs):
    '''Render a localized template using Jinja'''
    env = get_jinja_env()
    env.install_gettext_translations(context.translator)
    template = env.get_template(name)
    lang = kwargs.pop('lang', DEFAULT_LANG)
    return template.render(lang=lang, flag=LANGUAGES[lang][1], languages=LANGUAGES, **kwargs)


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
    current_location = context.req.uscript_name
    base_location = current_location.replace('/{0}'.format(lang), '')

    # Override browser language
    if lang in LANGUAGES:
        context.lang = lang
    elif lang is None:
        lang = DEFAULT_LANG
    else:
        return wsgihelpers.redirect(context, location=base_location)

    return render(context, name,
        current_location = current_location,
        current_base_location = base_location,
        user = auth.get_user_from_request(context.req),
        lang = lang,
        sidebar_groups = map(format_group_url, GROUPS),
        HOME_URL = conf['home_url'],
        WIKI_URL = conf['wiki_url'],
        QUESTIONS_URL = conf['questions_url'],
        **kwargs
    )
