# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import pkg_resources

from os.path import dirname

from babel.support import Translations

LANGUAGES = ['fr-FR', 'fr', 'en-US', 'en', 'de']

EXTRA_TRANSLATIONS = [
    (name, pkg_resources.resource_filename(name, 'i18n'))
    for name in ('biryani1', 'ckan')
]


def new_translator(languages=None):
    lang = languages or LANGUAGES
    translations = Translations.load(dirname(__file__), lang, 'weckan')

    if not isinstance(translations, Translations):
        return translations

    for name, path in EXTRA_TRANSLATIONS:
        translations.merge(Translations.load(path, lang, name))

    return translations

translation = new_translator()
