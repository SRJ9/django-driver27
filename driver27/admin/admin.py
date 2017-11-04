from django.conf.urls import url
from django.shortcuts import render
from django.utils.translation import ugettext as _
from .common import CommonTabbedModelAdmin
from django.shortcuts import redirect
from .forms import *
from .inlines import *
from ..models import Driver, Competition, Circuit, Season, Result, CompetitionTeam, SeatPeriod
from .. import lr_diff, lr_intr

from django.contrib.admin import SimpleListFilter

from django.db.models import Q, Count

from django.contrib import messages

import json


@admin.register(Driver)
class DriverAdmin(RelatedCompetitionAdmin, CommonTabbedModelAdmin):
    list_display = ('__str__', 'country',)
    list_filter = ('country', 'year_of_birth', 'teams',)
    search_fields = ('last_name', 'first_name',)
    tab_overview = (
        (None, {
            'fields': ('last_name', 'first_name', 'year_of_birth', 'country')
        }),
    )
    tab_seats = (SeatInline,)
    tabs = [
        ('Overview', tab_overview),
        ('Seats', tab_seats),
    ]


class CompetitionTeamInline(CompetitionFilterInline):
    model = CompetitionTeam


@admin.register(Team)
class TeamAdmin(RelatedCompetitionAdmin, CommonTabbedModelAdmin):
    model = Team
    list_display = ('__str__', 'country', 'print_competitions')
    list_filter = ('competitions',)
    search_fields = ('name', 'full_name',)
    tab_overview = (
        (None, {
            'fields': ('name', 'full_name', 'country')
        }),
    )
    tab_competitions = (
        CompetitionTeamInline,
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

@admin.register(Competition)
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
    tab_seasons = (
        CompetitionSeasonAdmin,
    )
    tabs = [
        ('Overview', tab_overview),
        ('Team', tab_team),
        ('Seasons', tab_seasons)
    ]

@admin.register(Circuit)
class CircuitAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'country', 'opened_in')

@admin.register(GrandPrix)
class GrandPrixAdmin(RelatedCompetitionAdmin, admin.ModelAdmin):
    list_display = ('name', 'country', 'default_circuit', 'print_competitions')
    list_filter = ('competitions',)

@admin.register(Season)
class SeasonAdmin(CommonTabbedModelAdmin):
    form = SeasonAdminForm
    tab_overview = (
        (None, {
            'fields': ('year', 'competition', 'rounds', 'punctuation')
        }),
    )
    tab_races = (
        RaceInline,
    )
    tabs = [
        ('Overview', tab_overview),
        ('Races', tab_races),
    ]
    readonly_fields = ('print_copy_season',)
    list_display = ('__str__', 'print_copy_season', 'print_copy_races',)
    list_filter = ('competition',)

    def get_season_copy(self, copy_id):
        seasons = Season.objects.filter(pk=copy_id)
        copy_dict = {}
        if seasons.count():
            season = seasons.first()
            copy_dict = {
                # 'year': season.year+1,
                'competition': season.competition,
                'rounds': season.rounds,
                'punctuation': season.punctuation
            }
        return copy_dict

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
                'available_seasons': available_seasons,
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

    def get_duplicate_season(self, request, pk, *args, **kwargs):
        season = Season.objects.get(pk=pk)

        context = {
            'season': season,
            'opts': self.model._meta,
            'app_label': self.model._meta.app_label,
            'change': True,
            'title': 'Duplicating season {season}'.format(season=season)

        }
        if request.POST.get('_selector'):
            season_year = request.POST.get('year')
            if Season.objects.filter(year=season_year).exists():
                error_message = _("Season with {competition: %(competition)s, year: %(year)s} already exists") % \
                                {'competition': season.competition, 'year': season_year}
                context['error_message'] = error_message
            else:
                new_season, created = Season.objects.get_or_create(competition=season.competition,
                                                          year=season_year,
                                                          rounds=season.rounds,
                                                          punctuation=season.punctuation)

                return redirect('admin:driver27_season_change', new_season.pk)


        return render(request, 'driver27/admin/copy/copy_season.html', context)

    def print_copy_season(self, obj):
        if obj.pk:
            copy_link = reverse("admin:dr27-copy-season", kwargs={'pk': obj.pk})
            return "<a href='{link}'>{copy_text}</a>".format(link=copy_link,
                                                                    copy_text=_('Duplicate season'))
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

    def get_urls(self, *args, **kwargs):
        urls = super(SeasonAdmin, self).get_urls(*args, **kwargs)
        new_urls = [
                       url(r'^(?P<pk>[\d]+)/get_copy_races/$', self.admin_site.admin_view(self.get_copy_races),
                           name='dr27-copy-races'),
                       url(r'^(?P<pk>[\d]+)/duplicate/$', self.admin_site.admin_view(self.get_duplicate_season),
                           name='dr27-copy-season'),
                   ] + urls
        return new_urls

@admin.register(Race)
class RaceAdmin(CommonTabbedModelAdmin):
    list_display = ('__str__', 'season', 'print_pole', 'print_winner', 'print_fastest', 'print_positions')
    list_filter = ('season', 'season__competition', 'circuit', 'grand_prix',)

    readonly_fields = ('print_positions',)
    form = RaceAdminForm
    tab_overview = (
        (None, {
            'fields': ('season', 'round', 'grand_prix', 'circuit', 'date', 'alter_punctuation', 'fastest_car',
                       'print_positions')
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

    def get_urls(self):
        urls = super(RaceAdmin, self).get_urls()
        urlpatterns = [
            url(r'(?P<pk>\d+)/positions/$', self.admin_site.admin_view(self.edit_positions), name='driver27_race_results')
        ]

        return urlpatterns + urls

    def print_positions(self, obj):
        link = reverse("admin:driver27_race_results", kwargs={'pk': obj.pk})
        return "<a href='{link}'>{text}</a>".format(link=link,
                                                    text=_('Positions'))
    print_positions.allow_tags = True
    print_positions.short_description = 'Positions'

    def edit_positions(self, request, pk, *args, **kwargs):
        race = Race.objects.get(pk=pk)
        if request.method == 'POST':
            positions = request.POST.get('positions')
            positions = json.loads(positions)

            results_pk = {
                'to_remove': list(race.results.values_list('pk', flat=True)),
                'created': []
            }


            for position in positions:
                result, created = Result.objects.update_or_create(
                    seat_id=position['seat_id'],
                    race=race,
                    defaults=position
                )
                if created:
                    results_pk['created'].append(result.pk)
                else:
                    results_pk['to_remove'].remove(result.pk)
                    has_changed = False
                    for attr in ['qualifying', 'finish', 'retired', 'wildcard']:
                        if getattr(result, attr) != position[attr]:
                            has_changed = True

                    if not has_changed:
                        continue

            Result.objects.filter(pk__in=results_pk['to_remove']).delete()
            messages.success(request, 'Positions are updated. Created: {created},  Deleted: {to_remove}'\
                             .format(**{x:len(results_pk[x]) for x in results_pk}))
        context = {'race': race}
        return render(request, 'driver27/admin/positions.html', context, *args, **kwargs)

    def print_seat(self, seat):
        return u"{driver}".format(driver=seat.driver) if seat else None

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

    class Media:
        js = ['driver27/js/list_filter_collapse.js']


class SeatPeriodFilter(SimpleListFilter):
    title = 'period'
    parameter_name = 'period'

    def lookups(self, request, model_admin):
        periods = Season.objects.order_by().values_list('year', flat=True).distinct()
        return [(p, p) for p in periods]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(
                Q(periods__from_year__lte=self.value()) | Q(periods__from_year__isnull=True),
                Q(periods__until_year__gte=self.value()) | Q(periods__until_year__isnull=True)
            ).distinct()
        else:
            return queryset

@admin.register(Seat)
class SeatAdmin(CommonTabbedModelAdmin):
    list_display = ('driver', 'team', 'print_periods')
    list_filter = (SeatPeriodFilter, 'driver', 'team', 'team__competitions')
    tab_overview = (
        (None, {
            'fields': ('team', 'driver')
        }),
    )
    tab_periods = (
        SeatPeriodInline,
    )
    tabs = [
        ('Overview', tab_overview),
        ('Periods', tab_periods),
    ]

    def print_periods(self, obj):
        periods = obj.periods.all()
        if periods.count():
            return ', '.join(['{from_year} to {until_year}'.format(from_year=period.from_year,
                                                                   until_year=period.until_year) for period in periods])
        else:
            return None

    print_periods.short_description = _('periods')

    class Media:
        js = ['driver27/js/list_filter_collapse.js']

@admin.register(SeatPeriod)
class SeatPeriodAdmin(admin.ModelAdmin):
    list_filter = ('seat__driver', 'seat__team', 'seat__team__competitions',)

    class Media:
        js = ['driver27/js/list_filter_collapse.js']


