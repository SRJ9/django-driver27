from django.shortcuts import render, get_object_or_404


def competition_request(f):
    def wrap(request, *args, **kwargs):
        if request.is_ajax():
            slug = request.GET.get('competition_slug', None)
            year = request.GET.get('year', None)
        else:
            slug = kwargs.pop('competition_slug', None)
            year = kwargs.pop('year', None)

        from .models import Season, Competition, RankModel
        season = competition = None
        if slug:
            if year:
                season_or_competition = get_object_or_404(Season, competition__slug=slug, year=year)
                season = season_or_competition
                competition = season.competition
            else:
                season_or_competition = get_object_or_404(Competition, slug=slug)
                competition = season_or_competition
        else:
            season_or_competition = RankModel()

        context = kwargs.setdefault('context', {})
        context.update(season=season, competition=competition, season_or_competition=season_or_competition)
        kwargs['context'] = context
        return f(request, *args, **kwargs)

    wrap.__doc__ = f.__doc__
    wrap.__name__ = f.__name__
    return wrap
