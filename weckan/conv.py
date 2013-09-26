# -*- coding: utf-8 -*-


# Weckan -- Web application using CKAN model
# By: Emmanuel Raviart <emmanuel@raviart.com>
#
# Copyright (C) 2013 Etalab
# http://github.com/etalab/weckan
#
# This file is part of Weckan.
#
# Weckan is free software; you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# Weckan is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


"""Conversion functions"""


import re
import urlparse

from biryani1.baseconv import *
from biryani1.base64conv import *
#from biryani1.datetimeconv import *
from biryani1.jsonconv import *
from biryani1.objectconv import *
from biryani1.states import default_state, State


encoding_declaration_re = re.compile('[=:]\s*([-\w.]+)')


# Level-1 converters


def attribute(attribute_name):
    return function(lambda value: getattr(value, attribute_name))


def is_local_url(value, state = None):
    from . import urls
    if value is None:
        return value, None
    if state is None:
        state = default_state
    split_url = urlparse.urlsplit(value)
    if split_url.netloc and not any(
            value.startswith(full_url)
            for full_url in urls.iter_full_urls(state)
            ):
        return value, state._(u'External URL')
    return value, None


input_to_token = cleanup_line


def method(method_name, *args, **kwargs):
    def method_converter(value, state = None):
        if value is None:
            return value, None
        return getattr(value, method_name)(state or default_state, *args, **kwargs)
    return method_converter


def str_to_python_source_code(value, state = None):
    if value is None:
        return value, None
    # If a comment in the first or second line of the Python script matches the regular expression coding
    # [=:]\s*([-\w.]+), this comment is handled as an encoding declaration and removed.
    lines = value.split(u'\n', 2)
    for i, line in enumerate(lines[:2]):
        if line.lstrip().startswith(u'#') and encoding_declaration_re.search(line) is not None:
            del lines[i]
            value = u'\n'.join(lines)
            break
    return value, None


def url_to_local_url(value, state = None):
    if value is None:
        return value, None
    split_url = list(urlparse.urlsplit(value))
    split_url[0:2] = [u'', u'']
    path = split_url[2]
    if path.startswith(u'/'):
        split_url[2] = path.rstrip(u'/') or u'/'
    else:
        split_url[2] = path.rstrip(u'/')
    return urlparse.urlunsplit(split_url), None


# Level-2 converters


decode_form_stop_voucher = pipe(
    make_base64url_to_bytes(add_padding = True),
    # TODO: Decipher
    make_input_to_json(),
    test_isinstance(dict),
    struct(dict(
        cancel = pipe(
            guess_bool,
            default(False),
            ),
        token = noop,
        )),
    )


encode_form_stop_token = pipe(
    make_json_to_str(encoding = 'utf-8', ensure_ascii = False, separators = (',', ':'), sort_keys = True),
    # TODO: Cipher string.
    make_bytes_to_base64url(remove_padding = True),
    )


input_to_python_source_code = pipe(
    cleanup_text,
    str_to_python_source_code,
    )
