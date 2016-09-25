from __future__ import unicode_literals

import datetime
from django.db import models
from django.core.exceptions import ValidationError

try:
    from django_countries.fields import CountryField
except ImportError:
    raise ImportError(
        'You are using the `driver27` app which requires the `django-countries` module.'
        'Be sure to add `django_countries` to your INSTALLED_APPS for `driver27` to work properly.'
    )

class Driver(models.Model):
    last_name = models.CharField(max_length=50)
    first_name = models.CharField(max_length=25)
    year_of_birth = models.IntegerField()
    country = CountryField()

    def save(self, *args, **kwargs):
        if self.year_of_birth < 1900 or self.year_of_birth > 2099:
            raise ValidationError('Year_of_birth must be between 1900 and 2099')
        super(Driver, self).save(*args, **kwargs)

    def __unicode__(self):
        return ', '.join((self.last_name, self.first_name))

    class Meta:
        unique_together = ('last_name', 'first_name')


class Team(models.Model):
    name = models.CharField(max_length=75)
    full_name = models.CharField(max_length=200)
    country = CountryField()

    def __unicode__(self):
        return self.name

class Competition(models.Model):
    name = models.CharField(max_length=30)
    full_name = models.CharField(max_length=100)
    country = CountryField(null=True, blank=True, default=None)

    def __unicode__(self):
        return self.name

class Circuit(models.Model):
    name = models.CharField(max_length=30)
    city = models.CharField(max_length=100, null=True, blank=True)
    country = CountryField()
    year_of_built = models.IntegerField()

    def __unicode__(self):
        # @todo Add country name in __unicode__
        return self.name

class Season(models.Model):
    year = models.IntegerField()
    competition = models.ForeignKey(Competition, related_name='seasons')
    teams = models.ManyToManyField(Team, related_name='seasons')

    class Meta:
        unique_together = ('year', 'competition')

    def __unicode__(self):
        return '/'.join((self.competition.name, str(self.year)))



