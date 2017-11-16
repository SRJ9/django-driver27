# -*- coding: utf-8 -*-
from django import template
from ..models import Season, Race
from ..common import ordered_position
register = template.Library()

@register.filter
def champion_filter(season_id):
    if season_id:
        season = Season.objects.get(pk=season_id)
        return '<span class="champion_tag">&#9818;</span>' if season.has_champion() else ''
    else:
        return ''

@register.filter(is_safe=False)
def get_attribute(obj, attr):
    if attr is None:
        return None
    return getattr(obj, attr)

@register.filter(is_safe=False)
def order_results(results, pos_key):
    return sorted(results, key=lambda result: (ordered_position(result, pos_key)))

@register.filter
def print_pos(pos):
    str_pos = u''
    if pos:
        str_pos = u'{pos}º'.format(pos=pos)
        if pos == 1:
            str_pos = u'<strong>{0}</strong>'.format(str_pos)
    return str_pos

@register.filter
def race_url(race_id):
    race = Race.objects.get(pk=race_id)
    return race.get_absolute_url()
