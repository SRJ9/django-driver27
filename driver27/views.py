from django.shortcuts import render
from django.db.models import Count
from django.http import Http404
from .models import Competition, Season, Race


def get_season(slug, year):
    try:
        season = Season.objects.get(year=year, competition__slug=slug)
    except Season.DoesNotExist:
        raise Http404('Season does not exist')
    return season

def competition_view(request, competition_slug=None):
    if competition_slug is not None:
        try:
            competition_obj = Competition.objects.get(slug=competition_slug)
        except Competition.DoesNotExist:
            raise Http404('Competition does not exist')

        title = '%s' % competition_obj
        context = {'competition': competition_obj, 'title': title}
        tpl = 'driver27/competition-view.html'
    else:
        competitions = Competition.objects.all()
        title = 'Competitions'
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
    if type == 'driver':
        rank = season.points_rank()
        rank_title = 'DRIVERS'
        tpl = 'driver27/driver-list.html'
    elif type == 'team':
        rank = season.team_points_rank()
        rank_title = 'TEAMS'
        tpl = 'driver27/team-list.html'
    else:
        raise Http404('Impossible rank')
    title = '%s [%s]' % (season, rank_title)

    context = {'rank': rank, 'season': season, 'title': title}
    return render(request, tpl, context)

def driver_rank_view(request, competition_slug, year):
    return _rank_view(request, competition_slug, year, type='driver')


def team_rank_view(request, competition_slug, year):
    return _rank_view(request, competition_slug, year, type='team')


def race_list(request, competition_slug, year):
    season = get_season(competition_slug, year)
    races = season.races.all().order_by('round')
    title = '%s [RACES]' % season
    context = {'races': races, 'season': season, 'title': title}
    tpl = 'driver27/race-list.html'
    return render(request, tpl, context)


def race_view(request, competition_slug, year, race_id=None):
    season = get_season(competition_slug, year)
    try:
        race = season.races.get(round=race_id)
    except Race.DoesNotExist:
        raise Http404('Race does not exist')
    results = race.results.all()\
        .annotate(null_position=Count('finish')).order_by('-null_position', 'finish', 'qualifying')
    title = 'Results of %s' % race
    context = {'race': race, 'season': season, 'title': title, 'results': results}
    tpl = 'driver27/race-view.html'
    return render(request, tpl, context)