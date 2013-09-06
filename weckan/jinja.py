# -*- coding: utf-8 -*-
import urllib

from pkg_resources import resource_stream

from jinja2 import Environment, PackageLoader
from webassets import Environment as AssetsEnvironment
from webassets.ext.jinja2 import AssetsExtension
from webassets.loaders import YAMLLoader

from biryani1 import strings

from ckan.lib.helpers import markdown, markdown_extract

from babel import dates

from . import conf
from . import urls

# Langugages definitions: language code => (Display name, flag)
LANGUAGES = {
    'fr': (u'Français', 'fr'),
    'en': (u'English', 'us'),
}
DEFAULT_LANG = 'fr'

GRAVATAR_DEFAULTS = ('404', 'mm', 'identicon', 'monsterid', 'wavatar', 'retro')


def url(*args, **kwargs):
    return urls.get_url(None, *args, **kwargs)


def static(*args, **kwargs):
    return url(*args, **kwargs)


def format_datetime(value, format='short', locale='fr'):
    try:
        return dates.format_datetime(value, format, locale=locale)
    except:
        return value


def format_date(value, format='short', locale='fr'):
    try:
        return dates.format_date(value, format, locale=locale)
    except:
        return value


def gravatar(email_hash, size=100, default=None):
    if default is None:
        default = conf.get('ckan.gravatar_default', 'identicon')

    if not default in GRAVATAR_DEFAULTS:
        # treat the default as a url
        default = urllib.quote(default, safe='')

    return (
        '<img src="//gravatar.com/avatar/{hash}?s={size}&amp;d={default}"'
        'class="gravatar" width="{size}" height="{size}" />'
        ).format(hash=email_hash, size=size, default=default)


# Configure webassets
assets_environment = AssetsEnvironment(conf['static_files_dir'], '/')
assets_environment.debug = conf['debug']
assets_environment.auto_build = True # conf['debug']

# Load bundle from yaml file
loader = YAMLLoader(resource_stream(__name__, 'assets.yaml'))
bundles = loader.load_bundles()
for name, bundle in bundles.items():
    assets_environment.register(name, bundle)

# Configure Jinja Environment with webassets
env = Environment(
    loader = PackageLoader('weckan', 'templates'),
    extensions = (AssetsExtension, 'jinja2.ext.i18n')
    )
env.assets_environment = assets_environment

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


def render_template(context, name, **kwargs):
    '''Render a localized template using Jinja'''
    env.install_gettext_translations(context.translator)
    template = env.get_template(name)
    lang = kwargs.pop('lang', DEFAULT_LANG)
    return template.render(lang=lang, flag=LANGUAGES[lang][1], languages=LANGUAGES, **kwargs)
