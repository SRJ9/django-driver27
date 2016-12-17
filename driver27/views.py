from django.shortcuts import render
from django.db.models import Count
from django.http import Http404
from django.utils.translation import ugettext as _
from .models import Competition, Season, Race
from .punctuation import DRIVER27_PUNCTUATION
from .record_filters import DR27_RECORDS_FILTER


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

        title = '%s' % competition_obj
        context = {'competition': competition_obj, 'title': title}
        tpl = 'driver27/competition-view.html'
    else:
        competitions = Competition.objects.all()
        title = _('Competitions')
        context = {'competitions': competitions, 'title': title}
        tpl = 'driver27/competition-list.html'
    return render(request, tpl, context)


def season_view(request, competition_slug, year):
    season = get_season(competition_slug, year)
    title = '%s/%d' % (season.competition, season.year)
    driver_rank = season.points_rank()[:5]
    team_rank = season.team_points_rank()[:5]
    context = {'season': season, 'title': title, 'driver_rank': driver_rank, 'team_rank': team_rank}
    tpl = 'driver27/season-view.html'
    return render(request, tpl, context)


def _rank_view(request, competition_slug, year, type='driver'):
    season = get_season(competition_slug, year)
    access_to_road = False
    has_champion = False
    scoring = [(punctuation['label'], punctuation['code']) for punctuation in DRIVER27_PUNCTUATION]
    scoring_code = request.POST.get('scoring', season.punctuation)
    if type == 'driver':
        rank = season.points_rank(scoring_code=scoring_code)
        rank_title = _('DRIVERS')
        tpl = 'driver27/driver-list.html'
        has_champion = season.has_champion()
        access_to_road = (not has_champion and season.pending_races() <= 5)
    elif type == 'team':
        rank = season.team_points_rank()
        rank_title = _('TEAMS')
        tpl = 'driver27/team-list.html'
    else:
        raise Http404(_('Impossible rank'))

    title = '%s [%s]' % (season, rank_title)

    context = {'rank': rank,
               'season': season,
               'title': title,
               'access_to_road': access_to_road,
               'has_champion': has_champion,
               'scoring_list': scoring,
               'scoring_code': scoring_code}
    return render(request, tpl, context)


def driver_rank_view(request, competition_slug, year):
    return _rank_view(request, competition_slug, year, type='driver')


def driver_olympic_view(request, competition_slug, year):
    season = get_season(competition_slug, year)
    rank = season.olympic_rank()
    rank_title = _('DRIVERS rank by olympic mode')
    tpl = 'driver27/driver-list.html'

    title = '%s [%s]' % (season, rank_title)

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
        tpl = 'driver27/driver-list.html'

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
    return _rank_view(request, competition_slug, year, type='team')


def race_list(request, competition_slug, year):
    season = get_season(competition_slug, year)
    races = season.races.all().order_by('round')
    title = _('%(season)s [RACES]') % {'season': season}
    context = {'races': races, 'season': season, 'title': title}
    tpl = 'driver27/race-list.html'
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
    tpl = 'driver27/race-view.html'
    return render(request, tpl, context)


def get_record_config(record):
    for record_config in DR27_RECORDS_FILTER:
        if record_config['code'] == record:
            return record_config
    raise Http404(_('Record does not exist'))


def get_record_common_context(request, competition_slug, year, record=None):
    season = get_season(competition_slug, year)
    if record:
        record_config = get_record_config(record)
        title = _('%(record_label)s Record, %(season)s') \
            % {'record_label': record_config['label'], 'season': season}
    else:
        title = _('Select a %(season)s record' % {'season': season})

    context = {
               'season': season,
               'title': title,
               'record': record,
               'record_codes': DR27_RECORDS_FILTER
               }

    return context


def driver_record_view(request, competition_slug, year, record=None):
    context = get_record_common_context(request, competition_slug, year, record)

    if record:
        season = context.get('season', None)
        record_config = get_record_config(record)
        rank = season.stats_rank(**record_config['filter']) if record_config else None
    else:
        rank = None
    context['rank'] = rank
    tpl = 'driver27/driver-record.html'
    return render(request, tpl, context)


def team_record_by_race_view(request, competition_slug, year, record=None):
    return team_record_view(request, competition_slug, year, record=record, unique_by_race=True)


def team_record_view(request, competition_slug, year, record=None, unique_by_race=False):
    context = get_record_common_context(request, competition_slug, year, record)

    if record:
        season = context.get('season', None)
        record_config = get_record_config(record)
        rank = season.team_stats_rank(unique_by_race=unique_by_race, **record_config['filter']) \
            if record_config else None
    else:
        rank = None
    context['rank'] = rank
    context['by_race'] = bool(unique_by_race)
    tpl = 'driver27/team-record.html'
    return render(request, tpl, context)

