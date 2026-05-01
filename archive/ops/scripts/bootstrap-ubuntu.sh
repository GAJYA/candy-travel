#!/usr/bin/env bash

set -euo pipefail

if [[ "${EUID}" -ne 0 ]]; then
  echo "Please run as root." >&2
  exit 1
fi

APP_USER="${APP_USER:-ubuntu}"
APP_ROOT="${APP_ROOT:-/srv/candy-travel}"
NODE_MAJOR="${NODE_MAJOR:-20}"

apt-get update
apt-get install -y curl git nginx certbot python3-certbot-nginx ufw

if ! command -v node >/dev/null 2>&1; then
  curl -fsSL "https://deb.nodesource.com/setup_${NODE_MAJOR}.x" | bash -
  apt-get install -y nodejs
fi

mkdir -p "${APP_ROOT}/app" "${APP_ROOT}/shared" /var/log/candy-travel
chown -R "${APP_USER}:${APP_USER}" "${APP_ROOT}" /var/log/candy-travel

ufw allow OpenSSH || true
ufw allow 'Nginx Full' || true

echo "Bootstrap completed."
echo "Next steps:"
echo "1. Upload project to ${APP_ROOT}/app"
echo "2. Copy ops/env/backend.env.example to ${APP_ROOT}/shared/backend.env and fill real values"
echo "3. Install backend dependencies and run build"
echo "4. Install systemd and nginx templates"
