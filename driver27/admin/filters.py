from django.contrib import admin
from ..models import Team, GrandPrix, Seat


class CompetitionFilterInline(admin.TabularInline):
    def get_formset(self, request, obj=None, **kwargs):
        formset = super(CompetitionFilterInline, self).get_formset(request, obj, **kwargs)
        formset.request = request
        return formset

    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        if getattr(request, '_obj_', None):
            if db_field.name == 'team':
                kwargs['queryset'] = Team.objects.filter(competitions__exact=request._obj_.competition)
            elif db_field.name == 'grand_prix':
                kwargs['queryset'] = GrandPrix.objects.filter(competitions__exact=request._obj_.competition)
            elif db_field.name == 'seat':
                kwargs['queryset'] = Seat.objects.filter(contender__competition__exact=request._obj_.competition)
        return super(CompetitionFilterInline, self).formfield_for_foreignkey(db_field, request, **kwargs)
