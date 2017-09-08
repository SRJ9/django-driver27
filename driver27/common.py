from django.shortcuts import render, get_object_or_404

DRIVER27_NAMESPACE = 'driver27'
DRIVER27_API_NAMESPACE = 'api'

def get_season_or_competition(slug=None, year=None):
    from .models import Season, Competition, RankModel
    if slug:
        if year:
            return get_object_or_404(Season, competition__slug=slug, year=year)
        else:
            return get_object_or_404(Competition, slug=slug)
    else:
        return RankModel()

def split_season_and_competition(season_or_competition):
    season = None
    competition = None
    # if season_or_competition does not have 'competition' attr, season_or_competition is competition
    if hasattr(season_or_competition, 'competition'):
        season = season_or_competition
        competition = season.competition
    elif hasattr(season_or_competition, 'seasons'):
        competition = season_or_competition
    return season, competition