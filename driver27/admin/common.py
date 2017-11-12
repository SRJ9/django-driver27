from django import forms
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _
from tabbed_admin import TabbedModelAdmin

from django.utils.safestring import mark_safe
from django.utils.html import format_html
from django.utils.encoding import force_text


def get_circuit_id_from_gp(grand_prix_id):
    data_circuit_attr = ''
    if grand_prix_id:
        from driver27.models import GrandPrix
        grand_prix = GrandPrix.objects.filter(pk=grand_prix_id)
        if grand_prix.count() and grand_prix.first().default_circuit:
            data_circuit_attr = getattr(grand_prix.first().default_circuit, 'pk', '')
    return data_circuit_attr


class GrandPrixWidget(forms.widgets.Select):

    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        # Add default_circuit as data to automatize circuit selection (>2.7)
        option = None
        if hasattr(super(GrandPrixWidget, self), 'create_option'):
            option = getattr(super(GrandPrixWidget, self), 'create_option')(name, value, label, selected, index, subindex, attrs)
            option['attrs']['data-circuit'] = get_circuit_id_from_gp(value)
        return option

    def render_option(self, selected_choices, option_value, option_label):
        # Add default_circuit as data to automatize circuit selection (==2.7)
        # Override method
        if option_value is None:
            option_value = ''
        option_value = force_text(option_value)
        if option_value in selected_choices:
            selected_html = mark_safe(' selected="selected"')
            if not self.allow_multiple_selected:
                # Only allow for a single selection.
                selected_choices.remove(option_value)
        else:
            selected_html = ''
        data_circuit_attr = get_circuit_id_from_gp(option_value)

        return format_html(u'<option value="{}"{} data-circuit="{}">{}</option>',
                           option_value, selected_html,
                           data_circuit_attr, force_text(option_label))

    class Media:
        js = ['driver27/js/select_default_circuit.js']



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
