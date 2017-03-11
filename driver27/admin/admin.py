from django.conf.urls import url
from django.shortcuts import render
from django.utils.translation import ugettext as _
from .common import CommonTabbedModelAdmin
from django.shortcuts import redirect
from .forms import *
from .inlines import *
from ..models import Contender, SeatsSeason
from ..models import ContenderSeason
from ..models import Driver, Competition, Circuit, Season, Result
from .. import lr_diff, lr_intr


class DriverAdmin(RelatedCompetitionAdmin, CommonTabbedModelAdmin):
    list_display = ('__str__', 'country', 'print_competitions')
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


class TeamAdmin(RelatedCompetitionAdmin, CommonTabbedModelAdmin):
    model = Team
    list_display = ('__str__', 'country', 'print_competitions')
    list_filter = ('competitions', 'seats__seasons')
    tab_overview = (
        (None, {
                'fields': ('name', 'full_name', 'country')
        }),
    )
    tab_competitions = (
        (None, {
            'fields': ('competitions',)
        }),
    )
    tab_seats = (
        SeatInline,
    )
    tabs = [
        ('Overview', tab_overview),
        ('Competitions', tab_competitions),
        ('Seats', tab_seats),
    ]


class CompetitionSeasonAdmin(admin.TabularInline):
    model = Season


class CompetitionAdmin(CommonTabbedModelAdmin):
    model = Competition
    list_display = ('name', 'full_name')
    tab_overview = (
        (None, {
        'fields': ('name', 'full_name', 'country', 'slug')
        }),
    )
    tab_team = (
        CompetitionTeamInline,
    )
    tab_drivers = (
        ContenderInline,
    )
    tab_seasons = (
        CompetitionSeasonAdmin,
    )
    tabs = [
        ('Overview', tab_overview),
        ('Team', tab_team),
        ('Drivers', tab_drivers),
        ('Seasons', tab_seasons)
    ]


class CircuitAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'country', 'opened_in')


class GrandPrixAdmin(RelatedCompetitionAdmin, admin.ModelAdmin):
    list_display = ('name', 'country', 'default_circuit', 'print_competitions')
    list_filter = ('competitions',)


class SeatSeasonAdmin(CommonTabbedModelAdmin):
    tab_overview = (
        (None, {
                'fields': ('year', 'competition', 'rounds', 'punctuation')
        }),
    )
    tab_teams = (
        TeamSeasonInline,
    )
    tab_drivers = (
        SeatSeasonInline,
    )
    tabs = [
        ('Overview', tab_overview),
        ('Drivers', tab_drivers),
    ]

    readonly_fields = ('year', 'competition', 'rounds', 'punctuation')
    list_filter = ('competition',)
    list_display = ('competition', 'year',)

    def has_add_permission(self, request):
        return False


class SeasonAdmin(CommonTabbedModelAdmin):
    form = SeasonAdminForm
    tab_overview = (
        (None, {
        'fields': ('year', 'competition', 'rounds', 'punctuation')
        }),
    )
    tab_teams = (
        TeamSeasonInline,
    )
    # tab_drivers = (
    #     SeatSeasonInline,
    # )
    tab_races = (
        RaceInline,
    )
    tabs = [
        ('Overview', tab_overview),
        ('Teams', tab_teams),
        # ('Drivers', tab_drivers),
        ('Races', tab_races),
    ]
    readonly_fields = ('print_copy_season',)
    list_display = ('__str__', 'print_copy_season', 'print_copy_races', 'print_copy_teams', 'print_copy_seats')
    list_filter = ('competition',)

    def get_season_copy(self, copy_id):
        seasons = Season.objects.filter(pk=copy_id)
        copy_dict = {}
        if seasons.count():
            season = seasons.first()
            copy_dict = {
                #'year': season.year+1,
                'competition': season.competition,
                'rounds': season.rounds,
                'punctuation': season.punctuation
            }
        return copy_dict

    def get_changeform_initial_data(self, request, *args, **kwargs):
        copy_id = request.GET.get('copy')
        if copy_id:
            return self.get_season_copy(copy_id)


    def get_copy_item(self, request, pk, item_cls, items_plural, *args, **kwargs):
        season = Season.objects.get(pk=pk)
        if request.POST.get('_confirm'):
            post_items_pk = request.POST.getlist('items', [])
            post_season_destiny = request.POST.get('season_destiny', None)
            item_cls.bulk_copy(post_items_pk, post_season_destiny)
            return redirect('admin:driver27_season_change', post_season_destiny)

        elif request.POST.get('_selector'):

            post_season_destiny = request.POST.get('season_destiny', None)
            context = {
                'season': season,
                'opts': self.model._meta,
                'app_label': self.model._meta.app_label,
                'change': True,
                'items_plural': items_plural,
                'title': 'Copy {items_plural} from season {season_slug} > Step 2'.format(items_plural=items_plural,
                                                                               season_slug=season),
                'step': 2
            }
            if post_season_destiny:
                post_items_pk = request.POST.getlist('items', [])
                check_list_in_season = item_cls.check_list_in_season(post_items_pk, post_season_destiny)


                context.update(
                    {
                        'season_destiny': post_season_destiny,
                        'not_exists': check_list_in_season.get('not_exists'),
                        'both_exists': check_list_in_season.get('both_exists'),
                        'conditional_exists': check_list_in_season.get('conditional_exists', None),
                        'can_save': check_list_in_season.get('can_save'),
                        'season_destiny_info': check_list_in_season.get('season_info')
                    }
                )
            else:
                context['no_destiny'] = True
        else:
            items = getattr(season, items_plural).all()
            available_seasons = Season.objects.filter(competition=season.competition).exclude(pk=pk)

            context = {
                'season': season,
                'items': items,
                'available_seasons':  available_seasons,
                'opts': self.model._meta,
                'app_label': self.model._meta.app_label,
                'change': True,
                'items_plural': items_plural,
                'title': 'Copy {items_plural} from season {season_slug}'.format(items_plural=items_plural,
                                                                               season_slug=season),
                'step': 1
            }

        return render(request, 'driver27/admin/copy/copy_items.html', context)

    def get_copy_races(self, request, pk, *args, **kwargs):
        return self.get_copy_item(request, pk, Race, 'races', *args, **kwargs)

    def get_copy_teams(self, request, pk, *args, **kwargs):
        return self.get_copy_item(request, pk, Team, 'teams', *args, **kwargs)

    def get_copy_seats(self, request, pk, *args, **kwargs):
        return self.get_copy_item(request, pk, Seat, 'seats', *args, **kwargs)

    def print_copy_season(self, obj):
        if obj.pk:
            copy_link = reverse("admin:driver27_season_add")
            get_copy_id = '?copy={obj_pk}'.format(obj_pk=obj.pk)
            return "<a href='{link}{query}'>{copy_text}</a>".format(link=copy_link,
                                                                    query=get_copy_id,
                                                                    copy_text=_('Copy'))
        else:
            return ''
    print_copy_season.short_description = _('Create new season from this')
    print_copy_season.allow_tags = True

    def print_copy_link(self, obj, reverse_link, copy_text):
        if obj.pk:
            copy_link = reverse(reverse_link, kwargs={'pk': obj.pk})
            return "<a href='{link}'>{copy_text}</a>".format(link=copy_link, copy_text=copy_text)
        else:
            return ''

    def print_copy_races(self, obj):
        return self.print_copy_link(obj, "admin:dr27-copy-races", _('copy races'))
    print_copy_races.short_description = _('copy races')
    print_copy_races.allow_tags = True

    def print_copy_teams(self, obj):
        return self.print_copy_link(obj, "admin:dr27-copy-teams", _('copy teams'))
    print_copy_teams.short_description = _('copy teams')
    print_copy_teams.allow_tags = True

    def print_copy_seats(self, obj):
        return self.print_copy_link(obj, "admin:dr27-copy-seats", _('copy seats'))
    print_copy_seats.short_description = _('copy seats')
    print_copy_seats.allow_tags = True

    def get_urls(self, *args, **kwargs):
        urls = super(SeasonAdmin, self).get_urls(*args, **kwargs)
        new_urls = [
            url(r'^(?P<pk>[\d]+)/get_copy_races/$', self.admin_site.admin_view(self.get_copy_races), name='dr27-copy-races'),
            url(r'^(?P<pk>[\d]+)/get_copy_teams/$', self.admin_site.admin_view(self.get_copy_teams), name='dr27-copy-teams'),
            url(r'^(?P<pk>[\d]+)/get_copy_seats/$', self.admin_site.admin_view(self.get_copy_seats), name='dr27-copy-seats')
        ] + urls
        return new_urls


class RaceAdmin(CommonTabbedModelAdmin):
    list_display = ('__str__', 'season', 'print_pole', 'print_winner', 'print_fastest',)
    list_filter = ('season', 'season__competition',)

    tab_overview = (
        (None, {
            'fields': ('season', 'round', 'grand_prix', 'circuit', 'date', 'alter_punctuation')
        }),
    )
    tab_results = (
        ResultInline,
    )
    tabs = [
        ('Overview', tab_overview),
        # ('Summary', tab_summary),
        # ('Drivers', tab_drivers),
        ('Results', tab_results),
    ]

    # def get_urls(self):
    #     urls = super(RaceAdmin, self).get_urls()
    #     urlpatterns = [
    #         url(r'(?P<race_id>\d+)/results/$', self.admin_site.admin_view(self.results), name='driver27_race_results')
    #     ]
    #
    #     return urlpatterns + urls

    def print_seat(self, seat):
        return u"{driver}".format(driver=seat.contender.driver) if seat else None

    def print_pole(self, obj):
        return self.print_seat(obj.pole)
    print_pole.short_description = _('Pole')

    def print_winner(self, obj):
        return self.print_seat(obj.winner)
    print_winner.short_description = _('Winner')

    def print_fastest(self, obj):
        return self.print_seat(obj.fastest)
    print_fastest.short_description = _('Fastest')

    @staticmethod
    def clean_position(position):
        try:
            position = int(position)
        except (ValueError, TypeError):
            position = None
        return position

    # def edit_result_entries(self, request, entries, race, action='update'):
    #     for entry in entries:
    #         field_prefix = '%s-%s-' % ('seat', str(entry))
    #         qualifying = request.POST.get(field_prefix + 'qualifying', None)
    #         finish = request.POST.get(field_prefix + 'finish', None)
    #         fastest_lap = request.POST.get(field_prefix + 'fastest-lap', False)
    #         retired = request.POST.get(field_prefix + 'retired', False)
    #         wildcard = request.POST.get(field_prefix + 'wildcard', False)
    #
    #         qualifying = self.clean_position(qualifying)
    #         finish = self.clean_position(finish)
    #
    #         dict_to_save = {
    #             'qualifying': qualifying,
    #             'finish': finish,
    #             'fastest_lap': fastest_lap,
    #             'retired': retired,
    #             'wildcard': wildcard
    #         }
    #         if action == 'update':
    #             # filter allows update
    #             result = Result.objects.filter(race=race, seat_id=entry)
    #             result.update(**dict_to_save)
    #         elif action == 'add':
    #             Result.objects.create(
    #                 race=race,
    #                 seat_id=entry,
    #                 **dict_to_save
    #             )
    #
    # def add_result_entries(self, request, entries, race):
    #     self.edit_result_entries(request, entries, race, action='add')
    #
    # def update_result_entries(self, request, entries, race):
    #     self.edit_result_entries(request, entries, race, action='update')
    #
    # def del_result_entries(self, request, entries, race):
    #     for entry in entries:
    #         result = Result.objects.get(race=race, seat_id=entry)
    #         result.delete()
    #
    # def update_race_seats(self, request, new_seats, race):
    #     old_seats = [result.seat_id for result in race.results.all()]
    #     entries_to_add = lr_diff(new_seats, old_seats)
    #     entries_to_upd = lr_intr(new_seats, old_seats)
    #     entries_to_del = lr_diff(old_seats, new_seats)
    #     if entries_to_add:
    #         self.add_result_entries(request, entries_to_add, race)
    #
    #     if entries_to_upd:
    #         self.update_result_entries(request, entries_to_upd, race)
    #
    #     if entries_to_del:
    #         self.del_result_entries(request, entries_to_del, race)
    #
    # def order_entries(self, entries, seats_len):
    #     if seats_len:
    #         entries = sorted(entries, key=lambda x: (
    #             -x['checked'],
    #             -x['finished'],
    #             x['finish'],
    #             -x['qualified'],
    #             x['qualifying'],
    #             -x['season_points']
    #         ))
    #     else:
    #         entries = sorted(entries, key=lambda x: -x['season_points'])
    #     return entries
    #
    # def results(self, request, race_id):
    #     race = self.model.objects.get(pk=race_id)
    #     title = 'Results in %s' % race
    #     season = race.season
    #     if request.method == 'POST':
    #         post_entries = request.POST.getlist('entry[]')
    #         if len(post_entries):
    #             post_entries = list(map(int, post_entries))
    #             self.update_race_seats(request, post_entries, race)
    #
    #         else:
    #             race_seats = [result.seat_id for result in race.results.all()]
    #             self.del_result_entries(request, race_seats, race)
    #     entries = self.get_entries(race, season)
    #
    #     context = {
    #         'race': race, 'season': season, 'entries': entries, 'title': title,
    #         'opts': self.model._meta,
    #         'app_label': self.model._meta.app_label,
    #         'change': True
    #     }
    #     tpl = 'driver27/admin/results.html'
    #     return render(request, tpl, context)
    #
    # def get_entries(self, race, season):
    #     season_seats = Seat.objects.filter(seasons__pk=season.pk)
    #     race_seats = [result.seat_id for result in race.results.all()]
    #     entries = []
    #     for seat in season_seats:
    #         contender = seat.contender
    #         driver_name = ' '.join((contender.driver.first_name, contender.driver.last_name))
    #         season_points = ContenderSeason(contender, season).get_points(limit_races=race.round)
    #
    #         points = finish = qualifying = None
    #         fastest_lap = retired = wildcard = False
    #
    #         is_race_seat = False
    #         if seat.pk in race_seats:
    #             result = Result.objects.get(race=race, seat=seat)
    #             qualifying = result.qualifying
    #             finish = result.finish if result.finish else None
    #             points = result.points
    #             fastest_lap = result.fastest_lap
    #             retired = result.retired
    #             wildcard = result.wildcard
    #             is_race_seat = True
    #
    #         entry = {
    #             'seat': seat.pk,
    #             'driver_name': driver_name,
    #             'team': seat.team.name,
    #             'checked': is_race_seat,
    #             'qualifying': qualifying,
    #             'qualified': bool(qualifying),
    #             'finish': finish,
    #             'finished': bool(finish),
    #             'fastest_lap': fastest_lap,
    #             'retired': retired,
    #             'wildcard': wildcard,
    #             'points': points,
    #             'season_points': season_points
    #         }
    #         entries.append(entry)
    #     entries = self.order_entries(entries, len(race_seats))
    #     return entries


class ContenderAdmin(CommonTabbedModelAdmin):
    list_display = ('__str__', 'competition', 'teams_verbose', 'print_current')
    list_filter = ('competition', 'seats__seasons',)
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
    print_current.short_description = _('current team')


class SeatAdmin(CommonTabbedModelAdmin):
    list_display = ('contender', 'team',)
    list_filter = ('contender__competition', 'seasons',)
    tab_overview = (
        (None, {
                'fields': ('team', 'contender', 'current')
        }),
    )
    tab_seasons = (
        # (None, {
        #         'fields': ('seasons',)
        # }),
        SeatSeasonInline,
    )
    tabs = [
        ('Overview', tab_overview),
        ('Seasons', tab_seasons)
    ]


admin.site.register(Driver, DriverAdmin)
admin.site.register(Team, TeamAdmin)
admin.site.register(Competition, CompetitionAdmin)
admin.site.register(Circuit, CircuitAdmin)
admin.site.register(GrandPrix, GrandPrixAdmin)
admin.site.register(Season, SeasonAdmin)
admin.site.register(Race, RaceAdmin)
admin.site.register(Seat, SeatAdmin)

# m2m admin
admin.site.register(Contender, ContenderAdmin)
admin.site.register(SeatsSeason, SeatSeasonAdmin)
