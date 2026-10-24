#!/usr/bin/env bash
# Runs the TM Forum TMF638 v5.0.0 API Conformance Test Kit (CTK) against this project's API.
#
#   ctk/run-api-ctk.sh                    # the `app` service of this compose project (must be running)
#   ctk/run-api-ctk.sh http://host:8080   # any other reachable API; the CTK container has to reach it
#
# An API with AUTH_MODE=basic / oauth2 needs credentials (they go into the kit's `headers`, and the script uses
# them for its own check): CTK_BASIC=user:password   or   CTK_BEARER=<access token>   (the user needs the write role).
#
# Downloads the kit into ctk/work/ (git-ignored), verifies its checksum, points config.json at the API and runs
# the kit's own run.sh. Result: ctk/work/ctk/REPORT.HTML. See ctk/README.md.
set -euo pipefail

ZIP_URL="https://tmf-open-api-table-documents.s3.eu-west-1.amazonaws.com/OpenApiTable/TMF638_Service_Inventory/5.0.0/ctk/tmf638-v5.0.0-ctk-1.0.1.zip"
ZIP_SHA256="2ddea57dcafa6ec7881ff66046cfe93deb21546bdfc911ed52c37433336ae0d5"
# host name of the app on the CTK's Docker network `tmf` (the kit's default NO_PROXY list contains it) and its port
ALIAS="tmf638-ri"
APP_PORT=8000
auth_header=""
[ -n "${CTK_BASIC:-}" ] && auth_header="Basic $(printf '%s' "$CTK_BASIC" | base64 | tr -d '\n')"
[ -n "${CTK_BEARER:-}" ] && auth_header="Bearer $CTK_BEARER"

# more services than this in the database slow the kit down (see the warning below)
MAX_SERVICES=20

here="$(cd "$(dirname "$0")" && pwd)"
root="$(dirname "$here")"
work="$here/work"
zip="$work/$(basename "$ZIP_URL")"
kit="$work/ctk"

for tool in docker curl python3; do
  command -v "$tool" >/dev/null || { echo "Error: '$tool' is required" >&2; exit 1; }
done

case "$(uname -m)" in
  x86_64 | amd64) platform="linux/amd64" ;;
  aarch64 | arm64) platform="linux/arm64" ;;
  *) echo "Error: unsupported architecture $(uname -m)" >&2; exit 1 ;;
esac

# --- the kit ---------------------------------------------------------------------------------------------------
mkdir -p "$work"
[ -f "$zip" ] || curl -fsSL -o "$zip" "$ZIP_URL"
actual="$( (sha256sum "$zip" 2>/dev/null || shasum -a 256 "$zip") | cut -d' ' -f1)"
if [ "$actual" != "$ZIP_SHA256" ]; then
  rm -f "$zip"
  echo "Error: checksum of $(basename "$zip") is $actual, expected $ZIP_SHA256" >&2
  exit 1
fi
rm -rf "$kit"
python3 -m zipfile -e "$zip" "$kit"
chmod +x "$kit/run.sh"

# --- the API under test ----------------------------------------------------------------------------------------
if [ $# -ge 1 ]; then
  api_url="${1%/}"
else
  app="$(docker compose --project-directory "$root" ps -q app)"
  if [ -z "$app" ]; then
    echo "Error: the app container isn't running. Start it first, e.g. 'docker compose --profile postgres up -d --build'" >&2
    exit 1
  fi
  docker network inspect tmf >/dev/null 2>&1 || docker network create tmf >/dev/null
  # the CTK container reaches the app by this alias; "already exists" if connected before
  docker network connect --alias "$ALIAS" tmf "$app" 2>/dev/null || true
  api_url="http://$ALIAS:$APP_PORT"
  published="$(docker compose --project-directory "$root" port app "$APP_PORT" 2>/dev/null || true)"
  [ -n "$published" ] && check_url="http://127.0.0.1:${published##*:}"
fi
check_url="${check_url:-$api_url}"   # where this script can reach the API (may not be possible: then no check)

# the kit validates every returned service against the schema in its own process: with many services in the
# database the list tests need 5+ s each, although the API answers in milliseconds
total="$(curl -fsS -m 10 -D - -o /dev/null ${auth_header:+-H "Authorization: $auth_header"} "$check_url/service?limit=1" 2>/dev/null | tr -d '\r' | awk -F': ' 'tolower($1)=="x-total-count" {print $2}')" || true
if [ -n "${total:-}" ] && [ "$total" -gt "$MAX_SERVICES" ]; then
  echo "Warning: the database holds $total services. The run passes but is slow (the 'Test schema' steps of the list" >&2
  echo "         requests take 5+ s each); use an empty database for a quick, clean run. See ctk/README.md." >&2
fi

# the kit appends the resource path (/service) to "url"; the API serves it at the root
python3 - "$kit/config.json" "$api_url" "$auth_header" <<'PY'
import json, sys
path, url, authorization = sys.argv[1:]
with open(path) as f:
    config = json.load(f)
config["url"] = url
if authorization:
    config["headers"]["Authorization"] = authorization
with open(path, "w") as f:
    json.dump(config, f, indent=4)
PY
echo "CTK $(basename "$ZIP_URL") against $api_url ($platform)"

# --- run -------------------------------------------------------------------------------------------------------
cd "$kit"
platform="$platform" ./run.sh || true   # run.sh ends with xdg-open, which fails on a machine without a desktop
if [ -f REPORT.HTML ]; then
  echo "Report: $kit/REPORT.HTML"
else
  echo "Error: the CTK produced no report" >&2
  exit 1
fi
