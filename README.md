[![Build Status](https://travis-ci.org/SRJ9/django-driver27.svg?branch=develop)](https://travis-ci.org/SRJ9/django-driver27)
[![codecov](https://codecov.io/gh/SRJ9/django-driver27/branch/develop/graph/badge.svg)](https://codecov.io/gh/SRJ9/django-driver27)
[![Code Climate](https://codeclimate.com/github/SRJ9/django-driver27/badges/gpa.svg)](https://codeclimate.com/github/SRJ9/django-driver27)
[![Requirements Status](https://requires.io/github/SRJ9/django-driver27/requirements.svg?branch=develop)](https://requires.io/github/SRJ9/django-driver27/requirements/?branch=develop)

# driver27
Racing competition manager in Django where you can manage different
motor competitions with its own punctuation rules, races, drivers, teams
which, at the same time, can be part of multiple competitions.

Modify your settings.py
=======================
```
INSTALLED_APPS = [
    'bootstrap3',
...
    'django_countries',
    'tabbed_admin',
    'driver27'
]


TABBED_ADMIN_USE_JQUERY_UI = True
```

Versions
========
- 0.14-ALO (Fernando Alonso 14)
- 0.27-VIL (Gilles Villeneuve 27)

0.14
====
- Initial models
- Basic relation restriction with exceptions and tests
- Basic templates to frontend views
- Basic demo to test the app

models
===========
- Driver
- Team
- Circuit
- Grand Prix
- Competition
- Season
- Race
- Result
- Contender (Driver/Competition relation)
- Seat (Contender/Team relation)
- fixtures folder contains fixture of each model to demo project.

Demo
====
```bash
$ git clone https://github.com/SRJ9/django-driver27
$ cd django-driver27 # or name of destiny folder
$ python demo/manage.py runserver
$ # login /admin: admin:pass
```

Todo
====
- [ ] Add records by season, driver, team, competition
- [ ] Add drivers profile with records, last_wins, teams...
- [ ] Add easy clone to Season
- [ ] Translate
- [ ] 1980's punctuation. Only 11 best results.
- [ ] Old punctuation. Split season races, and get only 4 of each half.

# History
Driver 27 is a reference to car number of Gilles Villeneuve, F1 Driver died in 1982. Gilles is considered one of best driver despite he never won the World Championship, something that Jacques Villeneuve, his son, did in 1998.

In 1980's decade, F1 teams kept their numbers unless they were champions. This made Ferrari, the most legendary team of the F1, take that number for many years (1981-1995), making the number an icon of this sport.
