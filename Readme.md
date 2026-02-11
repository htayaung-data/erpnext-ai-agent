# ERPNext Factory Template (ERPNext v16 + HRMS + FAC)

This repo is a **template** to spin up a fresh ERPNext environment using a **prebuilt golden Docker image** hosted on GHCR.

**Golden Image includes:**

- Frappe `16.5.0`
- ERPNext `16.4.1`
- HRMS `16.4.0`
- Frappe Assistant Core (FAC) `2.3.1`

You will create a **new project folder per customer/project**, each with its **own DB/Redis/sites volumes**, so projects do not mix.

---

## 1) Create a New Project on the Same Computer (Local Factory Use)

### What you already have

- Docker Engine + Docker Compose installed and working
- Your golden image already built/pulled at least once
- This template repo cloned somewhere

### Goal

Create a brand-new ERPNext project folder that runs independently, using the same golden image.

---

### Step 1 — Create a new project folder (per project)

Example project name: `meet-electronics-stg`

```bash
mkdir -p ~/erp-projects/meet-electronics-stg
cd ~/erp-projects/meet-electronics-stg
```

---

### Step 2 — Copy template files into the project folder

Assuming you cloned this repo at `~/factory-template`:

```bash
cp ~/factory-template/compose.yaml .
cp ~/factory-template/.env.example .env
mkdir -p scripts
cp -r ~/factory-template/scripts/* ./scripts/
```

---

### Step 3 — Edit `.env` for this project

Open `.env` and set at least these:

```bash
nano .env
```

Minimum recommended values:

```env
# Project identity
PROJECT_NAME=meet-electronics-stg
SITE_NAME=frontend

# Web port for this project (must be unique per project)
HTTP_PORT=8082

# GHCR golden image
CUSTOM_IMAGE=ghcr.io/htayaung-data/erpnext-factory
CUSTOM_TAG=erp16.4.1-hrms16.4.0-fac2.3.1-frappe16.5.0
PULL_POLICY=if_not_present

# Passwords (change per project)
DB_ROOT_PASSWORD=admin
ADMIN_PASSWORD=admin
```

**Important:**

- If you run multiple projects at the same time, set different `HTTP_PORT` (e.g. `8082`, `8083`, `8084`...).
- You can keep `SITE_NAME=frontend` for all projects (it’s inside each project’s own volumes, so no collision).

---

### Step 4 — Start Docker (after reboot, if needed)

If you are in Ubuntu/WSL and Docker is not running:

```bash
sudo systemctl start docker
docker info
```

---

### Step 5 — Start infra first (DB + Redis)

```bash
export COMPOSE_PROJECT_NAME="$(grep '^PROJECT_NAME=' .env | cut -d= -f2)"

docker compose up -d db redis-cache redis-queue redis-socketio
docker compose ps
```

---

### Step 6 — Run configurator (writes `common_site_config`)

```bash
docker compose up configurator
```

It should exit with **code 0**.

---

### Step 7 — First-time only: create site and install apps

Run once per new project folder:

```bash
docker compose --profile init up create-site
```

**Expected behavior:**

- Creates site `frontend` (or your `SITE_NAME`)
- Installs: `erpnext`, `hrms`, `frappe_assistant_core`

---

### Step 8 — Start the full stack

```bash
docker compose up -d
docker compose ps
```

---

### Step 9 — Open ERPNext

Open in browser:

```text
http://localhost:8082
```

Login:

- **Username**: `Administrator`
- **Password**: your `ADMIN_PASSWORD`

---

### Step 10 — Quick checks (optional)

List apps:

```bash
docker compose exec backend bash -lc "bench --site frontend list-apps"
```

FAC UI:

```text
http://localhost:8082/app/fac-admin
```

---

### Day-to-day commands (same project folder)

**Stop:**

```bash
docker compose down
```

**Start:**

```bash
sudo systemctl start docker 2>/dev/null || true
docker compose up -d
```

**Logs:**

```bash
docker compose logs -f --tail=200 frontend
docker compose logs -f --tail=200 backend
docker compose logs -f --tail=200 websocket
```

---

## 2) Create a New Project on Another Computer (Fresh Machine Setup)

### Goal

On a new computer, you should be able to:

- Install Docker
- Clone this repo
- Pull the golden image from GHCR
- Create a project folder and run the same steps

---

### Step 1 — Install Docker + Compose

Install Docker Engine + Docker Compose for your OS.

After install, verify:

```bash
docker version
docker compose version
```

---

### Step 2 — Login to GHCR (required to pull private images)

If your GHCR image is private, login:

```bash
export GH_USER="htayaung-data"
echo "<YOUR_GITHUB_TOKEN>" | docker login ghcr.io -u "$GH_USER" --password-stdin
```

**Notes:**

- Token needs `read:packages` permission.
- If image is public, you can skip login.

---

### Step 3 — Pull the golden image

```bash
export TAG="erp16.4.1-hrms16.4.0-fac2.3.1-frappe16.5.0"
docker pull ghcr.io/htayaung-data/erpnext-factory:$TAG
docker images | grep erpnext-factory
```

---

### Step 4 — Clone the template repo

```bash
cd ~
git clone https://github.com/htayaung-data/ERPNext-template.git factory-template
cd factory-template
ls -lah
```

You should see:

- `compose.yaml`
- `.env.example`
- `scripts/`

---

### Step 5 — Create a new project folder (per project)

```bash
mkdir -p ~/erp-projects/project-1
cd ~/erp-projects/project-1
```

Copy template files:

```bash
cp ~/factory-template/compose.yaml .
cp ~/factory-template/.env.example .env
mkdir -p scripts
cp -r ~/factory-template/scripts/* ./scripts/
```

---

### Step 6 — Configure `.env` for this project

```bash
nano .env
```

Set at least:

```env
PROJECT_NAME=project-1
SITE_NAME=frontend
HTTP_PORT=8082

CUSTOM_IMAGE=ghcr.io/htayaung-data/erpnext-factory
CUSTOM_TAG=erp16.4.1-hrms16.4.0-fac2.3.1-frappe16.5.0
PULL_POLICY=if_not_present

DB_ROOT_PASSWORD=admin
ADMIN_PASSWORD=admin
```

---

### Step 7 — Start infra

```bash
export COMPOSE_PROJECT_NAME="$(grep '^PROJECT_NAME=' .env | cut -d= -f2)"

docker compose up -d db redis-cache redis-queue redis-socketio
docker compose ps
```

---

### Step 8 — Run configurator (must finish successfully)

```bash
docker compose up configurator
```

---

### Step 9 — First-time only: create site and install apps

```bash
docker compose --profile init up create-site
```

Wait until it finishes with **exit code 0**.

---

### Step 10 — Start full stack

```bash
docker compose up -d
docker compose ps
```

Open:

```text
http://localhost:8082
```

FAC UI:

```text
http://localhost:8082/app/fac-admin
```

---

### Reboot / restart notes (other computer)

After restart:

1. Ensure Docker is running.
2. Go into the project folder.
3. Run:

```bash
docker compose up -d
```

---

## Common mistakes

- **Port conflict**: if another service uses `8082`, change `HTTP_PORT` in `.env`.
- **Forgot GHCR login**: if pull fails, login again.
- **Re-running `create-site`**: do it only once per project. If you need a clean reset, remove volumes (see next).

---

## Full reset (danger: deletes this project data)

Only run inside the project folder you want to reset:

```bash
docker compose down -v
```

This deletes:

- Database data
- Redis data
- Site data

Then run the setup steps again (**infra → configurator → create-site → up**).
