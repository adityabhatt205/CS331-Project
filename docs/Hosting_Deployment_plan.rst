Hosting and Deployment Plan
===========================

Host site
---------

- **Primary hosting option (local):**
  - Deploy services on one or more local Linux servers/VMs (Ubuntu 20.04).
  - Example mapping (single-factory, small-scale):
    - `Server-1` : User Service (port 8000), Notification Service (8002)
    - `Server-2` : Automation Service (port 8001), Device Integration
    - `Server-3` : Simulation Service (port 8003), Logging Service (port 8004)
- **Alternate hosting option (cloud VM):**
  - Use basic cloud VMs (one VM per service) on AWS EC2 / Azure VM / GCP Compute Engine.
  - Same per-service port mapping as above; use cloud VM public IPs + a simple load balancer for scalable services.

Deployment strategy (steps)
---------------------------

1. **Prepare hosts**
   - Provision Linux servers or cloud VMs.
   - Create a deployment user (non-root) and configure SSH access.

2. **Install runtime & dependencies**
   - Install Python 3.10+, pip, PostgreSQL (or chosen DB), Nginx, and a process manager (systemd or supervisor).
   - Configure time sync (ntp/chrony) and basic OS updates.

3. **Create per-service directories**
   - Place each microservice repository under `/opt/<service-name>/`.
   - Example: `/opt/user-service`, `/opt/automation-service`, `/opt/logging-service`.

4. **Virtual environment & install**
   - Create a Python virtualenv per service: `python -m venv venv` → `venv/bin/pip install -r requirements.txt`.
   - Configure environment variables via a `.env` file (DB URL, secret keys).


5. **Configure databases**
   - Create separate databases for each service (UserDB, AutomationDB, LogDB).
   - Apply migrations and seed initial data (if any).

6. **Service process management**
   - Create `systemd` service unit files (or use `supervisord`) to run each FastAPI app on its assigned port:
     - `User Service` → `localhost:8000`
     - `Automation Service` → `localhost:8001`
     - `Notification Service` → `localhost:8002`
     - `Simulation Service` → `localhost:8003`
     - `Logging Service` → `localhost:8004`
   - Enable auto-start and restart on failure.

7. **API Gateway / Reverse proxy**
   - Configure Nginx (or a small API gateway) on the front-facing host:
     - Route `/api/users/*` → `http://server-1:8000`
     - Route `/api/automation/*` → `http://server-2:8001`
     - Expose only the gateway to the public network; keep service ports internal.
   - Provide a single client entry point and centralize CORS and rate-limit settings.


