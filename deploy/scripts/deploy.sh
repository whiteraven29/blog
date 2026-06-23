#!/usr/bin/env bash
set -Eeuo pipefail

APP_NAME=${APP_NAME:-whiteraven-blog}
APP_REPOSITORY=${APP_REPOSITORY:-https://github.com/whiteraven29/blog.git}
APP_BRANCH=${APP_BRANCH:-main}
KEEP_RELEASES=${KEEP_RELEASES:-5}

APP_ROOT="/var/www/apps/${APP_NAME}"
RELEASES_ROOT="${APP_ROOT}/releases"
SHARED_ROOT="/var/www/shared/${APP_NAME}"
TMP_ROOT="/var/www/tmp/${APP_NAME}"
BACKUP_RELEASE_ROOT="/var/www/backups/releases/${APP_NAME}"
ENV_FILE="${SHARED_ROOT}/.env"
RELEASE_ID=$(date -u +%Y%m%d%H%M%S)
RELEASE_DIR="${RELEASES_ROOT}/${RELEASE_ID}"
SOURCE_DIR=${1:-}
STAGING_DIR=
SWITCHED=false
DEPLOY_SUCCEEDED=false
PREVIOUS_TARGET=
PIP_CACHE_DIR="${TMP_ROOT}/pip-cache-${RELEASE_ID}"
npm_config_cache="${TMP_ROOT}/npm-cache-${RELEASE_ID}"

cleanup() {
    EXIT_CODE=$?
    if [[ -n "${STAGING_DIR}" && -d "${STAGING_DIR}" ]]; then
        rm -rf "${STAGING_DIR}"
    fi
    rm -rf "${PIP_CACHE_DIR}" "${npm_config_cache}"

    if [[ "${DEPLOY_SUCCEEDED}" == false && "${SWITCHED}" == true ]]; then
        echo "Deployment failed; restoring the previous release." >&2
        if [[ -n "${PREVIOUS_TARGET}" ]]; then
            ln -sfn "${PREVIOUS_TARGET}" "${APP_ROOT}/current.next"
            mv -Tf "${APP_ROOT}/current.next" "${APP_ROOT}/current"
            systemctl restart whiteraven-blog.service || true
            systemctl reload nginx || true
        else
            rm -f "${APP_ROOT}/current"
            systemctl stop whiteraven-blog.service || true
        fi
    fi

    if [[ "${DEPLOY_SUCCEEDED}" == false && -d "${RELEASE_DIR}" ]]; then
        rm -rf "${RELEASE_DIR}"
    fi

    trap - EXIT
    exit "${EXIT_CODE}"
}
trap cleanup EXIT

if [[ ! -f "${ENV_FILE}" ]]; then
    echo "Missing ${ENV_FILE}. Run bootstrap.sh and configure the environment first." >&2
    exit 1
fi

export PIP_CACHE_DIR
export npm_config_cache
export TMPDIR="${TMP_ROOT}"
mkdir -p "${PIP_CACHE_DIR}" "${npm_config_cache}"

if [[ -z "${SOURCE_DIR}" ]]; then
    STAGING_DIR=$(mktemp -d "${TMP_ROOT}/deploy.XXXXXX")
    git clone --depth 1 --branch "${APP_BRANCH}" "${APP_REPOSITORY}" "${STAGING_DIR}/source"
    SOURCE_DIR="${STAGING_DIR}/source"
fi

if [[ ! -d "${SOURCE_DIR}" ]]; then
    echo "Source directory does not exist: ${SOURCE_DIR}" >&2
    exit 1
fi

SOURCE_DIR=$(cd "${SOURCE_DIR}" && pwd)
if [[ ! -f "${SOURCE_DIR}/backend/requirements.txt" ||
      ! -f "${SOURCE_DIR}/backend/manage.py" ||
      ! -f "${SOURCE_DIR}/frontend/package.json" ]]; then
    echo "Source directory is not the repository root: ${SOURCE_DIR}" >&2
    echo "Expected backend/requirements.txt, backend/manage.py, and frontend/package.json." >&2
    exit 1
fi

mkdir -p "${RELEASE_DIR}"
rsync -a --delete \
    --exclude='.git/' \
    --exclude='.env' \
    --exclude='backend/db.sqlite3' \
    --exclude='backend/media/' \
    --exclude='backend/staticfiles/' \
    --exclude='frontend/node_modules/' \
    --exclude='frontend/dist/' \
    --exclude='**/__pycache__/' \
    "${SOURCE_DIR}/" "${RELEASE_DIR}/"

python3 -m venv "${RELEASE_DIR}/venv"
"${RELEASE_DIR}/venv/bin/pip" install --upgrade pip wheel
"${RELEASE_DIR}/venv/bin/pip" install -r "${RELEASE_DIR}/backend/requirements.txt"

(
    set -a
    # shellcheck disable=SC1090
    source "${ENV_FILE}"
    set +a
    cd "${RELEASE_DIR}/frontend"
    npm ci
    VITE_API_BASE_URL=${VITE_API_BASE_URL:-/api} npm run build

    cd "${RELEASE_DIR}/backend"
    "${RELEASE_DIR}/venv/bin/python" manage.py check --deploy
    if [[ -L "${APP_ROOT}/current" ]]; then
        "/var/www/scripts/${APP_NAME}/backup-db.sh"
    fi
    "${RELEASE_DIR}/venv/bin/python" manage.py migrate --noinput
    "${RELEASE_DIR}/venv/bin/python" manage.py collectstatic --noinput
)

chown -R root:www-data "${RELEASE_DIR}"
find "${RELEASE_DIR}" -type d -exec chmod 0755 {} +
find "${RELEASE_DIR}" -type f -exec chmod 0644 {} +
find "${RELEASE_DIR}/venv/bin" -type f -exec chmod 0755 {} +

if [[ -L "${APP_ROOT}/current" ]]; then
    CURRENT_TARGET=$(readlink -f "${APP_ROOT}/current")
    PREVIOUS_TARGET="${CURRENT_TARGET}"
    RELEASE_ARCHIVE="${BACKUP_RELEASE_ROOT}/$(basename "${CURRENT_TARGET}")-${RELEASE_ID}.tar.gz"
    tar -C "${RELEASES_ROOT}" -czf "${RELEASE_ARCHIVE}" "$(basename "${CURRENT_TARGET}")"
    chmod 0440 "${RELEASE_ARCHIVE}"
fi

ln -sfn "${RELEASE_DIR}" "${APP_ROOT}/current.next"
mv -Tf "${APP_ROOT}/current.next" "${APP_ROOT}/current"
SWITCHED=true

systemctl restart whiteraven-blog.service
systemctl reload nginx

for _ in {1..20}; do
    if curl --silent --fail \
        --header "X-Forwarded-Proto: https" \
        --unix-socket "${TMP_ROOT}/gunicorn.sock" \
        http://localhost/api/health/ >/dev/null; then
        echo "Deployment ${RELEASE_ID} is healthy."
        break
    fi
    sleep 1
done

if ! curl --silent --fail \
    --header "X-Forwarded-Proto: https" \
    --unix-socket "${TMP_ROOT}/gunicorn.sock" \
    http://localhost/api/health/ >/dev/null; then
    echo "Health check failed." >&2
    exit 1
fi

mapfile -t OLD_RELEASES < <(find "${RELEASES_ROOT}" -mindepth 1 -maxdepth 1 -type d -printf '%f\n' | sort -r | tail -n "+$((KEEP_RELEASES + 1))")
for release in "${OLD_RELEASES[@]}"; do
    rm -rf "${RELEASES_ROOT:?}/${release}"
done

DEPLOY_SUCCEEDED=true
