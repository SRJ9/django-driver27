from django.contrib import admin
from ..models import Team, GrandPrix, Seat, Race


class CompetitionFilterInline(admin.TabularInline):
    def get_formset(self, request, obj=None, **kwargs):
        formset = super(CompetitionFilterInline, self).get_formset(request, obj, **kwargs)
        formset.request = request
        return formset

    @staticmethod
    def seat_for_foreignkey(obj):
        if isinstance(obj, Race):
            seat_filter = {'seasons': obj.season}
        else:
            seat_filter = {'contender__competition__exact': obj.competition}
        return Seat.objects.filter(**seat_filter)

    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        if getattr(request, '_obj_', None):
            obj = request._obj_
            if db_field.name == 'team':
                kwargs['queryset'] = Team.objects.filter(competitions__exact=obj.competition)
            elif db_field.name == 'grand_prix':
                kwargs['queryset'] = GrandPrix.objects.filter(competitions__exact=obj.competition)
            elif db_field.name == 'seat':
                kwargs['queryset'] = self.seat_for_foreignkey(obj)
        return super(CompetitionFilterInline, self).formfield_for_foreignkey(db_field, request, **kwargs)
