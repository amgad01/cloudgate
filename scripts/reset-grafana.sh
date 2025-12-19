#!/usr/bin/env bash
set -euo pipefail

# Reset Grafana admin password or wipe Grafana state.
# Usage:
#   bash scripts/reset-grafana.sh [--password NEW_PASS] [--wipe]
#
# Options:
#   --password NEW_PASS  Reset the admin password to NEW_PASS using grafana-cli
#   --wipe               Stop Grafana and remove its Docker volume to factory reset

COMPOSE_DIR="$(dirname "$0")/.."
pushd "$COMPOSE_DIR" >/dev/null

GRAFANA_SERVICE=${GRAFANA_SERVICE:-grafana}
NEW_PASS=""
WIPE=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --password)
      NEW_PASS="$2"
      shift 2
      ;;
    --wipe)
      WIPE=1
      shift 1
      ;;
    *)
      echo "Unknown option: $1" >&2
      exit 1
      ;;
  esac
done

if [[ "$WIPE" -eq 1 ]]; then
  echo "Stopping Grafana and wiping its Docker volume (factory reset)..."
  docker compose stop "$GRAFANA_SERVICE"
  # Remove the grafana_data volume defined in docker-compose.yml
  VOLUME="grafana_data"
  if docker volume ls --format '{{.Name}}' | grep -q "$VOLUME"; then
    echo "Removing volume: $VOLUME"
    docker volume rm "$VOLUME" || true
  else
    echo "Volume $VOLUME not found. It may have been removed already."
  fi
  echo "Starting Grafana again..."
  docker compose up -d "$GRAFANA_SERVICE"
  echo "Grafana has been factory reset. Default credentials are admin/admin (unless overridden by env)."
  popd >/dev/null
  exit 0
fi

if [[ -n "$NEW_PASS" ]]; then
  echo "Resetting Grafana admin password via grafana-cli..."
  # Ensure Grafana is running
  docker compose up -d "$GRAFANA_SERVICE"
  # Use grafana-cli inside the container to reset admin password
  docker compose exec -T "$GRAFANA_SERVICE" bash -lc "grafana-cli admin reset-admin-password '$NEW_PASS'"
  echo "Admin password reset completed."
  popd >/dev/null
  exit 0
fi

echo "No action specified. Use --password NEW_PASS or --wipe"
popd >/dev/null
