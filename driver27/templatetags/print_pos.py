# -*- coding: utf-8 -*-
from django import template
register = template.Library()

@register.filter
def print_pos(pos):
    if pos:
        str_pos = u'{pos}º'.format(pos=pos)
        if pos == 1:
            str_pos = '<strong>' + str_pos + '</strong>'
    else:
        str_pos = u''
    return str_pos
