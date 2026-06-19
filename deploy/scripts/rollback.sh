#!/usr/bin/env bash
set -Eeuo pipefail

APP_NAME=${APP_NAME:-whiteraven-blog}
APP_ROOT="/var/www/apps/${APP_NAME}"
RELEASES_ROOT="${APP_ROOT}/releases"
CURRENT=$(readlink -f "${APP_ROOT}/current")
TARGET=${1:-}
TMP_ROOT="/var/www/tmp/${APP_NAME}"

if [[ -z "${TARGET}" ]]; then
    TARGET=$(find "${RELEASES_ROOT}" -mindepth 1 -maxdepth 1 -type d -printf '%f\n' | sort -r | grep -v "^$(basename "${CURRENT}")$" | head -n 1)
fi

if [[ -z "${TARGET}" || ! -d "${RELEASES_ROOT}/${TARGET}" ]]; then
    echo "Rollback release not found: ${TARGET:-none}" >&2
    exit 1
fi

ln -sfn "${RELEASES_ROOT}/${TARGET}" "${APP_ROOT}/current.next"
mv -Tf "${APP_ROOT}/current.next" "${APP_ROOT}/current"
systemctl restart whiteraven-blog.service
systemctl reload nginx

for _ in {1..20}; do
    if curl --silent --fail \
        --header "X-Forwarded-Proto: https" \
        --unix-socket "${TMP_ROOT}/gunicorn.sock" \
        http://localhost/api/health/ >/dev/null; then
        echo "Rolled back application code to ${TARGET}. Database and shared data were untouched."
        exit 0
    fi
    sleep 1
done

echo "Rollback target failed its health check; restoring $(basename "${CURRENT}")." >&2
ln -sfn "${CURRENT}" "${APP_ROOT}/current.next"
mv -Tf "${APP_ROOT}/current.next" "${APP_ROOT}/current"
systemctl restart whiteraven-blog.service
systemctl reload nginx
exit 1
