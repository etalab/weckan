# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
import requests

from biryani1 import strings

from weckan import conf


log = logging.getLogger(__name__)

TIMEOUT = 3


def fetch(kind, code):
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


def get_cookie(request):
    if request.cookies.get('territory-infos', '').count('|') == 1:
        territory_key, _ = request.cookies.get('territory-infos').split('|')
        territory = fetch(*territory_key.split('/')) if territory_key else {}
    else:
        territory = {}

    return {
        'full_name': territory.get('full_name', ''),
        'full_name_slug': strings.slugify(territory.get('full_name', '')),
        'depcom': territory.get('code', '')
    }
