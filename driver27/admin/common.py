from django import forms
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _
from tabbed_admin import TabbedModelAdmin


# http://stackoverflow.com/a/34567383
class AlwaysChangedModelForm(forms.ModelForm):
    def is_empty_form(self, *args, **kwargs):
        empty_form = True
        for name, field in self.fields.items():
            prefixed_name = self.add_prefix(name)
            data_value = field.widget.value_from_datadict(self.data, self.files, prefixed_name)
            if data_value:
                empty_form = False
                break
        return empty_form

    def has_changed(self, *args, **kwargs):
        """ Should returns True if data differs from initial.
        By always returning true even unchanged inlines will get validated and saved."""
        if self.instance.pk is None and self.initial:
            if not self.changed_data:
                return True
            if self.is_empty_form():
                return False
        return super(AlwaysChangedModelForm, self).has_changed()


class RelatedCompetitionAdmin(object):
    """ Aux class to share print_competitions method between driver and team """
    def print_competitions(self, obj):
        if hasattr(obj, 'competitions'):
            return ', '.join('{competition}'.format(competition=competition)
                             for competition in obj.competitions.all())
        else:
            return None
    print_competitions.short_description = _('competitions')


class CommonTabbedModelAdmin(TabbedModelAdmin):
    def get_form(self, request, obj=None, **kwargs):
        # just save obj reference for future processing in Inline
        if request and obj:
            request._obj_ = obj
        return super(CommonTabbedModelAdmin, self).get_form(request=request, obj=obj, **kwargs)
