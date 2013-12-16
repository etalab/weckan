# -*- coding: utf-8 -*-
from __future__ import unicode_literals

_ = lambda s: s

from wtforms import Form as WTForm, Field, validators, fields, widgets
from wtforms.fields import html5

from weckan import model


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


class RequiredIf(validators.Required):
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


class KeyValueWidget(WidgetHelper, widgets.TextInput):
    pass


class StringField(FieldHelper, fields.StringField):
    pass


class RadioField(FieldHelper, fields.RadioField):
    def __init__(self, *args, **kwargs):
        self.stacked = kwargs.pop('stacked', False)
        super(RadioField, self).__init__(*args, **kwargs)


class URLField(FieldHelper, html5.URLField):
    pass


class SelectField(FieldHelper, fields.SelectField):
    widget = SelectPicker()

    def iter_choices(self):
        for value, label, selected in super(SelectField, self).iter_choices():
            yield (value, self._translations.ugettext(label) if label else '', selected)


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
            setattr(obj, name, model.Group.get(self.data))


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
    resource_type = RadioField(_('Type'), [validators.required()], choices=(
        ('file', _('Link to a file')),
        ('api', _('Link to an API')),
        ('file.upload', _('Upload a file from your computer')),
    ))
    url = URLField(_('URL'), [validators.required()])
    format = StringField(_('Format'), widget=FormatAutocompleter())
    description = MarkdownField(_('Description'), [validators.required()])


class CommunityResourceForm(Form):
    name = StringField(_('Name'), [validators.required()])
    url = URLField(_('URL'), [validators.required()])
    format = StringField(_('Format'), widget=FormatAutocompleter())
    description = MarkdownField(_('Description'), [validators.required()])
    publish_as = PublishAsField(_('Publish as'))


class DatasetForm(Form):
    title = StringField(_('Title'), [validators.required()])
    notes = MarkdownField(_('Description'), [validators.required()])
    owner = PublishAsField(_('Publish as'))
    private = RadioField(_('Visibility'), [validators.required()], choices=(
        (True, _('Private')),
        (False, _('Public')),
    ))
    territorial_coverage = StringField(_('Territorial coverage'), widget=TerritoryAutocompleter())
    territorial_coverage_granularity = SelectField(_('Territorial coverage granularity'),
        # description=_('Dataset update periodicity'),
        choices=(
            ('', ''),
            ('poi', "Point d'intérêt"),
            ('iris', 'Iris (quartier Insee)'),
            ('commune', 'Commune'),
            ('canton', 'Canton'),
            ('epci', 'Intercommunalité (EPCI)'),
            ('department', 'Département'),
            ('region', 'Région'),
            ('pays', 'Pays'),
            ('other', "Autre"),
        )
    )

    frequency = SelectField(_('Frequency'),
        description=_('Dataset update periodicity'),
        choices=(
            ('', ''),
            ('aucune', 'Aucune'),
            ('ponctuelle', 'Ponctuelle'),
            ('temps réel', "Temps réel"),
            ('quotidienne', 'Quotidienne'),
            ('hebdomadaire', 'Hebdomadaire'),
            ('bimensuelle', 'Bimensuelle'),
            ('mensuelle', 'Mensuelle'),
            ('bimestrielle', 'Bimestrielle'),
            ('trimestrielle', 'Trimestrielle'),
            ('semestrielle', 'Semestrielle'),
            ('annuelle', 'Annuelle'),
            ("triennale", "Triennale"),
            ("quinquennale", "Quinquennale"),

            # ('aucune': 'Aucune'),
            # ('ponctuelle': 'Ponctuelle'),
            # ('temps réel': "Temps réel"),
            # ('quotidienne': 'Quotidienne'),
            # ('hebdomadaire': 'Hebdomadaire'),
            # ('bimensuelle': 'Bimensuelle'),
            # ('mensuelle': 'Mensuelle'),
            # ('bimestrielle': 'Bimestrielle'),
            # ('trimestrielle': 'Trimestrielle'),
            # ('semestrielle': 'Semestrielle'),
            # ('annuelle': 'Annuelle'),
            # ("triennale": "Triennale"),
            # ("quinquennale": "Quinquennale"),
        )
    )

class DatasetExtrasForm(Form):
    extras = KeyValueField(_('Additional data'))
