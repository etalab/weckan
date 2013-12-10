# -*- coding: utf-8 -*-
from __future__ import unicode_literals

_ = lambda s: s

from wtforms import Form as WTForm, Field, validators, fields, widgets
from wtforms.fields import html5


class Form(WTForm):
    def __init__(self, *args, **kwargs):
        self.i18n = kwargs.pop('i18n', None)
        super(Form, self).__init__(*args, **kwargs)

    def _get_translations(self):
        return self.i18n


class FieldHelper(object):
    def __init__(self, *args, **kwargs):
        id = kwargs.pop('id', None)
        if not id and '_name' in kwargs:
            id = '{_name}_id'.format(**kwargs)
        super(FieldHelper, self).__init__(*args, id=id, **kwargs)

    def is_visible(self, user):
        return True


class SelectPicker(widgets.Select):
    def __call__(self, field, **kwargs):
        classes = (kwargs.pop('class', '') or kwargs.pop('class_', '')).split()
        if not 'selectpicker' in classes:
            classes.append('selectpicker')
        kwargs['class'] = ' '.join(classes)
        return super(SelectPicker, self).__call__(field, **kwargs)


class MarkdownEditor(widgets.TextArea):
    def __call__(self, field, **kwargs):
        classes = (kwargs.pop('class', '') or kwargs.pop('class_', '')).split(' ')
        if not 'md' in classes:
            classes.append('md')
        kwargs['class'] = ' '.join(classes)
        kwargs.setdefault('rows', 8)
        return super(MarkdownEditor, self).__call__(field, **kwargs)


class StringField(FieldHelper, fields.StringField):
    pass


class URLField(FieldHelper, html5.URLField):
    pass


class SelectField(FieldHelper, fields.SelectField):
    widget = SelectPicker()

    def iter_choices(self):
        for value, label, selected in super(SelectField, self).iter_choices():
            yield (value, self._translations.ugettext(label), selected)


class MarkdownField(FieldHelper, fields.TextAreaField):
    widget = MarkdownEditor()


class PublishAsField(FieldHelper, Field):
    def is_visible(self, user):
        return len(user.organizations) > 0


class ReuseForm(Form):
    title = StringField(_('Title'), [validators.required()])
    url = URLField(_('URL'), [validators.required()])
    image_url = URLField(_('Image URL'), [validators.required()])
    type = SelectField(_('Type'), [validators.required()], choices=(
        ('api', _('API')),
        ('application', _('Application')),
        ('idea', _('Idea')),
        ('news_article', _('News Article')),
        ('paper', _('Paper')),
        ('post', _('Post')),
        ('visualization', _('Visualization')),
    ))
    description = MarkdownField(_('Description'), [validators.required()])
    publish_as = PublishAsField(_('Publish as'))
