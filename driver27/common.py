from django.shortcuts import render, get_object_or_404

DRIVER27_NAMESPACE = 'driver27'
DRIVER27_API_NAMESPACE = 'api'

def ordered_position(result, pos):
    position = getattr(result, pos, None)
    if position is None or 0 >= position:
        position = float('inf')
    return position
