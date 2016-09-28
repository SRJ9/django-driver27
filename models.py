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
    competitions = models.ManyToManyField('Competition', through='DriverCompetition')

    def save(self, *args, **kwargs):
        if self.year_of_birth < 1900 or self.year_of_birth > 2099:
            raise ValidationError('Year_of_birth must be between 1900 and 2099')
        super(Driver, self).save(*args, **kwargs)

    def __unicode__(self):
        return ', '.join((self.last_name, self.first_name))

    class Meta:
        unique_together = ('last_name', 'first_name')

class DriverCompetitionTeam(models.Model):
    team = models.ForeignKey('Team')
    driver_competition = models.ForeignKey('DriverCompetition')
    current = models.BooleanField(default=False)

    def __unicode__(self):
        return '%s %s %s' % (self.driver_competition.driver, 'in', self.team)

    class Meta:
        unique_together = [('team', 'driver_competition'), ('driver_competition', 'current')]

class DriverCompetition(models.Model):
    driver = models.ForeignKey(Driver)
    competition = models.ForeignKey('Competition')
    teams = models.ManyToManyField('Team', through='DriverCompetitionTeam')

    @property
    def teams_verbose(self):
        teams = self.teams
        if teams.count():
            return ', '.join([team.name for team in teams.all()])
        else:
            return None

    def __unicode__(self):
        return '%s %s %s' % (self.driver, 'in', self.competition)

    class Meta:
        unique_together = ('driver', 'competition')


class Team(models.Model):
    name = models.CharField(max_length=75, verbose_name='team')
    full_name = models.CharField(max_length=200)
    competitions = models.ManyToManyField('Competition')
    country = CountryField()

    def __unicode__(self):
        return self.name

class Competition(models.Model):
    name = models.CharField(max_length=30, verbose_name='competition')
    full_name = models.CharField(max_length=100)
    country = CountryField(null=True, blank=True, default=None)

    def __unicode__(self):
        return self.name

class Circuit(models.Model):
    name = models.CharField(max_length=30, verbose_name='circuit')
    city = models.CharField(max_length=100, null=True, blank=True)
    country = CountryField()
    opened_in = models.IntegerField()

    # @todo Add Clockwise and length
    def __unicode__(self):
        # @todo Add country name in __unicode__
        return self.name

class GrandPrix(models.Model):
    name = models.CharField(max_length=30, verbose_name='grand prix')
    country = CountryField(null=True, blank=True, default=None)
    first_held = models.IntegerField(null=True, blank=True)
    default_circuit = models.ForeignKey(Circuit, related_name='default_to_grands_prix', null=True, blank=True, default=None)
    competitions = models.ManyToManyField('Competition', related_name='grands_prix', default=None)

    def __unicode__(self):
        return self.name


class Season(models.Model):
    year = models.IntegerField()
    competition = models.ForeignKey(Competition, related_name='seasons')
    teams = models.ManyToManyField(Team, related_name='seasons', through='TeamSeasonRel')

    def __unicode__(self):
        return '/'.join((self.competition.name, str(self.year)))

    class Meta:
        unique_together = ('year', 'competition')



class TeamSeasonRel(models.Model):
    season = models.ForeignKey('Season')
    team = models.ForeignKey('Team')
    sponsor_name = models.CharField(max_length=75)

    def save(self, *args, **kwargs):
        if self.season.competition not in self.team.competitions.all():
            raise ValidationError('Team ' + str(self.team) + ' doesn\'t participate in '+str(self.season.competition))
        super(TeamSeasonRel, self).save(*args, **kwargs)




