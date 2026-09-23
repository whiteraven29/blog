# Production Deployment

This deployment follows **Server Directory Structure Amendment v1.0**. Nothing
persistent is stored inside a release directory.

## Resulting server layout

```text
/var/www/
├── apps/whiteraven-blog/
│   ├── releases/<UTC timestamp>/    # Immutable application releases
│   └── current -> releases/...      # Active release
├── logs/whiteraven-blog/            # Gunicorn and Nginx logs
├── backups/
│   ├── db/whiteraven-blog/          # Read-only database backups
│   └── releases/whiteraven-blog/    # Read-only release archives
├── tmp/whiteraven-blog/             # Socket, clones, and disposable caches
├── scripts/whiteraven-blog/         # Deploy, backup, and rollback scripts
└── shared/whiteraven-blog/
    ├── .env                          # Production configuration
    ├── media/                        # Persistent uploads
    ├── static/                       # Collected Django static files
    └── data/                         # SQLite only, if selected
```

## Server prerequisites

```bash
sudo apt update
sudo apt install -y nginx postgresql postgresql-client python3 python3-venv \
  python3-dev build-essential libpq-dev nodejs npm git rsync curl sqlite3 \
  certbot python3-certbot-nginx
```

Use a current Node.js LTS release supported by Vite 8.

## PostgreSQL

```bash
sudo -u postgres psql
```

```sql
CREATE USER whiteraven_blog WITH PASSWORD 'replace-with-a-strong-password';
CREATE DATABASE whiteraven_blog OWNER whiteraven_blog;
\q
```

## First deployment

Clone into a disposable location, bootstrap the standard directories, and edit
the persistent environment file:

```bash
sudo mkdir -p /var/www/tmp/whiteraven-blog
sudo git clone https://github.com/whiteraven29/blog.git \
  /var/www/tmp/whiteraven-blog/bootstrap-source
cd /var/www/tmp/whiteraven-blog/bootstrap-source

sudo deploy/scripts/bootstrap.sh
sudoedit /var/www/shared/whiteraven-blog/.env
sudoedit /etc/nginx/sites-available/whiteraven-blog
```

Set the real domain in `server_name`. Obtain and configure the TLS certificate
before enabling permanent HSTS or preload options.

Deploy the checked-out source:

```bash
# Run this from the repository root (the directory containing backend/ and frontend/).
cd /var/www/tmp/whiteraven-blog/bootstrap-source
sudo /var/www/scripts/whiteraven-blog/deploy.sh "$PWD"
sudo systemctl enable --now whiteraven-blog
sudo systemctl enable --now nginx
sudo certbot --nginx -d blog.wh1teraven.site
curl --fail https://blog.wh1teraven.site/api/health/
```

Every deployment after the first creates a database backup before migrations.
After HTTPS is confirmed, keep secure redirect/cookies enabled in the persistent
environment file and restart the service after configuration changes.

## Routine deployment

The operational script clones `main` into `/var/www/tmp`, creates a timestamped
release, builds it, runs checks and migrations, switches `current` atomically,
and retains the newest five releases:

```bash
sudo /var/www/scripts/whiteraven-blog/deploy.sh
```

Override the source when needed:

```bash
sudo APP_BRANCH=release /var/www/scripts/whiteraven-blog/deploy.sh
sudo /var/www/scripts/whiteraven-blog/deploy.sh /path/to/checked-out/source
```

When `deploy/nginx/whiteraven-blog.conf` changes, merge the update into the
installed site configuration so root-level endpoints such as `sitemap.xml` and
`rss.xml` reach Django.

Do not `install` the repository copy over the live one. The installed file holds
the real `server_name` and the TLS block certbot wrote in place; neither is in
the repository, and overwriting them takes the site off its own domain. Requests
then fall through to whatever other vhost listens on that port.

```bash
diff -u /etc/nginx/sites-available/whiteraven-blog \
  deploy/nginx/whiteraven-blog.conf
sudoedit /etc/nginx/sites-available/whiteraven-blog   # apply the changes by hand
sudo nginx -t
sudo systemctl reload nginx
```

If the installed copy was overwritten, restore the domain in `server_name` and
re-run `sudo certbot --nginx -d <domain>` to rebuild the TLS block.

## Email and newsletter

Email goes out through Brevo's SMTP relay. It covers three things: newsletter
confirmations, new-post emails to subscribers, and contact-form messages
forwarded to `CONTACT_NOTIFY_EMAIL`. When `DJANGO_EMAIL_HOST` is empty, nothing
is sent. Sign-ups still work, and new-post emails wait until email is configured.

### One-time Brevo setup

1. In Brevo, add and authenticate the sending domain (**Senders, Domains &
   Dedicated IPs → Domains**). Publish the DKIM, SPF and DMARC records it lists.
   Without them, Gmail and Yahoo send the mail to spam or reject it.
2. Add the From address as a verified sender.
3. Generate an SMTP key under **SMTP & API → SMTP**.
4. Fill in the email block of `/var/www/shared/whiteraven-blog/.env` (see
   `deploy/env.production.example`), then `sudo systemctl restart whiteraven-blog`.
5. Send yourself a test message:

   ```bash
   cd /var/www/apps/whiteraven-blog/current/backend
   sudo -u www-data bash -c 'set -a; source /var/www/shared/whiteraven-blog/.env; set +a; \
     ../venv/bin/python manage.py sendtestemail you@example.com'
   ```

### The send timer

`whiteraven-blog-newsletter.timer` runs `manage.py send_newsletter` every ten
minutes. `bootstrap.sh` installs it on a new server. A server bootstrapped
before the newsletter existed needs it installed once:

```bash
sudo install -m 0644 deploy/systemd/whiteraven-blog-newsletter.{service,timer} /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now whiteraven-blog-newsletter.timer
```

```bash
systemctl list-timers whiteraven-blog-newsletter.timer   # next and last run
sudo journalctl -u whiteraven-blog-newsletter            # what each run sent
```

To see what the next run would send without sending anything, run the same
command as the test email above with `send_newsletter --dry-run`.

### How sending behaves

- A post is emailed once, the first time the timer sees it published. Posts that
  were already published when the newsletter shipped are marked as sent and never
  go out. So is any post published more than seven days before the timer reaches it.
- Each email is recorded before it is sent. A crash or SMTP failure never mails
  anyone twice, and the next run retries whatever was left.
- New-post emails stop at `NEWSLETTER_DAILY_SEND_LIMIT` per rolling 24 hours and
  resume on a later run.
- To publish a post without emailing anyone, select it in the admin and choose
  **Don't email subscribers about selected posts** within ten minutes of
  publishing.

### Subscribers

Sign-up is double opt-in. Only addresses that clicked the confirmation link get
mail. Addresses that signed up before confirmation existed show as **Awaiting
confirmation**. Select them in the admin and choose **Resend confirmation email**
to invite them to opt in. Every new-post email carries an unsubscribe link and
the one-click `List-Unsubscribe` headers that Gmail and Yahoo require.

## Backups and rollback

```bash
sudo /var/www/scripts/whiteraven-blog/backup-db.sh
sudo /var/www/scripts/whiteraven-blog/rollback.sh
sudo /var/www/scripts/whiteraven-blog/rollback.sh 20260619143000
```

Rollback changes only the application symlink. Shared media and the database
remain untouched. If a migration itself must be reversed, restore the matching
database backup deliberately after reviewing the migration.

## Operations

```bash
sudo systemctl status whiteraven-blog
sudo journalctl -u whiteraven-blog -f
sudo tail -f /var/www/logs/whiteraven-blog/error.log
sudo nginx -t
sudo logrotate -d /etc/logrotate.d/whiteraven-blog
```

Logs rotate daily and retain fourteen compressed rotations. Temporary package
caches are deleted after deployment. Uploaded media, database files, logs, and
backups never live under `/var/www/apps`.
