# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mantis_actionables', '0016_auto_20150303_1400'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='source',
            unique_together=set([('iobject_identifier', 'iobject_fact', 'iobject_factvalue', 'top_level_iobject_identifier', 'content_type', 'object_id')]),
        ),
    ]
