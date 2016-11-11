from django import template
from ..models import Season
register = template.Library()

@register.filter
def champion_filter(season_id):
    season = Season.objects.get(pk=season_id)
    return '<span class="champion_tag">&#9818;</span>' if season.has_champion() else ''