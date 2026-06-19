#!/usr/bin/env bash
set -Eeuo pipefail

if [[ ${EUID} -ne 0 ]]; then
    echo "Run this bootstrap script as root." >&2
    exit 1
fi

APP_NAME=${APP_NAME:-whiteraven-blog}
APP_ROOT="/var/www/apps/${APP_NAME}"
SHARED_ROOT="/var/www/shared/${APP_NAME}"
LOG_ROOT="/var/www/logs/${APP_NAME}"
TMP_ROOT="/var/www/tmp/${APP_NAME}"
SCRIPT_ROOT="/var/www/scripts/${APP_NAME}"
BACKUP_DB_ROOT="/var/www/backups/db/${APP_NAME}"
BACKUP_RELEASE_ROOT="/var/www/backups/releases/${APP_NAME}"
REPO_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)

install -d -m 0755 /var/www/{apps,logs,backups,tmp,scripts,shared}
install -d -o www-data -g www-data -m 0755 \
    "${APP_ROOT}/releases" \
    "${SHARED_ROOT}/media" \
    "${SHARED_ROOT}/static" \
    "${SHARED_ROOT}/data" \
    "${LOG_ROOT}" \
    "${TMP_ROOT}" \
    "${TMP_ROOT}/uploads"
install -d -o root -g www-data -m 0750 \
    "${BACKUP_DB_ROOT}" \
    "${BACKUP_RELEASE_ROOT}" \
    "${SCRIPT_ROOT}"

install -o root -g www-data -m 0750 "${REPO_ROOT}/deploy/scripts/deploy.sh" "${SCRIPT_ROOT}/deploy.sh"
install -o root -g www-data -m 0750 "${REPO_ROOT}/deploy/scripts/rollback.sh" "${SCRIPT_ROOT}/rollback.sh"
install -o root -g www-data -m 0750 "${REPO_ROOT}/deploy/scripts/backup-db.sh" "${SCRIPT_ROOT}/backup-db.sh"
install -o root -g root -m 0644 "${REPO_ROOT}/deploy/systemd/whiteraven-blog.service" /etc/systemd/system/whiteraven-blog.service
install -o root -g root -m 0644 "${REPO_ROOT}/deploy/nginx/whiteraven-blog.conf" /etc/nginx/sites-available/whiteraven-blog
install -o root -g root -m 0644 "${REPO_ROOT}/deploy/logrotate/whiteraven-blog" /etc/logrotate.d/whiteraven-blog
rm -f /etc/nginx/sites-enabled/default
ln -sfn /etc/nginx/sites-available/whiteraven-blog /etc/nginx/sites-enabled/whiteraven-blog

if [[ ! -f "${SHARED_ROOT}/.env" ]]; then
    install -o root -g www-data -m 0640 "${REPO_ROOT}/deploy/env.production.example" "${SHARED_ROOT}/.env"
    echo "Created ${SHARED_ROOT}/.env; replace every placeholder before deployment."
fi

systemctl daemon-reload
nginx -t

echo "Bootstrap complete."
echo "Next: edit ${SHARED_ROOT}/.env, configure server_name/TLS, then run ${SCRIPT_ROOT}/deploy.sh."
