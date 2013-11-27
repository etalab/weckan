# -*- coding: utf-8 -*-
from __future__ import unicode_literals

_ = lambda s: s


class Field(object):
    def __init__(self, name, label, type='text', required=False, initial=None, help_text=None, **kwargs):
        self.name = name
        self.label = label
        self.type = type
        self.required = required
        self.initial = initial
        self.help_text = help_text

    def feed(self, data, initial=None):
        initial = initial.get(self.name, self.initial) if initial else None
        self.data = data.get(self.name, initial) if data else initial

    def validate(self):
        self.errors = []
        if self.required and not self.data:
            self.errors.append(_('Field {label} is required'))
        return not self.errors

    def is_visible(self, user):
        return True


class SelectField(Field):
    def __init__(self, name, label, options, **kwargs):
        super(SelectField, self).__init__(name, label, type='select', **kwargs)
        self.options = options


class PublishAsField(Field):
    def __init__(self, name, label, **kwargs):
        super(PublishAsField, self).__init__(name, label, type='publish_as', **kwargs)

    def is_visible(self, user):
        return len(user.organizations) > 0


class Form(object):
    '''Base form helper'''
    fields = []

    def __init__(self, data=None, initial=None):
        self.data = data
        for field in self.fields:
            field.feed(data, initial)

    def validate(self):
        return all([field.validate() for field in self.fields])


class ReuseForm(Form):
    fields = (
        Field('title', _('Title'), required=True),
        Field('url', _('URL'), type='url', required=True),
        Field('image_url', _('Image URL'), type='url', required=True),
        SelectField('type', _('Type'), required=True, options=(
            ('api', _('API')),
            ('application', _('Application')),
            ('idea', _('Idea')),
            ('news_article', _('News Article')),
            ('paper', _('Paper')),
            ('post', _('Post')),
            ('visualization', _('Visualization')),
        )),
        Field('description', _('Description'), type='markdown', required=True),
        PublishAsField('publish_as', _('Publish as')),
    )
