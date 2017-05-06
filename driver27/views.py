# -*- coding: utf-8 -*-
from django.db.models import Count
from django.http import Http404
from django.shortcuts import render
from django.utils.translation import ugettext as _

from .models import Competition, Season, Race
from .records import get_record_config, get_record_label_dict
from .punctuation import get_punctuation_config, get_punctuation_label_dict


def get_or_404(cls, conditions, raise_text):
    try:
        obj = cls.objects.get(**conditions)
    except cls.DoesNotExist:
        raise Http404(raise_text)
    return obj


def get_season(slug, year):
    return get_or_404(Season, {'year': year, 'competition__slug': slug}, _('Season does not exist'))


def get_competition(slug):
    return get_or_404(Competition, {'slug': slug}, _('Competition does not exist'))


def get_season_or_competition(slug, year=None):
    if year:
        return get_season(slug, year)
    else:
        return get_competition(slug)


def competition_view(request, competition_slug=None):
    if competition_slug is not None:
        competition_obj = get_competition(slug=competition_slug)
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
    driver_rank = season.points_rank()
    team_rank = season.team_points_rank()
    title = '{competition}/{year:d}'.format(competition=season.competition, year=season.year)
    context = {'season': season, 'title': title, 'driver_rank': driver_rank, 'team_rank': team_rank}
    tpl = 'driver27/season/season-view.html'
    return render(request, tpl, context)


def split_season_and_competition(season_or_competition):
    # if season_or_competition does not have 'competition' attr, season_or_competition is competition
    if hasattr(season_or_competition, 'competition'):
        season = season_or_competition
        competition = season.competition
    else:
        season = None
        competition = season_or_competition
    return season, competition


def _rank_view(request, competition_slug, year, rank_model='driver'):
    season_or_competition = get_season_or_competition(competition_slug, year)
    season, competition = split_season_and_competition(season_or_competition)
    default_punctuation = getattr(season_or_competition, 'punctuation', None)
    scoring_code = request.POST.get('scoring', default_punctuation)

    has_champion = access_to_road = False
    punctuation_selector = get_punctuation_label_dict()
    if rank_model == 'driver':
        rank = season_or_competition.points_rank(punctuation_code=scoring_code)
        if hasattr(season_or_competition, 'has_champion'):
            has_champion = season_or_competition.has_champion(punctuation_code=scoring_code)
            access_to_road = (not has_champion)
        rank_title = _('DRIVERS')
        tpl = 'driver27/driver/driver-list.html'
    elif rank_model == 'team':
        rank = season_or_competition.team_points_rank(punctuation_code=scoring_code)
        rank_title = _('TEAMS')
        tpl = 'driver27/team/team-list.html'
    else:
        raise Http404(_('Impossible rank'))

    title = u'{season_or_competition} [{title}]'.format(season_or_competition=season_or_competition,
                                                            title=rank_title)

    context = {'rank': rank,
               'season': season,
               'competition': competition,
               'title': title,
               'access_to_road': access_to_road,
               'has_champion': has_champion,
               'scoring_list': punctuation_selector,
               'scoring_code': scoring_code}

    return render(request, tpl, context)


def driver_rank_view(request, competition_slug, year=None):
    return _rank_view(request, competition_slug, year, rank_model='driver')


def driver_olympic_view(request, competition_slug, year):
    season = get_season(competition_slug, year)
    rank = season.olympic_rank()
    rank_title = _('DRIVERS rank by olympic mode')
    tpl = 'driver27/driver/driver-list.html'

    title = u'{season} [{title}]'.format(season=season, title=rank_title)

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
        road_rank = season.only_title_contenders()
        punctuation_config = season.get_punctuation_config()
        title = _('%(season)s - Road to the championship') % {'season': season}
        tpl = 'driver27/driver/driver-list.html'

        context = {'rank': road_rank,
                   'season': season,
                   'title': title,
                   'scoring': punctuation_config.get('finish'),
                   'pending_races': range(1, pending_races+1),
                   'road_to_championship': True}
    else:
        raise Http404(_('%(leader)s is the Champion!') % {'leader': season.leader[1]})
    return render(request, tpl, context)


def team_rank_view(request, competition_slug, year=None):
    return _rank_view(request, competition_slug, year, rank_model='team')


def race_list(request, competition_slug, year):
    season = get_season(competition_slug, year)
    races = season.races.all()
    title = _('%(season)s [RACES]') % {'season': season}
    context = {'races': races, 'season': season, 'title': title}
    tpl = 'driver27/race/race-list.html'
    return render(request, tpl, context)


def race_view(request, competition_slug, year, race_id=None):
    season = get_season(competition_slug, year)
    race = get_or_404(Race, {'season': season.pk, 'round': race_id}, _('Race does not exist'))
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
    season_or_competition = get_season_or_competition(competition_slug, year)
    season, competition = split_season_and_competition(season_or_competition)

    context = {
        'season_or_competition': season_or_competition,
        'season': season,
        'competition': competition,
        'record': record,
    }
    if record:
        record_config = get_safe_record_config(record)
        record_label = record_config.get('label')
        title = _('%(record_label)s Record, %(season_or_competition)s') \
            % {'record_label': record_label, 'season_or_competition': season_or_competition}
        context['record_filter'] = record_config.get('filter')
    else:
        title = _('Select a %(season_or_competition)s record') % {'season_or_competition': season_or_competition}

    context['title'] = title
    context['record_codes'] = get_record_label_dict()
    return context


def driver_record_view(request, competition_slug, year=None, record=None):
    context = get_record_common_context(request, competition_slug, year, record)
    rank = None
    season_or_competition = context.get('season_or_competition')
    if record:
        rank = season_or_competition.stats_rank(**context.get('record_filter')) if 'record_filter' in context else None
    context.pop('record_filter', None)
    context['rank'] = rank
    tpl = 'driver27/driver/driver-record.html'
    return render(request, tpl, context)


def driver_streak_view(request, competition_slug, year=None, record=None):
    context = get_record_common_context(request, competition_slug, year, record)
    rank = None
    season_or_competition = context.get('season_or_competition')
    if record:
        rank = season_or_competition.streak_rank(**context.get('record_filter')) if 'record_filter' in context else None
    context.pop('record_filter', None)
    context['rank'] = rank
    context['streak'] = True
    tpl = 'driver27/driver/driver-record.html'
    return render(request, tpl, context)


def team_record_doubles_view(request, competition_slug, year=None, record=None):
    return team_record_view(request, competition_slug, year, record=record, rank_type='DOUBLES')


def team_record_races_view(request, competition_slug, year=None, record=None):
    return team_record_view(request, competition_slug, year, record=record, rank_type='RACES')


def team_record_stats_view(request, competition_slug, year=None, record=None):
    return team_record_view(request, competition_slug, year, record=record, rank_type='STATS')


def team_record_view(request, competition_slug, year, rank_type, record=None):
    context = get_record_common_context(request, competition_slug, year, record)

    rank = None
    season_or_competition = context.get('season_or_competition')
    if record:
        rank = season_or_competition.get_team_rank(rank_type, **context.get('record_filter')) if 'record_filter' in context else None
    context['rank'] = rank
    context['rank_type'] = rank_type
    context['doubles_record_codes'] = get_record_label_dict(doubles=True)
    # context['races'] = (rank_type in ('RACES', 'RACES-DOUBLES'))
    tpl = 'driver27/team/team-record.html'
    return render(request, tpl, context)

