# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('rw', '0014_specify_multipoly_shape_add_atten_border'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='out_of_range_distance',
            field=models.FloatField(default=1000),
            preserve_default=True,
        ),
    ]
