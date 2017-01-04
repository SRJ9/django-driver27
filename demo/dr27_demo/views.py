from django.shortcuts import redirect


def index(request):
    return redirect('dr27-competition-list')

