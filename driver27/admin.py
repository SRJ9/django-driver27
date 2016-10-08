from django.contrib import admin
from django import forms
from django.conf.urls import url
from django.shortcuts import render
from django.db.models.fields import BLANK_CHOICE_DASH

from .models import Driver, Team, Competition, Circuit, Season, GrandPrix, Race, Result
from .models import DriverCompetition, DriverCompetitionTeam, TeamSeasonRel
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

class DriverCompetitionTeamInline(admin.TabularInline):
    model = DriverCompetitionTeam
    extra = 3

class DriverCompetitionInline(admin.TabularInline):
    model = DriverCompetition
    extra = 1

class TeamSeasonInline(admin.TabularInline):
    model = TeamSeasonRel
    extra = 1

class DriverCompetitionInline(admin.TabularInline):
    model = DriverCompetition
    extra = 1

class TeamInline(admin.TabularInline):
    model = Team
    extra = 1

class DriverAdmin(RelatedCompetitionAdmin, admin.ModelAdmin):
    list_display = ('__unicode__', 'country', 'print_competitions')
    list_filter = ('competitions__name',)
    inlines = [DriverCompetitionInline]

class TeamAdmin(RelatedCompetitionAdmin, admin.ModelAdmin):
    list_display = ('__unicode__', 'country', 'print_competitions')

class CompetitionAdmin(admin.ModelAdmin):
    list_display = ('name', 'full_name')
    inlines = [DriverCompetitionInline]

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

class SeasonAdmin(admin.ModelAdmin):
    inlines = [TeamSeasonInline, RaceInline]
    form = SeasonAdminForm

class RaceAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'season')
    list_filter = ('season',)
    def get_urls(self):
        urls = super(RaceAdmin, self).get_urls()
        urlpatterns = [
            url(r'(?P<race_id>\d+)/results/$', self.admin_site.admin_view(self.results), name='results')
        ]

        return urlpatterns + urls

    def add_result_entries(self, request, entries, race):
        for entry in entries:
            field_prefix = 'contender-'+str(entry)+'-'
            qualifying = request.POST.get(field_prefix + 'qualifying', None)
            finish = request.POST.get(field_prefix + 'finish', None)
            fastest_lap = request.POST.get(field_prefix + 'fastest-lap', None)
            retired = request.POST.get(field_prefix + 'retired', None)
            Result.objects.create(
                race=race,
                contender_id=entry,
                qualifying=qualifying if qualifying else None,
                finish=finish if finish else None,
                fastest_lap=fastest_lap if fastest_lap else False,
                retired = retired if retired else False
            )

    def update_result_entries(self, request, entries, race):
        for entry in entries:
            field_prefix = 'contender-'+str(entry)+'-'
            qualifying = request.POST.get(field_prefix + 'qualifying', None)
            finish = request.POST.get(field_prefix + 'finish', None)
            fastest_lap = request.POST.get(field_prefix + 'fastest-lap', None)
            retired = request.POST.get(field_prefix + 'retired', None)
            result = Result.objects.get(race=race, contender_id=entry)
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
            if update_needed:
                result.save()

    def del_result_entries(self, request, entries, race):
        for entry in entries:
            result = Result.objects.get(race=race, contender_id=entry)
            result.delete()

    def update_race_contenders(self, request, new_contenders, race):
        old_contenders = [result.contender_id for result in race.results.all()]
        entries_to_add = lr_diff(new_contenders, old_contenders)
        entries_to_upd = lr_intr(new_contenders, old_contenders)
        entries_to_del = lr_diff(old_contenders, new_contenders)
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
        season_contenders = DriverCompetitionTeam.objects.filter(seasons__pk=season.pk)
        if request.POST:
            race_contenders = [result.contender_id for result in race.results.all()]
            post_entries = request.POST.getlist('entry[]')
            if post_entries:
                post_entries = map(int, post_entries)
                self.update_race_contenders(request, post_entries, race)

            else:
                self.del_result_entries(request, race_contenders, race)
        race_contenders = [result.contender_id for result in race.results.all()]
        entries = []
        for contender in season_contenders:
            enrolled = contender.enrolled
            driver_name = ' '.join((enrolled.driver.first_name, enrolled.driver.last_name))
            season_points = ContenderSeason(enrolled, season).get_points()

            points = finish = qualifying = None
            fastest_lap = retired = False

            if contender.pk in race_contenders:
                result = Result.objects.get(race=race, contender=contender)
                qualifying = result.qualifying
                finish = result.finish if result.finish else None
                points = result.points
                fastest_lap = result.fastest_lap
                retired = result.retired

            entry = {
                'contender': contender.pk,
                'driver_name': driver_name,
                'team': contender.team.name,
                'checked': contender.pk in race_contenders,
                'qualifying': qualifying,
                'qualified': True if qualifying else False,
                'finish': finish,
                'finished': True if finish else False,
                'fastest_lap': fastest_lap,
                'retired': retired,
                'points': points,
                'season_points': season_points
            }
            entries.append(entry)

        if race_contenders:
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

        context = {'race': race, 'season': season, 'entries': entries, 'title': title}
        tpl = 'driver27/admin/results.html'
        return render(request, tpl, context)

class DriverCompetitionAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'competition', 'teams_verbose', 'print_current')
    list_filter = ('competition',)
    inlines = [DriverCompetitionTeamInline]

    def print_current(self, obj):
        filter_current = DriverCompetitionTeam.objects.filter(
            enrolled__driver=obj.driver,
            enrolled__competition=obj.competition,
            current=True)
        return filter_current[0].team if filter_current.count() else None
    print_current.short_description = 'current team'


admin.site.register(Driver, DriverAdmin)
admin.site.register(Team, TeamAdmin)
admin.site.register(Competition, CompetitionAdmin)
admin.site.register(Circuit, CircuitAdmin)
admin.site.register(GrandPrix, GrandPrixAdmin)
admin.site.register(Season, SeasonAdmin)
admin.site.register(Race, RaceAdmin)

# m2m admin
admin.site.register(DriverCompetition, DriverCompetitionAdmin)
