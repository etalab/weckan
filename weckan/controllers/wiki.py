# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
import requests

from weckan import conf


log = logging.getLogger(__name__)

SEARCH_MAX_TOPICS = 2

SEARCH_TIMEOUT = 2


def search(query):
    '''Perform a topic search given a ``query``'''
    params = {
        'format': 'json',
        'action': 'query',
        'list': 'search',
        'srsearch': query,
        'srprop': 'timestamp',
        'srlimit': SEARCH_MAX_TOPICS,
    }
    try:
        response = requests.get(conf['wiki_api_url'], params=params, timeout=SEARCH_TIMEOUT)
        response.raise_for_status()
    except requests.RequestException:
        log.exception('Unable to fetch topics')
        return 'topics', {'results': [], 'more': False}
    json_response = response.json()
    return 'topics', {
        'results': json_response.get('query', {}).get('search', []),
        'more': 'query-continue' in json_response,
    }
