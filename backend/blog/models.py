from django.db import models
from django.contrib.auth.hashers import check_password, identify_hasher, make_password
from django.contrib.auth.models import User
from django.utils.text import slugify
import secrets
import uuid


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=7, default='#a855f7')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'categories'
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name) or 'category'
            self.slug = base
            n = 1
            while Category.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f'{base}-{n}'
                n += 1
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=60, unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class PostQuerySet(models.QuerySet):
    def with_searchable_content(self):
        """Annotate the content search may match against.

        Locked writeups contribute nothing, otherwise a search for a flag or a
        password would confirm what a locked post says.
        """
        return self.annotate(
            searchable_content=models.Case(
                models.When(is_locked=True, then=models.Value('')),
                default=models.F('content'),
                output_field=models.TextField(),
            )
        )


class Post(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
    ]
    DIFFICULTY_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=250)
    slug = models.SlugField(max_length=280, unique=True, blank=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='posts')
    tags = models.ManyToManyField(Tag, blank=True, related_name='posts')
    excerpt = models.TextField(max_length=500, blank=True)
    content = models.TextField()
    cover_image = models.ImageField(upload_to='covers/', blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    difficulty = models.CharField(max_length=15, choices=DIFFICULTY_CHOICES, default='beginner')
    is_featured = models.BooleanField(default=False)
    views = models.PositiveIntegerField(default=0)
    read_time = models.PositiveSmallIntegerField(default=5, help_text='Estimated read time in minutes')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)
    # Set once subscribers have been emailed about this post, or once it has been
    # deliberately skipped. `send_newsletter` only looks at posts where it is empty.
    newsletter_sent_at = models.DateTimeField(null=True, blank=True)
    # Writeups for active machines. While locked, readers get the post's title
    # and a notice, and the content only after posting the password to /unlock/.
    is_locked = models.BooleanField(default=False)
    lock_password = models.CharField(
        max_length=128, blank=True,
        help_text='Stored hashed. Type a new password here to change it.',
    )
    lock_platform = models.CharField(max_length=60, blank=True, default='HackTheBox')
    lock_hint = models.CharField(
        max_length=200, blank=True, default='the root flag',
        help_text='Completes "the password is …" in the notice readers see.',
    )

    objects = PostQuerySet.as_manager()

    class Meta:
        ordering = ['-published_at', '-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title)
            self.slug = base
            n = 1
            while Post.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f'{base}-{n}'
                n += 1
        if self.is_locked:
            # An excerpt cut from the content would publish the start of a
            # locked writeup on cards, in the RSS feed and in newsletter mail.
            if self.excerpt == self.content[:400]:
                self.excerpt = ''
        elif not self.excerpt and self.content:
            self.excerpt = self.content[:400]
        if self.lock_password:
            try:
                identify_hasher(self.lock_password)
            except ValueError:
                # Plain text from the editor or the admin form.
                self.lock_password = make_password(self.lock_password)
        super().save(*args, **kwargs)

    def check_lock_password(self, raw_password):
        return bool(self.lock_password) and check_password(raw_password, self.lock_password)

    def __str__(self):
        return self.title


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author_name = models.CharField(max_length=80, blank=True, default='')
    author_email = models.EmailField(blank=True, default='')
    body = models.TextField()
    # Comments go live as soon as they are posted. Unticking this in the admin
    # hides one again.
    is_approved = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'{self.author_name or "Anonymous"} on "{self.post.title}"'


class ContactMessage(models.Model):
    """A message sent through the public contact form.

    Records are an inbox, not a moderation queue: nothing here is ever published,
    so there is no approval step. `is_read` only tracks what has been triaged.
    """

    name = models.CharField(max_length=120)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField(max_length=5000)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.subject} — {self.email}'


def new_unsubscribe_token():
    return secrets.token_urlsafe(32)


class NewsletterQuerySet(models.QuerySet):
    def receiving(self):
        """Addresses that confirmed and have not unsubscribed since."""
        return self.filter(is_active=True, confirmed_at__isnull=False)


class Newsletter(models.Model):
    """A newsletter subscriber.

    Mail about new posts only goes to addresses that are active and confirmed.
    Anyone can type any address into the sign-up form, so an unconfirmed address
    only ever receives the one confirmation email.
    """

    email = models.EmailField(unique=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)
    # False once the reader unsubscribes.
    is_active = models.BooleanField(default=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    # Also what the confirmation link is bound to, so sending a new link, or
    # unsubscribing, invalidates every earlier one.
    confirmation_sent_at = models.DateTimeField(null=True, blank=True)
    unsubscribed_at = models.DateTimeField(null=True, blank=True)
    # Random rather than signed, so a link keeps working if SECRET_KEY rotates.
    unsubscribe_token = models.CharField(
        max_length=64, unique=True, default=new_unsubscribe_token, editable=False
    )

    objects = NewsletterQuerySet.as_manager()

    @property
    def is_receiving(self):
        return self.is_active and self.confirmed_at is not None

    def __str__(self):
        return self.email


class NewsletterDelivery(models.Model):
    """One post emailed to one subscriber.

    A row is written before the email is sent and removed if sending fails, so a
    run that is interrupted, or two that overlap, never mail anyone twice.
    """

    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='newsletter_deliveries')
    subscriber = models.ForeignKey(Newsletter, on_delete=models.CASCADE, related_name='deliveries')
    sent_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name_plural = 'newsletter deliveries'
        constraints = [
            models.UniqueConstraint(fields=['post', 'subscriber'], name='unique_newsletter_delivery'),
        ]

    def __str__(self):
        return f'{self.post} → {self.subscriber}'
