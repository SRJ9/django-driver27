# -*- coding: utf-8 -*-
from django.http import Http404
from django.shortcuts import render
from django.utils.translation import ugettext as _

try:
    from django.urls import reverse
except ImportError:
    from django.core.urlresolvers import reverse

from .decorators import competition_request
from .records import get_record_config

def get_safe_record_config(record):
    record_config = get_record_config(record)
    if record_config:
        return record_config
    else:
        raise Http404(_('Record does not exist'))

@competition_request
def standing_view(request, context):
    season_or_competition = context.get('season_or_competition')

    # driver/team olympic/common
    standing_model = request.GET.get('model', 'driver')
    if standing_model not in ['driver', 'team']:
        raise Http404(_('The standing requested is invalid'))

    olympic = request.GET.get('olympic', False)
    if olympic:
        standing_type = suffix_tpl = 'olympic'
    else:
        standing_type = 'common'
        suffix_tpl = 'table'

    standing_method = {
        'driver': {'olympic': 'olympic_rank', 'common': 'points_rank'},
        'team': {'olympic': 'team_olympic_rank','common': 'team_points_rank'}
    }.get(standing_model)[standing_type]


    # kwargs to rank
    by_season = request.GET.get('by_season', False)
    punctuation_code = request.GET.get('punctuation', None)


    standing_kwargs = {}
    if not olympic:
        standing_kwargs.update(punctuation_code=punctuation_code, by_season=by_season)

    rank = getattr(season_or_competition, standing_method)(**standing_kwargs)
    tpl = 'driver27/' + standing_model + '/list-'+suffix_tpl + '.html'

    context.update(rank=rank, by_season=by_season)

    return render(request, tpl, context)

@competition_request
def stats_view(request, context):
    season_or_competition = context.get('season_or_competition')

    record = request.GET.get('record', None)
    record_config = get_safe_record_config(record)

    standing_model = request.GET.get('model', 'driver')

    if standing_model not in ['driver', 'team']:
        raise Http404(_('The standing requested is invalid'))

    rank_opt = request.GET.get('rank_opt', None)
    rank = None
    tpl = 'driver27/' + standing_model + '/record-table.html'
    if record:
        record_filter = record_config.get('filter')
        if rank_opt:
            if rank_opt == 'seasons':
                rank = stats_by_season_view(season_or_competition, standing_model, record_filter)
                context.update(rank_opt='seasons')
            else:
                rank = stats_by_streak_view(season_or_competition, standing_model, record_filter, rank_opt)
        else:
            rank = season_or_competition.stats_rank(**record_filter)

    context.update(rank=rank)
    return render(request, tpl, context)


def stats_by_streak_view(season_or_competition, standing_model, record_filter, rank_opt):
    streak_method = {
        'team': 'streak_team_rank',
        'driver': 'streak_rank'
    }.get(standing_model)
    rank_kwargs_by_opt = {
        'streak': {},
        'streak_top': {'max_streak': True},
        'streak_actives': {'only_actives': True},
        'streak_top_actives': {'only_actives': True, 'max_streak': True}
    }
    rank_kwargs = rank_kwargs_by_opt.get(rank_opt, {})
    record_filter.update(**rank_kwargs)
    rank = getattr(season_or_competition, streak_method)(**record_filter)
    return rank


def stats_by_season_view(season_or_competition, standing_model, record_filter):
    seasons_method = {
        'team': 'seasons_team_rank',
        'driver': 'seasons_rank'
    }.get(standing_model)
    rank = getattr(season_or_competition, seasons_method)(**record_filter)
    return rank