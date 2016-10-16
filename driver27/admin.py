from django.contrib import admin
from django import forms
from django.conf.urls import url
from django.shortcuts import render
from django.db.models.fields import BLANK_CHOICE_DASH

from django.core.urlresolvers import reverse

from tabbed_admin import TabbedModelAdmin

from .models import Driver, Team, Competition, Circuit, Season, GrandPrix, Race, Result
from .models import Contender, Seat, TeamSeason
from .models import ContenderSeason
import punctuation

lr_diff = lambda l, r: list(set(l).difference(r))
lr_intr = lambda l, r: list(set(l).intersection(r))

class RelatedCompetitionAdmin(object):
    """ Aux class to share print_competitions method between driver and team """
    def print_competitions(self, obj):
        return ', '.join("%s" % competition for competition in obj.competitions.all())
    print_competitions.short_description = 'competitions'

class RaceInline(admin.TabularInline):
    model = Race
    extra = 1
    readonly_fields = ('print_results_link', )

    def print_results_link(self, obj):
        if obj.pk:
            results_url = reverse("admin:driver27_race_results", args=[obj.pk])
            return '<a href="%s">%s</a>' % (results_url, 'Results')
        else:
            return None
    print_results_link.allow_tags = True
    print_results_link.short_description = 'Results link'

    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        if db_field.name == 'grand_prix':
            if request._obj_ is not None:
                kwargs['queryset'] = GrandPrix.objects.filter(competitions__exact=request._obj_.competition)
        return super(RaceInline, self).formfield_for_foreignkey(db_field, request, **kwargs)

class SeatInline(admin.TabularInline):
    model = Seat
    extra = 3

    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        if db_field.name == 'team':
            if request._obj_ is not None:
                kwargs['queryset'] = Team.objects.filter(competitions__exact=request._obj_.competition)
        return super(SeatInline, self).formfield_for_foreignkey(db_field, request, **kwargs)

class SeatSeasonInline(admin.TabularInline):
    model = Seat.seasons.through
    extra = 3
    ordering = ('seat',)

    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        if db_field.name == 'seat':
            if request._obj_ is not None:
                kwargs['queryset'] = Seat.objects.filter(
                    contender__competition__exact=request._obj_.competition)
        return super(SeatSeasonInline, self).formfield_for_foreignkey(db_field, request, **kwargs)


class ContenderInline(admin.TabularInline):
    model = Contender
    extra = 1

class TeamSeasonInline(admin.TabularInline):
    model = TeamSeason
    extra = 1

    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        if db_field.name == 'team':
            if request._obj_ is not None:
                kwargs['queryset'] = Team.objects.filter(competitions__exact=request._obj_.competition)
        return super(TeamSeasonInline, self).formfield_for_foreignkey(db_field, request, **kwargs)

class TeamInline(admin.TabularInline):
    model = Team
    extra = 1

class DriverAdmin(RelatedCompetitionAdmin, TabbedModelAdmin):
    list_display = ('__unicode__', 'country', 'print_competitions')
    list_filter = ('competitions__name',)
    tab_overview = (
        (None, {
        'fields': ('last_name', 'first_name', 'year_of_birth', 'country')
        }),
    )
    tab_competitions = (
        ContenderInline,
    )
    tabs = [
        ('Overview', tab_overview),
        ('Competitions', tab_competitions)
    ]

class TeamAdmin(RelatedCompetitionAdmin, admin.ModelAdmin):
    list_display = ('__unicode__', 'country', 'print_competitions')

class CompetitionAdmin(TabbedModelAdmin):
    model = Competition
    list_display = ('name', 'full_name')
    tab_overview = (
        (None, {
        'fields': ('name', 'full_name', 'country', 'slug')
        }),
    )
    tab_drivers = (
        ContenderInline,
    )
    tabs = [
        ('Overview', tab_overview),
        ('Drivers', tab_drivers)
    ]

class CircuitAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'country', 'opened_in')

class GrandPrixAdmin(RelatedCompetitionAdmin, admin.ModelAdmin):
    list_display = ('name', 'country', 'default_circuit', 'print_competitions')

class SeasonAdminForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(SeasonAdminForm, self).__init__(*args, **kwargs)
        punctuation_dict = punctuation.DRIVER27_PUNCTUATION
        punctuation_choices = [(punct['code'], punct['label']) for punct in punctuation_dict]
        self.fields['punctuation'] = forms.ChoiceField(choices=BLANK_CHOICE_DASH + list(punctuation_choices), initial=None)

    class Meta:
        model = Season
        fields = ('year', 'competition', 'rounds', 'punctuation')

class SeasonAdmin(TabbedModelAdmin):
    form = SeasonAdminForm
    tab_overview = (
        (None, {
        'fields': ('year', 'competition', 'rounds', 'punctuation')
        }),
    )
    tab_teams = (
        TeamSeasonInline,
    )
    tab_drivers = (
        # (None, {
        #     'fields': ('team_contenders',)
        # }),
        SeatSeasonInline,
    )
    tab_races = (
        RaceInline,
    )
    tabs = [
        ('Overview', tab_overview),
        ('Teams', tab_teams),
        ('Drivers', tab_drivers),
        ('Races', tab_races),
    ]

    def get_form(self, request, obj=None, **kwargs):
        # just save obj reference for future processing in Inline
        request._obj_ = obj
        return super(SeasonAdmin, self).get_form(request, obj, **kwargs)

class RaceAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'season', 'print_pole', 'print_winner', 'print_fastest')
    list_filter = ('season',)
    readonly_fields = ('print_results_link',)

    def print_pole(self, obj):
        return "%s" % obj.pole.driver
    print_pole.short_description = 'Pole'

    def print_winner(self, obj):
        return "%s" % obj.winner.driver
    print_winner.short_description = 'Winner'

    def print_fastest(self, obj):
        return "%s" % obj.fastest.driver
    print_fastest.short_description = 'Fastest'

    def get_urls(self):
        urls = super(RaceAdmin, self).get_urls()
        urlpatterns = [
            url(r'(?P<race_id>\d+)/results/$', self.admin_site.admin_view(self.results), name='driver27_race_results')
        ]

        return urlpatterns + urls

    def print_results_link(self, obj):
        results_url = reverse("admin:driver27_race_results", args=[obj.pk])
        return '<a href="%s">%s</a>' % (results_url, 'Results')
    print_results_link.allow_tags = True
    print_results_link.short_description = 'link'

    def add_result_entries(self, request, entries, race):
        for entry in entries:
            field_prefix = '%s-%s-' % ('seat-', str(entry))
            qualifying = request.POST.get(field_prefix + 'qualifying', None)
            finish = request.POST.get(field_prefix + 'finish', None)
            fastest_lap = request.POST.get(field_prefix + 'fastest-lap', None)
            retired = request.POST.get(field_prefix + 'retired', None)
            wildcard = request.POST.get(field_prefix + 'wildcard', None)
            Result.objects.create(
                race=race,
                seat_id=entry,
                qualifying=qualifying if qualifying else None,
                finish=finish if finish else None,
                fastest_lap=fastest_lap if fastest_lap else False,
                retired = retired if retired else False,
                wildcard = wildcard if wildcard else False
            )

    def update_result_entries(self, request, entries, race):
        for entry in entries:
            field_prefix = '%s-%s-' % ('seat', entry)
            # raise Exception('field_prefix')
            qualifying = request.POST.get(field_prefix + 'qualifying', None)
            finish = request.POST.get(field_prefix + 'finish', None)
            fastest_lap = request.POST.get(field_prefix + 'fastest-lap', None)
            retired = request.POST.get(field_prefix + 'retired', None)
            wildcard = request.POST.get(field_prefix + 'wildcard', None)
            result = Result.objects.get(race=race, seat_id=entry)
            update_needed = False
            if qualifying != result.qualifying:
                result.qualifying = qualifying if qualifying else None
                update_needed = True
            if finish != result.finish:
                result.finish = finish if finish else None
                update_needed = True
            if fastest_lap != result.fastest_lap:
                result.fastest_lap = fastest_lap if fastest_lap else False
            if retired != result.retired:
                result.retired = retired if retired else False
            if wildcard != result.wildcard:
                result.wildcard = wildcard if wildcard else False
            if update_needed:
                result.save()

    def del_result_entries(self, request, entries, race):
        for entry in entries:
            result = Result.objects.get(race=race, seat_id=entry)
            result.delete()

    def update_race_seats(self, request, new_seats, race):
        old_seats = [result.seat_id for result in race.results.all()]
        entries_to_add = lr_diff(new_seats, old_seats)
        entries_to_upd = lr_intr(new_seats, old_seats)
        entries_to_del = lr_diff(old_seats, new_seats)
        if entries_to_add:
            self.add_result_entries(request, entries_to_add, race)

        if entries_to_upd:
            self.update_result_entries(request, entries_to_upd, race)

        if entries_to_del:
            self.del_result_entries(request, entries_to_del, race)

    def results(self, request, race_id):
        race = self.model.objects.get(pk=race_id)
        title = 'Results in %s' % race
        season = race.season
        season_seats = Seat.objects.filter(seasons__pk=season.pk)
        if request.POST:
            post_entries = request.POST.getlist('entry[]')
            if post_entries:
                post_entries = map(int, post_entries)
                self.update_race_seats(request, post_entries, race)

            else:
                race_seats = [result.seat_id for result in race.results.all()]
                self.del_result_entries(request, race_seats, race)
        race_seats = [result.seat_id for result in race.results.all()]
        entries = []
        for seat in season_seats:
            contender = seat.contender
            driver_name = ' '.join((contender.driver.first_name, contender.driver.last_name))
            season_points = ContenderSeason(contender, season).get_points(limit_races=race.round)

            points = finish = qualifying = None
            fastest_lap = retired = wildcard = False

            is_race_seat = False
            if seat.pk in race_seats:
                result = Result.objects.get(race=race, seat=seat)
                qualifying = result.qualifying
                finish = result.finish if result.finish else None
                points = result.points
                fastest_lap = result.fastest_lap
                retired = result.retired
                wildcard = result.wildcard
                is_race_seat = True

            entry = {
                'seat': seat.pk,
                'driver_name': driver_name,
                'team': seat.team.name,
                'checked': is_race_seat,
                'qualifying': qualifying,
                'qualified': True if qualifying else False,
                'finish': finish,
                'finished': True if finish else False,
                'fastest_lap': fastest_lap,
                'retired': retired,
                'wildcard': wildcard,
                'points': points,
                'season_points': season_points
            }
            entries.append(entry)

        if race_seats:
            entries = sorted(entries, key=lambda x: (
                -x['checked'],
                -x['finished'],
                x['finish'],
                -x['qualified'],
                x['qualifying'],
                -x['season_points']
            ))
        else:
            entries = sorted(entries, key=lambda x: -x['season_points'])

        context = {
            'race': race, 'season': season, 'entries': entries, 'title': title,
            'opts': self.model._meta,
            'app_label': self.model._meta.app_label,
            'change': True
        }
        tpl = 'driver27/admin/results.html'
        return render(request, tpl, context)

class ContenderAdmin(TabbedModelAdmin):
    list_display = ('__unicode__', 'competition', 'teams_verbose', 'print_current')
    list_filter = ('competition',)
    tab_overview = (
        (None, {
        'fields': ('driver', 'competition')
        }),
    )
    tab_teams = (
        SeatInline,
    )
    tabs = [
        ('Overview', tab_overview),
        ('Teams', tab_teams)
    ]

    def print_current(self, obj):
        filter_current = Seat.objects.filter(
            contender__driver=obj.driver,
            contender__competition=obj.competition,
            current=True)
        return filter_current[0].team if filter_current.count() else None
    print_current.short_description = 'current team'

    def get_form(self, request, obj=None, **kwargs):
        # just save obj reference for future processing in Inline
        request._obj_ = obj
        return super(ContenderAdmin, self).get_form(request, obj, **kwargs)


admin.site.register(Driver, DriverAdmin)
admin.site.register(Team, TeamAdmin)
admin.site.register(Competition, CompetitionAdmin)
admin.site.register(Circuit, CircuitAdmin)
admin.site.register(GrandPrix, GrandPrixAdmin)
admin.site.register(Season, SeasonAdmin)
admin.site.register(Race, RaceAdmin)

# m2m admin
admin.site.register(Contender, ContenderAdmin)
