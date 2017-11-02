# -*- coding: utf-8 -*-
from django import template
from ..models import Season, Race
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
def order_results(value, arg):
    return sorted(value, key=lambda x: (getattr(x, arg)<1, getattr(x, arg)))

@register.filter
def print_pos(pos):
    if pos:
        str_pos = u'{pos}º'.format(pos=pos)
        if pos == 1:
            str_pos = '<strong>' + str_pos + '</strong>'
    else:
        str_pos = u''
    return str_pos

@register.filter
def race_url(race_id):
    race = Race.objects.get(pk=race_id)
    return race.get_absolute_url()