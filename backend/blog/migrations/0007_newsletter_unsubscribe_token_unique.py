import blog.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0006_newsletter_backfill'),
    ]

    operations = [
        migrations.AlterField(
            model_name='newsletter',
            name='unsubscribe_token',
            field=models.CharField(default=blog.models.new_unsubscribe_token, editable=False, max_length=64, unique=True),
        ),
    ]
