# -*- coding: utf-8 -*-
import logging
import shutil

from glob import iglob
from os import makedirs
from os.path import dirname, join, exists, isdir

from setuptools import Command
from webassets.script import CommandLineEnvironment
from weckan.templates import get_webassets_env

STATIC = join(dirname(__file__), 'static')

TO_COPY = {
    'bower/bootstrap/dist/fonts/*': 'fonts/',
    'bower/etalab-assets/fonts/*': 'fonts/',
    'bower/etalab-assets/img/*': 'img/',
    'bower/etalab-assets/img/flags/*': 'img/flags/',
}

log = logging.getLogger('webassets')
log.addHandler(logging.StreamHandler())
log.setLevel(logging.DEBUG)


class BuildAssets(Command):
    '''Build assets for production deployment'''

    description = "Precompile assets for webassets"
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        assets_env = get_webassets_env({
            'debug': False,
            'static_files_dir': STATIC,
        })

        cmdenv = CommandLineEnvironment(assets_env, log)
        cmdenv.build()

        self.copy_assets()

    def copy_assets(self):
        '''Copy static assets unhandled by WebAssets'''
        for source, destination in TO_COPY.items():
            log.info('Copying %s to %s', source, destination)
            destination_path = join(STATIC, destination)
            if not exists(destination_path):
                makedirs(destination_path)
            for filename in iglob(join(STATIC, source)):
                if isdir(filename):
                    continue
                shutil.copy(filename, destination_path)
