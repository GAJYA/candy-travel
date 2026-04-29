#!/usr/bin/env bash

set -euo pipefail

BASE_URL="${1:-https://www.willer.tech}"

echo "Checking ${BASE_URL}/healthz"
curl --fail --show-error --silent "${BASE_URL}/healthz" | tee /tmp/candy-travel-healthz.json
printf "\n\n"

echo "Checking ${BASE_URL}/api/v1/healthz"
curl --fail --show-error --silent "${BASE_URL}/api/v1/healthz" | tee /tmp/candy-travel-api-healthz.json
printf "\n"

echo "Health verification completed."
