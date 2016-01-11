# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):
    dependencies = [
        ('rw', '0015_project_out_of_range_distance'),
    ]

    operations = [
        migrations.RunSQL(
                "UPDATE rw_speaker SET shape = ST_Multi(ST_Buffer(ST_MakePoint(longitude, latitude)::geography, maxdistance)::geometry)::geography;"
        )
    ]
