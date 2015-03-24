# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mantis_actionables', '0022_auto_20150310_1245'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='source',
            unique_together=set([('iobject_identifier', 'iobject_fact', 'iobject_factvalue', 'top_level_iobject_identifier', 'import_info', 'content_type', 'object_id')]),
        ),
    ]
