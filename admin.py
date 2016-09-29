from django.contrib import admin

from .models import Driver, Team, Competition, Circuit, Season, GrandPrix, Race
from .models import DriverCompetition, DriverCompetitionTeam

class RaceInline(admin.TabularInline):
    model = Race
    extra = 1

class DriverCompetitionTeamInline(admin.TabularInline):
    model = DriverCompetitionTeam
    extra = 3

class DriverCompetitionInline(admin.TabularInline):
    model = DriverCompetition
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
    inlines = [RaceInline]

admin.site.register(Driver, DriverAdmin)
admin.site.register(Team)
admin.site.register(Competition)
admin.site.register(Circuit)
admin.site.register(Season, SeasonAdmin)
admin.site.register(GrandPrix)

# m2m admin
admin.site.register(DriverCompetition, DriverCompetitionAdmin)
