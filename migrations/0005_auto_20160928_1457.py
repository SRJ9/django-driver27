# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2016-09-28 14:57
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('driver27', '0004_auto_20160928_1348'),
    ]

    operations = [
        migrations.CreateModel(
            name='DriverCompetition',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('competition', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='driver27.Competition')),
                ('driver', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='driver27.Driver')),
            ],
        ),
        migrations.CreateModel(
            name='DriverCompetitionTeam',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('current', models.BooleanField(default=False)),
                ('driver_competition', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='driver27.DriverCompetition')),
                ('team', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='driver27.Team')),
            ],
        ),
        migrations.AddField(
            model_name='drivercompetition',
            name='teams',
            field=models.ManyToManyField(through='driver27.DriverCompetitionTeam', to='driver27.Team'),
        ),
        migrations.AddField(
            model_name='driver',
            name='competitions',
            field=models.ManyToManyField(through='driver27.DriverCompetition', to='driver27.Competition'),
        ),
        migrations.AlterUniqueTogether(
            name='drivercompetitionteam',
            unique_together=set([('team', 'driver_competition'), ('driver_competition', 'current')]),
        ),
        migrations.AlterUniqueTogether(
            name='drivercompetition',
            unique_together=set([('driver', 'competition')]),
        ),
    ]
