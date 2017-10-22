# -*- coding: utf-8 -*-
from django.db.models import Count
from django.http import Http404
from django.shortcuts import render
from django.utils.translation import ugettext as _

from django.views.decorators.http import require_http_methods
from django.shortcuts import redirect
try:
    from django.urls import reverse
except ImportError:
    from django.core.urlresolvers import reverse

from .models import Competition, Season, Race, RankModel, Driver, Team, get_tuples_from_results
from .records import get_record_config, get_record_label_dict
from .punctuation import get_punctuation_label_dict
from django.shortcuts import render, get_object_or_404

from .common import DRIVER27_NAMESPACE
from .decorators import competition_request

def competition_view(request, competition_slug):
    competition_obj = get_object_or_404(Competition, slug=competition_slug)
    title = '{competition}'.format(competition=competition_obj)
    context = {'competition': competition_obj, 'title': title}
    tpl = 'driver27/competition/view.html'
    return render(request, tpl, context)


def global_view(request):
    title = _('Global view')
    context = {'title': title}
    tpl = 'driver27/global/view.html'
    return render(request, tpl, context)

def global_tpl(request, competition=None):
    seasons = Season.objects
    if competition:
        seasons = seasons.filter(competition=competition)
    seasons = seasons.order_by('year', 'competition')
    context = {'seasons': seasons}
    tpl = 'driver27/global/_season_list.html'
    return render(request, tpl, context)

@competition_request
def season_view(request, context):
    season = context.get('season')
    title = '{competition}/{year:d}'.format(competition=season.competition, year=season.year)
    context.update(title=title)
    tpl = 'driver27/season/view.html'
    return render(request, tpl, context)


@competition_request
def _rank_view(request, context, rank_model='driver', by_season=False):
    season_or_competition = context.get('season_or_competition')
    by_season = request.POST.get('by_season', by_season)
    scoring_code = request.POST.get('scoring', None)

    punctuation_selector = get_punctuation_label_dict()
    rank_title = {'driver': _('DRIVERS'), 'team': _('TEAMS')}.get(rank_model)
    if rank_title is None:
        raise Http404(_('Impossible rank'))

    tpl = 'driver27/' + rank_model + '/list.html'
    title = u'{season_or_competition} [{title}]'.format(season_or_competition=season_or_competition,
                                                        title=rank_title)

    context.update(title=title, scoring_list=punctuation_selector, scoring_code=scoring_code, by_season=by_season)
    return render(request, tpl, context)

@competition_request
def driver_comeback_view(request, context, *args, **kwargs):
    season_or_competition = context['season_or_competition']
    rank_title = _('DRIVERS Comeback')

    title = u'{season_or_competition} [{title}]'.format(season_or_competition=season_or_competition,
                                                        title=rank_title)
    context['title'] = title
    tpl = 'driver27/driver/comeback.html'
    return render(request, tpl, context)


@competition_request
def common_olympic_view(request, context, tpl, olympic_method, rank_title):
    season_or_competition = context.get('season_or_competition')

    title = u'{season_or_competition} [{title}]'.format(season_or_competition=season_or_competition,
                                                        title=rank_title)

    context.update(title=title, olympic=True)
    return render(request, tpl, context)

def driver_olympic_view(request, *args, **kwargs):
    return common_olympic_view(request,
                               tpl='driver27/driver/list.html',
                               olympic_method='olympic_rank',
                               rank_title=_('DRIVERS rank by olympic mode'),
                               *args, **kwargs)


def team_olympic_view(request, *args, **kwargs):
    return common_olympic_view(request,
                               tpl='driver27/team/list.html',
                               olympic_method='team_olympic_rank',
                               rank_title=_('TEAMS rank by olympic mode'),
                               *args, **kwargs)

def driver_season_pos_view(request, competition_slug, year):
    season = get_object_or_404(Season, competition__slug=competition_slug, year=year)
    # rank = season.get_positions_draw()
    rank_title = 'POSITION draw'
    title = u'{season} [{title}]'.format(season=season,
                                         title=rank_title)
    context = {
        'season': season,
        'title': title,
        'positions': list(season.past_races.values_list('round', flat=True)),
        'olympic': True}
    return render(request, 'driver27/driver/list.html', context)


def race_list(request, competition_slug, year):
    season = get_object_or_404(Season, competition__slug=competition_slug, year=year)
    races = season.races.all()
    title = _('%(season)s [RACES]') % {'season': season}
    context = {'races': races, 'season': season, 'title': title}
    tpl = 'driver27/race/list.html'
    return render(request, tpl, context)


def race_view(request, competition_slug, year, race_id=None):
    race = get_object_or_404(Race, season__competition__slug=competition_slug, season__year=year, round=race_id)
    results = race.results.all() \
        .annotate(null_position=Count('finish')).order_by('-null_position', 'finish', 'qualifying')
    title = _('Results of %(race)s') % {'race': race}
    context = {'race': race, 'season': race.season, 'title': title, 'results': results}
    tpl = 'driver27/race/view.html'
    return render(request, tpl, context)


def get_safe_record_config(record):
    record_config = get_record_config(record)
    if record_config:
        return record_config
    else:
        raise Http404(_('Record does not exist'))

@competition_request
def get_record_common_context(request, context, record=None, *args, **kwargs):
    season_or_competition = context.get('season_or_competition')

    context.update(record=record)
    if record:
        record_config = get_safe_record_config(record)
        record_label = record_config.get('label')
        title = _('%(record_label)s Record, %(season_or_competition)s') \
                % {'record_label': record_label, 'season_or_competition': season_or_competition}
        context['record_filter'] = record_config.get('filter')
    else:
        title = _('Select a %(season_or_competition)s record') % {'season_or_competition': season_or_competition}

    context['title'] = title
    context.pop('record_filter', None)
    context['record_codes'] = get_record_label_dict()
    return context

def driver_record_view(request, *args, **kwargs):
    context = get_record_common_context(request, *args, **kwargs)
    tpl = 'driver27/driver/record.html'
    return render(request, tpl, context)



def team_record_view(request, rank_type='STATS', *args, **kwargs):
    context = get_record_common_context(request, *args, **kwargs)
    context['rank_opt'] = rank_type
    context['doubles_record_codes'] = [double_code for double_code, double_label in get_record_label_dict(doubles=True)]
    tpl = 'driver27/team/record.html'
    return render(request, tpl, context)


def driver_profile_view(request, driver_id):
    driver = get_object_or_404(Driver, pk=driver_id)
    by_season = driver.get_stats_by_season(append_points=True)
    by_competition = driver.get_stats_by_competition(append_points=True)
    context = {
        'driver': driver,
        'by_season': by_season,
        'by_competition': by_competition,
        'results': get_tuples_from_results(driver.get_results()),
        'stats': driver.get_stats_list(append_points=True),
        'title': 'Profile of {driver}'.format(driver=driver)
    }
    tpl = 'driver27/driver/profile.html'
    return render(request, tpl, context)


def team_profile_view(request, team_id):
    team = get_object_or_404(Team, pk=team_id)
    by_season = team.get_stats_by_season(append_points=True)
    by_competition = team.get_stats_by_competition(append_points=True)
    context = {
        'team': team,
        'by_season': by_season,
        'by_competition': by_competition,
        'stats': team.get_stats_list(append_points=True),
        'title': 'Profile of {team}'.format(team=team)
    }
    tpl = 'driver27/team/profile.html'
    return render(request, tpl, context)

