# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def save_speakers(apps, schema_editor):
    """save speakers to generate derivative shapes after updating the `shape` attribute
    """
    Speaker = apps.get_model("rw", "Speaker")
    for speaker in Speaker.objects.iterator():
        speaker.save()

class Migration(migrations.Migration):
    dependencies = [
        ('rw', '0013_speaker_geometry'),
    ]

    operations = [
        migrations.RunSQL(
                "UPDATE rw_speaker SET shape = ST_Multi(ST_Buffer(ST_MakePoint(longitude, latitude)::geography, maxdistance)::geometry)::geography;"
        ),
        migrations.RunPython(save_speakers)
    ]
