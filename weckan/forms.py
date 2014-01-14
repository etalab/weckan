# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import cgi
import re

from datetime import datetime

from wtforms import Form as WTForm, Field, validators, fields, widgets
from wtforms.fields import html5

from weckan import model, urls, conf

_ = lambda s: s

STORAGE_BUCKET = 'default'

RE_TAG = re.compile('^[\w \-.]*$', re.U)


def handle_upload(request, field, user=None):
    from ckan.controllers import storage

    if not isinstance(field.data, cgi.FieldStorage):
        return None

    filename = '{ts:%Y-%m-%dT%H-%M-%S}/{name}'.format(name=field.data.filename, ts=datetime.now())
    ofs = storage.get_ofs()
    ofs.put_stream(STORAGE_BUCKET, filename, field.data.file, {
        'filename-original': field.data.filename,
        'uploaded-by': user.name if user else '',
    })
    root = conf['home_url'].replace('//', 'https://' if conf['https'] else 'http://', 1)
    path = urls.get_url(None, 'storage/f', filename)
    return ''.join([root, path])


class Form(WTForm):
    def __init__(self, *args, **kwargs):
        self.i18n = kwargs.pop('i18n', None)
        super(Form, self).__init__(*args, **kwargs)

    def _get_translations(self):
        return self.i18n


class FieldHelper(object):
    @property
    def id(self):
        return '{0}-id'.format(self.name)

    @id.setter
    def id(self, value):
        pass

    def is_visible(self, user):
        return True

    def __call__(self, **kwargs):
        placeholder = kwargs.pop('placeholder', self._translations.ugettext(self.label.text))
        if placeholder:
            kwargs['placeholder'] = placeholder
        required = kwargs.pop('required', self.flags.required)
        if required is True:
            kwargs['required'] = required
        return super(FieldHelper, self).__call__(**kwargs)

    def ugettext(self, string):
        return self._translations.ugettext(string)

    _ = ugettext


class RequiredIf(validators.DataRequired):
    '''
    A validator which makes a field required
    only if another field is set and has a truthy value.
    '''
    def __init__(self, other_field_name, *args, **kwargs):
        self.other_field_name = other_field_name
        super(RequiredIf, self).__init__(*args, **kwargs)

    def __call__(self, form, field):
        other_field = form._fields.get(self.other_field_name)
        if other_field is None:
            raise Exception('no field named "%s" in form' % self.other_field_name)
        if bool(other_field.data):
            super(RequiredIf, self).__call__(form, field)


class Requires(object):
    '''
    A validator which makes a field required another field.
    '''
    def __init__(self, other_field_name, *args, **kwargs):
        self.other_field_name = other_field_name
        super(Requires, self).__init__(*args, **kwargs)

    def __call__(self, form, field):
        if not field.data:
            return
        other_field = form._fields.get(self.other_field_name)
        if other_field is None:
            raise Exception('no field named "%s" in form' % self.other_field_name)
        if not bool(other_field.data):
            msg = field._('This field requires "%(name)s" to be set')
            raise validators.ValidationError(msg % {'name': field._(other_field.label.text)})


class RequiredIfVal(validators.DataRequired):
    '''
    A validator which makes a field required
    only if another field is set and has a specified value.
    '''
    def __init__(self, other_field_name, expected_value, *args, **kwargs):
        self.other_field_name = other_field_name
        self.expected_values = expected_value if isinstance(expected_value, (list, tuple)) else tuple(expected_value)
        super(RequiredIfVal, self).__init__(*args, **kwargs)

    def __call__(self, form, field):
        other_field = form._fields.get(self.other_field_name)
        if other_field is None:
            raise Exception('no field named "%s" in form' % self.other_field_name)
        if other_field.data in self.expected_values:
            super(RequiredIfVal, self).__call__(form, field)


class WidgetHelper(object):
    classes = []
    attributes = {}

    def __call__(self, field, **kwargs):
        # Handle extra classes
        classes = (kwargs.pop('class', '') or kwargs.pop('class_', '')).split()
        extra_classes = self.classes if isinstance(self.classes, (list, tuple)) else [self.classes]
        classes.extend([cls for cls in extra_classes if cls not in classes])
        kwargs['class'] = ' '.join(classes)

        # Handle defaults
        for key, value in self.attributes.items():
            kwargs.setdefault(key, value)

        return super(WidgetHelper, self).__call__(field, **kwargs)


class SelectPicker(WidgetHelper, widgets.Select):
    classes = 'selectpicker'


class MarkdownEditor(WidgetHelper, widgets.TextArea):
    classes = 'md'
    attributes = {'rows': 8}


class FormatAutocompleter(WidgetHelper, widgets.TextInput):
    classes = 'format-completer'


class TerritoryAutocompleter(WidgetHelper, widgets.TextInput):
    classes = 'territory-completer'


class TagAutocompleter(WidgetHelper, widgets.TextInput):
    classes = 'tag-completer'
    attributes = {
        'data-tag-minlength': model.MIN_TAG_LENGTH,
        'data-tag-maxlength': model.MAX_TAG_LENGTH,
    }


class TopicAutocompleter(WidgetHelper, widgets.TextInput):
    classes = 'topic-completer'


class KeyValueWidget(WidgetHelper, widgets.TextInput):
    pass


class StringField(FieldHelper, fields.StringField):
    pass


class BooleanField(FieldHelper, fields.BooleanField):
    def __init__(self, *args, **kwargs):
        self.stacked = kwargs.pop('stacked', False)
        super(BooleanField, self).__init__(*args, **kwargs)


class RadioField(FieldHelper, fields.RadioField):
    def __init__(self, *args, **kwargs):
        self.stacked = kwargs.pop('stacked', False)
        super(RadioField, self).__init__(*args, **kwargs)


class FileField(FieldHelper, fields.FileField):
    pass


class URLField(FieldHelper, html5.URLField):
    pass


def nullable_text(value):
    return None if value == 'None' else fields.core.text_type(value)


class SelectField(FieldHelper, fields.SelectField):
    widget = SelectPicker()

    def __init__(self, label=None, validators=None, coerce=nullable_text, **kwargs):
        super(SelectField, self).__init__(label, validators, coerce, **kwargs)

    def iter_choices(self):
        localized_choices = [
            (value, self._(label) if label else '', selected)
            for value, label, selected in super(SelectField, self).iter_choices()
        ]
        for value, label, selected in sorted(localized_choices, key=lambda c: c[1]):
            yield (value, label, selected)


class SelectMultipleField(FieldHelper, fields.SelectMultipleField):
    widget = SelectPicker(multiple=True)

    def iter_choices(self):
        localized_choices = [
            (value, self._(label) if label else '', selected)
            for value, label, selected in super(SelectMultipleField, self).iter_choices()
        ]
        for value, label, selected in sorted(localized_choices, key=lambda c: c[1]):
            yield (value, label, selected)


class TagField(StringField):
    widget = TagAutocompleter()

    def _value(self):
        if self.data:
            return u','.join(self.data)
        else:
            return u''

    def process_formdata(self, valuelist):
        if valuelist:
            self.data = list(set([x.strip().lower() for x in valuelist[0].split(',')]))
        else:
            self.data = []

    def pre_validate(self, form):
        if not self.data:
            pass
        for tag in self.data:
            if not model.MIN_TAG_LENGTH <= len(tag) <= model.MAX_TAG_LENGTH:
                message = self._('Tag "%(tag)s" must be between %(min)d and %(max)d characters long.')
                params = {'min': model.MIN_TAG_LENGTH, 'max': model.MAX_TAG_LENGTH, 'tag': tag}
                raise validators.ValidationError(message % params)
            if not RE_TAG.match(tag):
                message = self._('Tag "%s" must be alphanumeric characters or symbols: -_.')
                raise validators.ValidationError(message % tag)


class TerritoryField(TagField):
    widget = TerritoryAutocompleter()

    def pre_validate(self, form):
        pass


class MarkdownField(FieldHelper, fields.TextAreaField):
    widget = MarkdownEditor()


class PublishAsField(FieldHelper, Field):
    def is_visible(self, user):
        return len(user.organizations) > 0

    def process_data(self, value):
        self.data = value.id if isinstance(value, model.Group) else value

    def populate_obj(self, obj, name):
        fkey = '{0}_id'.format(name)
        if hasattr(obj, fkey):
            setattr(obj, fkey, self.data or None)
        else:
            setattr(obj, name, self.data)


class KeyValueForm(WTForm):
    key = StringField(_('Key'), [RequiredIf('value')])
    value = StringField(_('Value'))


class KeyValueField(FieldHelper, fields.FieldList):
    # widget = KeyValueWidget()
    def __init__(self, *args, **kwargs):
        kwargs['min_entries'] = kwargs.pop('min_entries', 1)
        super(KeyValueField, self).__init__(fields.FormField(KeyValueForm), *args, **kwargs)

    def process_data(self, values):
        print 'process_data', values
        return super(KeyValueField, self).process_data(values)

    def process(self, formdata, data=object()):
        print 'process', formdata, data
        return super(KeyValueField, self).process(formdata, data)

    @property
    def data(self):
        for f in self.entries:
            print f
        return [f.data for f in self.entries]

    # def process_data(self, values):
    #     if isinstance(values, dict):
    #         self.data = [(key, value) for key, value in values.items()]
    #     else:
    #         self.data = values

    # def _value(self):
    #     return self.data
        # if self.data:
        #     return u', '.join(self.data)
        # else:
        #     return u''
