from django import template
from ..models import Season
register = template.Library()

@register.filter
def champion_filter(season_id):
    season = Season.objects.get(pk=season_id)
    return '&#9818;' if season.has_champion() else ''