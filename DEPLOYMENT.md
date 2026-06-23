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
sudo certbot --nginx -d blog.example.com
curl --fail https://blog.example.com/api/health/
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
