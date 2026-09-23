import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0004_comments_publish_immediately'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='newsletter_sent_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='newsletter',
            name='confirmed_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='newsletter',
            name='confirmation_sent_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='newsletter',
            name='unsubscribed_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        # Nullable for now: every existing row needs its own random value, which
        # a column default cannot provide. 0006 fills them, 0007 makes it unique.
        migrations.AddField(
            model_name='newsletter',
            name='unsubscribe_token',
            field=models.CharField(max_length=64, null=True, editable=False),
        ),
        migrations.CreateModel(
            name='NewsletterDelivery',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sent_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('post', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='newsletter_deliveries', to='blog.post')),
                ('subscriber', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='deliveries', to='blog.newsletter')),
            ],
            options={
                'verbose_name_plural': 'newsletter deliveries',
                'constraints': [models.UniqueConstraint(fields=('post', 'subscriber'), name='unique_newsletter_delivery')],
            },
        ),
    ]
