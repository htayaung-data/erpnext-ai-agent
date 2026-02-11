#!/usr/bin/env bash
set -euo pipefail
# First-time only: creates SITE_NAME and installs ERPNext + HRMS + FAC
docker compose --profile init up create-site
