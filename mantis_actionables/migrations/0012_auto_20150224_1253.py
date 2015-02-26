# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('dingos', '0005_AddTaggingHistory'),
        ('mantis_actionables', '0011_singletonobservable_actionable_tags_cache'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='importinfo',
            name='comment',
        ),
        migrations.RemoveField(
            model_name='importinfo',
            name='user',
        ),
        migrations.AddField(
            model_name='importinfo',
            name='create_timestamp',
            field=models.DateTimeField(default=datetime.datetime(2015, 2, 24, 12, 52, 32, 263422), auto_now_add=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='importinfo',
            name='creating_action',
            field=models.ForeignKey(related_name=b'import_infos', default=0, to='mantis_actionables.Action'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='importinfo',
            name='description',
            field=models.TextField(default=b'', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='importinfo',
            name='name',
            field=models.CharField(default=b'Unnamed', help_text=b"Name of the information object, usually auto generated.\n                                         from type and facts flagged as 'naming'.", max_length=255, editable=False, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='importinfo',
            name='namespace',
            field=models.ForeignKey(default=0, to='dingos.IdentifierNameSpace'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='importinfo',
            name='related_threatactor',
            field=models.CharField(default='', max_length=255, blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='importinfo',
            name='timestamp',
            field=models.DateTimeField(default=datetime.datetime(2015, 2, 24, 12, 53, 49, 294188), auto_now_add=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='importinfo',
            name='uid',
            field=models.SlugField(default=b'', max_length=255),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='importinfo',
            name='uri',
            field=models.URLField(default=b'', help_text=b'URI pointing to further\n                                       information concerning this\n                                       import, e.g., the HTML\n                                       report of a malware analysis\n                                       through Cuckoo or similar.', blank=True),
            preserve_default=True,
        ),
    ]
