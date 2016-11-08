from django import template
from ..models import Season
register = template.Library()

@register.simple_tag
def champion_tag(season_id):
    season = Season.objects.get(pk=season_id)
    return '&#9818;' if season.has_champion() else ''