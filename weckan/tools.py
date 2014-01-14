# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
import logging

import requests

from weckan import conf

log = logging.getLogger(__name__)


class CkanApiError(ValueError):
    '''Error occuring while calling CKAN API'''


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
    except requests.RequestException as e:
        message = e.message
        try:
            error = response.json()['error']
            message += ' ({0})'.format(error)
        except:
            pass
        raise CkanApiError('Error for action "{0}": {1}'.format(action, message))
    return response.json()


def parse_page(request):
    try:
        page = int(request.params.get('page', 1))
    except:
        page = 1
    return max(page, 1)
