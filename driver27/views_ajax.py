# -*- coding: utf-8 -*-
from django.http import Http404
from django.shortcuts import render
from django.utils.translation import ugettext as _

try:
    from django.urls import reverse
except ImportError:
    from django.core.urlresolvers import reverse

from .decorators import competition_request

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
        'driver': {
            'olympic': 'olympic_rank',
            'common': 'points_rank'
        },
        'team': {
            'olympic': 'team_olympic_rank',
            'common': 'team_points_rank'
        }
    }.get(standing_model)[standing_type]


    # kwargs to rank
    by_season = request.GET.get('by_season', False)
    punctuation_code = request.GET.get('punctuation', None)


    standing_kwargs = {}
    if not olympic:
        standing_kwargs.update(punctuation_code=punctuation_code, by_season=by_season)

    rank = getattr(season_or_competition, standing_method)(**standing_kwargs)
    tpl = 'driver27/' + standing_model + '/' + standing_model + '-list-'+suffix_tpl + '.html'

    context.update(rank=rank, by_season=by_season)

    return render(request, tpl, context)
