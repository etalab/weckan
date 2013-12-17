# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
import logging

import requests

from weckan import conf

log = logging.getLogger(__name__)


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
        try:
            msg = response.json()['error']
        except:
            msg = 'No message'
        log.exception('Error on CKAN API for action %s: %s', action, msg)
        raise
    return response.json()
