# -*- coding: utf-8 -*-
from django import template
from ..models import Race
register = template.Library()

@register.filter
def race_url(race_id):
    race = Race.objects.get(pk=race_id)
    return race.get_absolute_url()
