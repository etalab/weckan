# -*- coding: utf-8 -*-
from pkg_resources import resource_stream

from jinja2 import Environment, PackageLoader
from webassets import Environment as AssetsEnvironment
from webassets.ext.jinja2 import AssetsExtension
from webassets.loaders import YAMLLoader

from biryani1 import strings

from . import conf
from . import urls


def url(*args, **kwargs):
    return urls.get_url(None, *args, **kwargs)


def format_datetime(value, format='%Y-%m-%d'):
    return value.strftime(format)


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
env = Environment(loader=PackageLoader('weckan', 'templates'), extensions=[AssetsExtension])
env.assets_environment = assets_environment

# Custom global functions
env.globals['url'] = url
env.globals['slugify'] = strings.slugify
env.globals['ifelse'] = lambda condition, first, second: first if condition else second

# Custom filters
env.filters['datetime'] = format_datetime
