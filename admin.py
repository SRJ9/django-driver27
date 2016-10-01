from django.contrib import admin
from django.conf.urls import url
from django.shortcuts import render

from .models import Driver, Team, Competition, Circuit, Season, GrandPrix, Race, Result
from .models import DriverCompetition, DriverCompetitionTeam, TeamSeasonRel

lr_diff = lambda l, r: list(set(l).difference(r))
lr_intr = lambda l, r: list(set(l).intersection(r))

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

class DriverCompetitionAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'competition', 'teams_verbose', 'print_current')
    list_filter = ('competition',)
    inlines = [DriverCompetitionTeamInline]

    def print_current(self, obj):
        filter_current = DriverCompetitionTeam.objects.filter(enrolled__driver=obj.driver).filter(enrolled__competition=obj.competition).filter(current=True)
        if filter_current.count():
            return filter_current[0].team
        else:
            return None
    print_current.short_description = 'current team'


class DriverAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'country')
    list_filter = ('competitions__name',)
    inlines = [DriverCompetitionInline]

class SeasonAdmin(admin.ModelAdmin):
    inlines = [TeamSeasonInline, RaceInline]

class RaceAdmin(admin.ModelAdmin):
    def get_urls(self):
        urls = super(RaceAdmin, self).get_urls()
        urlpatterns = [
            url(r'(?P<race_id>\d+)/results/$', self.admin_site.admin_view(self.results), name='results')
        ]

        return urlpatterns + urls

    def add_result_entries(self, request, entries, race):
        for entry in entries:
            qualifying = request.POST.get('qualifying_' + str(entry), None)
            finish = request.POST.get('finish_' + str(entry), None)
            Result.objects.create(
                race=race,
                contender_id=entry,
                qualifying=qualifying if qualifying else None,
                finish=finish if finish else None
            )

    def update_result_entries(self, request, entries, race):
        for entry in entries:
            qualifying = request.POST.get('qualifying_' + str(entry), None)
            finish = request.POST.get('finish_' + str(entry), None)
            result = Result.objects.get(race=race, contender_id=entry)
            update_needed = False
            if qualifying != result.qualifying:
                result.qualifying = qualifying if qualifying else None
                update_needed = True
            if finish != result.finish:
                result.finish = finish if finish else None
                update_needed = True
            if update_needed:
                result.save()

    def del_result_entries(self, request, entries, race):
        for entry in entries:
            result = Result.objects.get(race=race, contender_id=entry)
            result.delete()

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
                entries_to_add = lr_diff(post_entries, race_contenders)
                entries_to_upd = lr_intr(post_entries, race_contenders)
                entries_to_del = lr_diff(race_contenders, post_entries)
                if entries_to_add:
                    self.add_result_entries(request, entries_to_add, race)

                if entries_to_upd:
                    self.update_result_entries(request, entries_to_upd, race)

                if entries_to_del:
                    self.del_result_entries(request, entries_to_del, race)
            else:
                self.del_result_entries(request, race_contenders, race)



        race_contenders = [result.contender_id for result in race.results.all()]
        entries = []
        for contender in season_contenders:
            enrolled = contender.enrolled
            driver_name = ' '.join((enrolled.driver.first_name, enrolled.driver.last_name))

            qualifying = ''
            finish = ''

            if contender.pk in race_contenders:
                result = Result.objects.get(race=race, contender=contender)
                qualifying = result.qualifying if result.qualifying else ''
                finish = result.finish if result.finish else ''

            checked_ord = (contender.pk in race_contenders)
            finish_ord = finish if finish else 999999999

            entry = {
                'contender': contender.pk,
                'driver_name': driver_name,
                'team': contender.team.name,
                'checked_ord': checked_ord,
                'checked': 'checked' if checked_ord else '',
                'qualifying': qualifying,
                'finish': finish,
                'finish_ord': finish_ord
            }
            entries.append(entry)

            entries = sorted(entries, key=lambda x: (-x['checked_ord'],x['finish_ord']))

        context = {'race': race, 'season': season, 'entries': entries, 'title': title}
        tpl = 'driver27/admin/results.html'
        return render(request, tpl, context)

admin.site.register(Driver, DriverAdmin)
admin.site.register(Team)
admin.site.register(Competition)
admin.site.register(Circuit)
admin.site.register(Season, SeasonAdmin)
admin.site.register(GrandPrix)
admin.site.register(Race, RaceAdmin)

# m2m admin
admin.site.register(DriverCompetition, DriverCompetitionAdmin)
