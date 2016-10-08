from django.shortcuts import render
from .models import Competition, Season


def get_season(slug, year):
    return Season.objects.get(year=year, competition__slug=slug)

def competition_view(request, competition_slug=None):
    if competition_slug is not None:
        competition_obj = Competition.objects.get(slug=competition_slug)
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


def driver_view(request, competition_slug, year):
    season = get_season(competition_slug, year)
    rank = season.points_rank()
    title = '%s [DRIVERS]' % season
    context = {'rank': rank, 'season': season, 'title': title}
    tpl = 'driver27/driver-list.html'
    return render(request, tpl, context)


def team_view(request, competition_slug, year):
    season = get_season(competition_slug, year)
    rank = season.team_points_rank()
    title = '%s [TEAMS]' % season
    context = {'rank': rank, 'season': season, 'title': title}
    tpl = 'driver27/team-list.html'
    return render(request, tpl, context)


def race_list(request, competition_slug, year):
    season = get_season(competition_slug, year)
    races = season.races.all().order_by('round')
    title = '%s [RACES]' % season
    context = {'races': races, 'season': season, 'title': title}
    tpl = 'driver27/race-list.html'
    return render(request, tpl, context)


def race_view(request, competition_slug, year, race_id=None):
    season = get_season(competition_slug, year)
    race = season.races.get(round=race_id)
    results = race.results.all().order_by('finish', 'qualifying')
    title = 'Results of %s' % race
    context = {'race': race, 'season': season, 'title': title, 'results': results}
    tpl = 'driver27/race-view.html'
    return render(request, tpl, context)