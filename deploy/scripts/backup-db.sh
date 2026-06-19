#!/usr/bin/env bash
set -Eeuo pipefail

APP_NAME=${APP_NAME:-whiteraven-blog}
SHARED_ROOT="/var/www/shared/${APP_NAME}"
BACKUP_ROOT="/var/www/backups/db/${APP_NAME}"
ENV_FILE="${SHARED_ROOT}/.env"
STAMP=$(date -u +%Y%m%d%H%M%S)
TARGET=
BACKUP_COMPLETE=false

cleanup() {
    if [[ "${BACKUP_COMPLETE}" == false && -n "${TARGET}" ]]; then
        rm -f "${TARGET}"
    fi
}
trap cleanup EXIT

set -a
# shellcheck disable=SC1090
source "${ENV_FILE}"
set +a

mkdir -p "${BACKUP_ROOT}"

if [[ "${DJANGO_DB_ENGINE:-sqlite}" =~ ^(postgres|postgresql)$ ]]; then
    TARGET="${BACKUP_ROOT}/${STAMP}.sql.gz"
    PGPASSWORD="${DJANGO_DB_PASSWORD}" pg_dump \
        --host="${DJANGO_DB_HOST:-127.0.0.1}" \
        --port="${DJANGO_DB_PORT:-5432}" \
        --username="${DJANGO_DB_USER}" \
        --dbname="${DJANGO_DB_NAME}" \
        --no-owner --no-privileges | gzip -9 > "${TARGET}"
else
    TARGET="${BACKUP_ROOT}/${STAMP}.sqlite3"
    sqlite3 "${DJANGO_SQLITE_PATH}" ".backup '${TARGET}'"
fi

chmod 0440 "${TARGET}"
BACKUP_COMPLETE=true
echo "Created immutable database backup: ${TARGET}"
