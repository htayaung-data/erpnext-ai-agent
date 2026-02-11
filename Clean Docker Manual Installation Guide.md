# ERPNext v16 + HRMS + Frappe Assistant Core (FAC) — Clean Docker Install Guide

This guide is written from our real install path (including the wrong turns), so you can reproduce a **clean, reliable ERPNext v16 stack** on another computer.
To install from our all-in-one package, please see Readme file.

You will end with:

- **ERPNext v16** running on `http://localhost:8082`
- **HRMS** installed and visible in UI
- **FAC** installed and accessible at `/app/fac-admin`
- A **custom Docker image** that already contains the apps (so deployments are repeatable)

---

## 0) Key Lessons (Wrong path → Right path)

### ✅ Right path decisions (what worked)

- **Build a custom image** that includes: `erpnext`, `hrms`, `frappe_assistant_core`
- Use **Frappe v16 branch** (`version-16`) for Frappe/ERPNext/HRMS
- Use **Node >= 24** and **Python 3.14.x** for current Frappe v16 builds (we hit hard dependency constraints)
- Run the **init sequence** explicitly:
  1. Infra (db + redis)
  2. Configurator
  3. Create-site (one-time)
  4. Start all services

### ❌ Wrong paths we hit (and what they mean)

- `invalid reference format` when using `frappe/erpnext:` → caused by **empty tag variables** (e.g. `ERPNEXT_VERSION` not set).
- `frappe==16.5.0 depends on Python>=3.14` → we tried Python 3.12; it failed dependency resolution.
- `yarn error: Expected node >=24 got 18.x` → Node 18 is too old for this Frappe v16 frontend build.
- `curl: (35) connection reset by peer` while downloading nvm script → transient network issue; retry build (or use mirrors).
- `502 Bad Gateway` + websocket `ECONNREFUSED 127.0.0.1:6379` → websocket was trying to connect to **localhost** Redis; must connect to **redis service name**.
- Compose warning `The "host" variable is not set` → compose treated `$host` as an env var; must escape as `$$host`.

---

## 1) Prerequisites

### Hardware / OS

- Ubuntu 22.04+ (native) or WSL2 Ubuntu 22.04+ (works)
- RAM: **12GB+** recommended (**16GB** ideal)
- Disk: **15–25GB** free

### Required software

- Docker Engine + Docker Compose plugin
- Git
- Curl

Install basics:

```bash
sudo apt-get update
sudo apt-get install -y git curl
```

---

## 2) Start from a clean folder

Choose a clean working directory (**do NOT** mix with older broken folders):

```bash
mkdir -p ~/erp16_fac_hrms
cd ~/erp16_fac_hrms
```

Optional: if you want a true clean reset (dangerous, deletes project containers/volumes):

```bash
# only if you know what you're doing
docker compose -p pwdstg -f ~/erp16_fac_hrms/frappe_docker/compose.yaml down -v --remove-orphans 2>/dev/null || true
```

---

## 3) Get `frappe_docker` (baseline compose + images)

Clone `frappe_docker` inside your project:

```bash
cd ~/erp16_fac_hrms
git clone https://github.com/frappe/frappe_docker.git
```

You should now have:

```text
~/erp16_fac_hrms/frappe_docker/compose.yaml
```

**Important: Use `compose.yaml` consistently.**

If you also see `compose.yml`, pick **ONE** and delete/rename the other to avoid mistakes.

- Recommended: keep `compose.yaml`, rename `compose.yml` to `compose.yml.bak` or delete it.

---

## 4) Create `apps.json` (apps you want baked into image)

Create this file at:

```text
~/erp16_fac_hrms/apps.json
```

Commands:

```bash
cd ~/erp16_fac_hrms

cat > apps.json <<'JSON'
[
  { "url": "https://github.com/frappe/erpnext", "branch": "version-16" },
  { "url": "https://github.com/frappe/hrms",   "branch": "version-16" },
  { "url": "https://github.com/buildswithpaul/Frappe_Assistant_Core", "branch": "main" }
]
JSON
```

---

## 5) Build the custom image (MOST IMPORTANT STEP)

You want a local image like:

```text
custom-apps:erp16_fac_hrms
```

### 5.1 Build args you must respect (based on our failures)

- `FRAPPE_BRANCH`: `version-16`
- **Node**: `>= 24` (we used `24.13.0`)
- **Python**: `3.14.x` (we used `3.14.2`)

### 5.2 Build using the provided `Containerfile` approach

If your project contains `images/custom/Containerfile` (your repo did), run from project root:

```bash
cd ~/erp16_fac_hrms

APPS_JSON_BASE64="$(base64 -w 0 apps.json)"

docker build --progress=plain \
  -t custom-apps:erp16_fac_hrms \
  -f images/custom/Containerfile \
  --build-arg FRAPPE_PATH="https://github.com/frappe/frappe" \
  --build-arg FRAPPE_BRANCH="version-16" \
  --build-arg NODE_VERSION="24.13.0" \
  --build-arg PYTHON_VERSION="3.14.2" \
  --build-arg APPS_JSON_BASE64="${APPS_JSON_BASE64}" \
  .
```

Verify the image exists:

```bash
docker image inspect custom-apps:erp16_fac_hrms >/dev/null \
  && echo "OK: custom image exists" \
  || echo "NOT FOUND: build failed"
```

### Common build failures & fixes

- **Python constraint error (3.12/3.11)** → rebuild with **Python 3.14.x**
- **Node engine mismatch** → rebuild with **Node 24.x**
- **nvm download fails** → retry build (network issue), or switch mirror inside `Containerfile` if needed

---

## 6) Configure Compose to use your custom image

Go into `frappe_docker`:

```bash
cd ~/erp16_fac_hrms/frappe_docker
```

Create `.env` file (recommended so tags don’t go blank):

```bash
cat > .env <<'ENV'
CUSTOM_IMAGE=custom-apps
CUSTOM_TAG=erp16_fac_hrms
ENV
```

### IMPORTANT: Fix `$host` compose interpolation bug

If your compose uses:

```yaml
FRAPPE_SITE_NAME_HEADER: $host
```

Docker Compose will warn:

> The "host" variable is not set...

✅ The correct value must escape `$` as `$$host`:

```yaml
FRAPPE_SITE_NAME_HEADER: $$host
```

If you want to patch quickly:

```bash
# only if your compose.yaml contains "FRAPPE_SITE_NAME_HEADER: $host"
grep -n "FRAPPE_SITE_NAME_HEADER" compose.yaml

# edit and replace "$host" -> "$$host"
nano compose.yaml
```

---

## 7) First-time boot sequence (repeatable and reliable)

Run these commands exactly (this sequence solved our long “configurator waiting” and 502 issues):

```bash
cd ~/erp16_fac_hrms/frappe_docker

# 1) clean shutdown (safe)
docker compose -p pwdstg -f compose.yaml down --remove-orphans

# 2) start infra first
docker compose -p pwdstg -f compose.yaml up -d db redis-cache redis-queue redis-socketio

# 3) run configurator in foreground (should exit 0)
docker compose -p pwdstg -f compose.yaml up configurator

# 4) first-time only: create site (site name = "frontend")
docker compose -p pwdstg -f compose.yaml --profile init up create-site

# 5) start everything
docker compose -p pwdstg -f compose.yaml up -d
docker compose -p pwdstg -f compose.yaml ps
```

### What “success” looks like

- `configurator` exits with **code 0**
- `create-site` installs `frappe` then `erpnext` and exits **code 0**
- `frontend` publishes port mapping like `0.0.0.0:8082->8080/tcp`

Open in browser:

```text
http://localhost:8082
```

---

## 8) Verify ERPNext + HRMS + FAC are installed

### 8.1 Verify apps inside the container

```bash
docker exec -it pwdstg-backend-1 bash -lc "bench --site frontend list-apps"
```

Expected to include:

- `frappe`
- `erpnext`
- `hrms`
- `frappe_assistant_core`

### 8.2 Verify UI modules

- **ERPNext**: you should see standard ERPNext modules/workspaces after login.
- **HRMS**: search `HR` / `Employee` / `Leave` in Awesomebar.
- **FAC Admin**:

  Open:

  ```text
  http://localhost:8082/app/fac-admin
  ```

  If it loads, FAC is installed and the desk page is working.

### 8.3 FAC API endpoint check (without OAuth)

If you hit:

```bash
curl -I "http://localhost:8082/api/method/frappe_assistant_core.api.fac_endpoint.handle_mcp"
```

You’ll likely see:

```text
401 UNAUTHORIZED
```

✅ That is normal if you haven’t configured OAuth client/token yet. The route exists; it’s protected.

---

## 9) After restarting computer (how to start again)

### Start docker (Ubuntu/WSL)

```bash
sudo systemctl start docker
docker info | head
```

### Start ERPNext stack

```bash
cd ~/erp16_fac_hrms/frappe_docker
docker compose -p pwdstg -f compose.yaml up -d
docker compose -p pwdstg -f compose.yaml ps
```

Open:

```text
http://localhost:8082
```

---

## 10) Troubleshooting (fast mapping)

### A) Cannot connect to the Docker daemon

**Fix:**

```bash
sudo systemctl start docker
docker info
```

### B) `invalid reference format` for `frappe/erpnext:`

**Cause**: blank tag variables.

**Fix**:

- Use `.env` with `CUSTOM_IMAGE` and `CUSTOM_TAG`, or
- Always run with `--pull never` and custom image tag (and don’t refer to untagged images).

### C) `502 Bad Gateway` from nginx

Check:

```bash
docker compose -p pwdstg -f compose.yaml logs -n 80 --no-log-prefix frontend
docker compose -p pwdstg -f compose.yaml logs -n 80 --no-log-prefix backend
```

Common causes:

- Backend not ready yet (wait a bit, check backend logs).
- Wrong upstream in nginx template (should point to `backend:8000` in docker network).
- `$host` interpolation bug (fix to `$$host`).

### D) websocket `ECONNREFUSED 127.0.0.1:6379`

**Cause**: websocket connecting to local redis instead of docker redis service.

**Fix**: ensure websocket container uses `redis-socketio:6379` (service name), **not** `127.0.0.1`.

### E) configurator “Waiting … forever”

Do the **proven sequence**:

1. `up` infra
2. Run `configurator` foreground
3. Run `create-site` with profile `init`
4. Start the rest

---

## 11) Notes about MariaDB 10.6

- MariaDB **10.6** works well with ERPNext v16 in docker setups (it’s a common default).
- You only need to change DB version if:
  - You have a specific compatibility requirement, or
  - A Frappe official update demands it.

---

## 12) What’s “next phase” (optional)

- **OAuth Client setup** for FAC MCP access (later phase).
- **Production hardening**:
  - Persistent volumes + backups (e.g. `restic`)
  - Reverse proxy domain routing
  - SSL
  - Monitoring/log shipping

---

## Quick Reference Commands

### Status

```bash
docker compose -p pwdstg -f compose.yaml ps
```

### Logs

```bash
docker compose -p pwdstg -f compose.yaml logs -n 100 -f frontend
docker compose -p pwdstg -f compose.yaml logs -n 100 -f backend
docker compose -p pwdstg -f compose.yaml logs -n 100 -f websocket
```

### Stop

```bash
docker compose -p pwdstg -f compose.yaml down
```

### Hard clean (containers + volumes)

```bash
docker compose -p pwdstg -f compose.yaml down -v --remove-orphans
```
