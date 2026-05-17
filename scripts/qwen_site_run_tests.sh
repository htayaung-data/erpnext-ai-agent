#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SERVICE="${QWEN_DOCKER_SERVICE:-backend}"
SITE="${QWEN_SITE:-}"

usage() {
	echo "Usage: scripts/qwen_site_run_tests.sh <python.module.path>"
	echo "Runs 'bench --site <site> run-tests --module <module>' inside the backend container."
}

if [[ $# -ne 1 ]]; then
	usage
	exit 1
fi

if [[ -z "${SITE}" && -f "${ROOT_DIR}/.env" ]]; then
	SITE="$(awk -F= '
		$1 == "DEFAULT_SITE" { value = $2 }
		$1 == "SITE_NAME" && value == "" { value = $2 }
		END {
			gsub(/^["'\''"]|["'\''"]$/, "", value)
			print value
		}
	' "${ROOT_DIR}/.env")"
fi

if [[ -z "${SITE}" ]]; then
	echo "Unable to determine site name. Set QWEN_SITE or define DEFAULT_SITE/SITE_NAME in .env."
	exit 1
fi

MODULE_PATH="$1"

cd "${ROOT_DIR}"
exec docker compose exec -T "${SERVICE}" bench --site "${SITE}" run-tests --module "${MODULE_PATH}"
