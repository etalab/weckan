# -*- coding: utf-8 -*-
import logging

from os.path import dirname, join

from setuptools import Command
from webassets.script import CommandLineEnvironment
from weckan.templates import get_webassets_env


class BuildAssets(Command):
    '''Build assets for production deployment'''

    description = "Precompile assets for webassets"
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        log = logging.getLogger('webassets')
        log.addHandler(logging.StreamHandler())
        log.setLevel(logging.DEBUG)

        assets_env = get_webassets_env({
            'debug': False,
            'static_files_dir': join(dirname(__file__), 'static'),
        })

        cmdenv = CommandLineEnvironment(assets_env, log)
        cmdenv.build()
