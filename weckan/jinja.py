# -*- coding: utf-8 -*-
from pkg_resources import resource_stream

from jinja2 import Environment, PackageLoader
from webassets import Environment as AssetsEnvironment
from webassets.ext.jinja2 import AssetsExtension
from webassets.loaders import YAMLLoader

# Configure webassets from yaml file
loader = YAMLLoader(resource_stream(__name__, 'assets.yaml'))
assets = loader.load_environment()

# Configure Jinja Environment with webassets
env = Environment(loader=PackageLoader('weckan', 'templates'), extensions=[AssetsExtension])
env.assets_environment = assets
