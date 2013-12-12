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
        # Suffix name with _id for id
        id = kwargs.pop('id', None)
        if not id and '_name' in kwargs:
            id = '{_name}_id'.format(**kwargs)
        super(FieldHelper, self).__init__(*args, id=id, **kwargs)

    def is_visible(self, user):
        return True


class WidgetHelper(object):
    classes = []
    defaults = {}

    def __call__(self, field, **kwargs):
        # Handle extra classes
        classes = (kwargs.pop('class', '') or kwargs.pop('class_', '')).split()
        extra_classes = self.classes if isinstance(self.classes, (list, tuple)) else [self.classes]
        classes.extend([cls for cls in extra_classes if cls not in classes])
        kwargs['class'] = ' '.join(classes)

        # Handle defaults
        for key, value in self.defaults.items():
            kwargs.setdefault(key, value)

        return super(WidgetHelper, self).__call__(field, **kwargs)


class SelectPicker(WidgetHelper, widgets.Select):
    classes = 'selectpicker'


class MarkdownEditor(WidgetHelper, widgets.TextArea):
    classes = 'md'
    defaults = {'rows': 8}


class FormatAutocompleter(WidgetHelper, widgets.TextInput):
    classes = 'format-completer'


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


class ResourceForm(Form):
    name = StringField(_('Name'), [validators.required()])
    url = URLField(_('URL'), [validators.required()])
    format = StringField(_('Format'), widget=FormatAutocompleter())
    description = MarkdownField(_('Description'), [validators.required()])


class GroupCreateForm(Form):
    title = StringField(_('Title'), [validators.required()])
    description = MarkdownField(_('Description'), [validators.required()])
    image_url = URLField(_('Image URL'), [validators.required()])
