from django.contrib import admin
from django.db.models import Q
from ..models import Team, GrandPrix, Seat, Race


class CompetitionFilterInline(admin.TabularInline):
    def get_formset(self, request, obj=None, **kwargs):
        formset = super(CompetitionFilterInline, self).get_formset(request, obj, **kwargs)
        formset.request = request
        return formset

    @staticmethod
    def seat_for_foreignkey(obj):
        if isinstance(obj, Race):
            seat_filter = {'team__competitions__seasons__races': obj}
        else:
            seat_filter = {'contender__competition__exact': obj.competition}
        return Seat.objects.filter(**seat_filter).filter(

            Q(periods__from_year__lte=obj.season.year) | Q(periods__from_year__isnull=True),
            Q(periods__until_year__gte=obj.season.year) | Q(periods__until_year__isnull=True)
        ).distinct()

    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        if getattr(request, '_obj_', None):
            obj = request._obj_
            if db_field.name == 'team' and not isinstance(obj, Team):
                kwargs['queryset'] = Team.objects.filter(competitions__exact=obj.competition)
            elif db_field.name == 'grand_prix':
                kwargs['queryset'] = GrandPrix.objects.filter(competitions__exact=obj.competition)
            elif db_field.name == 'seat' and not isinstance(obj, Seat):
                kwargs['queryset'] = self.seat_for_foreignkey(obj)
        return super(CompetitionFilterInline, self).formfield_for_foreignkey(db_field, request, **kwargs)
