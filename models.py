from __future__ import unicode_literals

import datetime
from django.db import models
try:
    from django_countries.fields import CountryField
except ImportError:
    raise ImportError(
        'You are using the `driver27` app which requires the `django-countries` module.'
        'Be sure to add `django_countries` to your INSTALLED_APPS for `driver27` to work properly.'
    )

# large list to historical drivers.
# Starts in 1911, Fangio's year of birth

class Driver(models.Model):
    last_name = models.CharField(max_length=50)
    first_name = models.CharField(max_length=25)
    year_of_birth = models.IntegerField()
    country = CountryField()

    def __unicode__(self):
        return ', '.join((self.last_name, self.first_name))

    class Meta:
        unique_together = ('last_name', 'first_name')


# Create your models here.
