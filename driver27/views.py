from django.db.models import Count
from django.http import Http404
from django.shortcuts import render
from django.utils.translation import ugettext as _

from .models import Competition, Season, Race
from .records import get_record_config, get_record_label_dict
from .punctuation import get_punctuation_label_dict


def get_season(slug, year):
    try:
        season = Season.objects.get(year=year, competition__slug=slug)
    except Season.DoesNotExist:
        raise Http404(_('Season does not exist'))
    return season


def competition_view(request, competition_slug=None):
    if competition_slug is not None:
        try:
            competition_obj = Competition.objects.get(slug=competition_slug)
        except Competition.DoesNotExist:
            raise Http404(_('Competition does not exist'))

        title = '{competition}'.format(competition=competition_obj)
        context = {'competition': competition_obj, 'title': title}
        tpl = 'driver27/competition/competition-view.html'
    else:
        competitions = Competition.objects.all()
        title = _('Competitions')
        context = {'competitions': competitions, 'title': title}
        tpl = 'driver27/competition/competition-list.html'
    return render(request, tpl, context)


def season_view(request, competition_slug, year):
    season = get_season(competition_slug, year)
    title = '{competition}/{year:d}'.format(competition=season.competition, year=season.year)
    driver_rank = season.points_rank()[:5]
    team_rank = season.team_points_rank()[:5]
    context = {'season': season, 'title': title, 'driver_rank': driver_rank, 'team_rank': team_rank}
    tpl = 'driver27/season/season-view.html'
    return render(request, tpl, context)


def _rank_view(request, competition_slug, year, rank_model='driver'):
    season = get_season(competition_slug, year)
    scoring_code = request.POST.get('scoring', season.punctuation)
    has_champion = access_to_road = False
    scoring = get_punctuation_label_dict()
    if rank_model == 'driver':
        rank = season.points_rank(scoring_code=scoring_code)
        rank_title = _('DRIVERS')
        tpl = 'driver27/driver/driver-list.html'
        has_champion = season.has_champion()
        access_to_road = (not has_champion and season.pending_races() <= 5)
    elif rank_model == 'team':
        rank = season.team_points_rank()
        rank_title = _('TEAMS')
        tpl = 'driver27/team/team-list.html'
    else:
        raise Http404(_('Impossible rank'))

    title = '{season} [{title}]'.format(season=season, title=rank_title)

    context = {'rank': rank,
               'season': season,
               'title': title,
               'access_to_road': access_to_road,
               'has_champion': has_champion,
               'scoring_list': scoring,
               'scoring_code': scoring_code}
    return render(request, tpl, context)


def driver_rank_view(request, competition_slug, year):
    return _rank_view(request, competition_slug, year, rank_model='driver')


def driver_olympic_view(request, competition_slug, year):
    season = get_season(competition_slug, year)
    rank = season.olympic_rank()
    rank_title = _('DRIVERS rank by olympic mode')
    tpl = 'driver27/driver/driver-list.html'

    title = '{season} [{title}]'.format(season=season, title=rank_title)

    context = {'rank': rank,
               'season': season,
               'title': title,
               'positions': range(1, 21),
               'olympic': True}
    return render(request, tpl, context)


def driver_road_view(request, competition_slug, year):
    season = get_season(competition_slug, year)
    if not season.has_champion():
        pending_races = season.pending_races()
        pending_points = season.pending_points()
        rank = season.points_rank()
        minimum_points_to_road = season.leader[0] - pending_points
        road_rank = [position for position in rank if minimum_points_to_road <= position[0]]
        scoring = season.get_scoring()
        title = _('%(season)s - Road to the championship') % {'season': season}
        tpl = 'driver27/driver/driver-list.html'

        context = {'rank': road_rank,
                   'season': season,
                   'title': title,
                   'scoring': scoring['finish'],
                   'pending_races': range(1, pending_races+1),
                   'road_to_championship': True}
    else:
        raise Http404(_('%(leader)s is the Champion!') % {'leader': season.leader[1]})
    return render(request, tpl, context)


def team_rank_view(request, competition_slug, year):
    return _rank_view(request, competition_slug, year, rank_model='team')


def race_list(request, competition_slug, year):
    season = get_season(competition_slug, year)
    races = season.races.all().order_by('round')
    title = _('%(season)s [RACES]') % {'season': season}
    context = {'races': races, 'season': season, 'title': title}
    tpl = 'driver27/race/race-list.html'
    return render(request, tpl, context)


def race_view(request, competition_slug, year, race_id=None):
    season = get_season(competition_slug, year)
    try:
        race = season.races.get(round=race_id)
    except Race.DoesNotExist:
        raise Http404(_('Race does not exist'))
    results = race.results.all()\
        .annotate(null_position=Count('finish')).order_by('-null_position', 'finish', 'qualifying')
    title = _('Results of %(race)s') % {'race': race}
    context = {'race': race, 'season': season, 'title': title, 'results': results}
    tpl = 'driver27/race/race-view.html'
    return render(request, tpl, context)


def get_safe_record_config(record):
    record_config = get_record_config(record)
    if record_config:
        return record_config
    else:
        raise Http404(_('Record does not exist'))


def get_record_common_context(request, competition_slug, year, record=None):
    season = get_season(competition_slug, year)
    context = {
        'season': season,
        'record': record,
    }
    if record:
        record_config = get_safe_record_config(record)
        title = _('%(record_label)s Record, %(season)s') \
            % {'record_label': record_config.get('label'), 'season': season}
        context['record_filter'] = record_config.get('filter')
    else:
        title = _('Select a %(season)s record') % {'season': season}

    context['title'] = title
    context['record_codes'] = get_record_label_dict()
    return context


def driver_record_view(request, competition_slug, year, record=None):
    context = get_record_common_context(request, competition_slug, year, record)

    rank = None
    if record:
        season = context.get('season')
        rank = season.stats_rank(**context.get('record_filter')) if 'record_filter' in context else None
    context.pop('record_filter', None)
    context['rank'] = rank
    tpl = 'driver27/driver/driver-record.html'
    return render(request, tpl, context)


def team_record_doubles_view(request, competition_slug, year, record=None):
    return team_record_view(request, competition_slug, year, record=record, rank_type='DOUBLES')


def team_record_races_view(request, competition_slug, year, record=None):
    return team_record_view(request, competition_slug, year, record=record, rank_type='RACES')


def team_record_stats_view(request, competition_slug, year, record=None):
    return team_record_view(request, competition_slug, year, record=record, rank_type='STATS')


def team_record_view(request, competition_slug, year, rank_type, record=None):
    context = get_record_common_context(request, competition_slug, year, record)

    rank = None
    if record:
        season = context.get('season')
        rank = season.get_team_rank(rank_type, **context.get('record_filter')) if 'record_filter' in context else None
    context['rank'] = rank
    context['rank_type'] = rank_type

    context['doubles_record_codes'] = get_record_label_dict(doubles=True)
    # context['races'] = (rank_type in ('RACES', 'RACES-DOUBLES'))
    tpl = 'driver27/team/team-record.html'
    return render(request, tpl, context)

