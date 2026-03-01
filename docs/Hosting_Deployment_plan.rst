Single-Server FastAPI Hosting & Deployment Plan
===============================================

Host site
---------

- **Primary hosting (college / local server):**
  - Single Linux server (Ubuntu 20.04) hosts all microservices as independent processes.
  - Per-service port mapping (single-host example):
    - User Service  .......... `http://<server-ip>:8000`
    - Automation Service ..... `http://<server-ip>:8001`
    - Notification Service ... `http://<server-ip>:8002`
    - Simulation Service ..... `http://<server-ip>:8003`
    - Logging Service ........ `http://<server-ip>:8004`
  - **Nginx (API Gateway / reverse proxy)** runs on the same host and exposes a single public endpoint (ports 80/443) to clients.

- **Note (future scaling):**
  - Services are designed to be independently deployable; if load grows later they can be moved to separate servers or cloud VMs without changing the application design.

Deployment strategy (steps)
---------------------------

1. **Prepare host**
   - Provision the college server (Ubuntu 20.04 recommended).
   - Create a non-root deploy user:
     ```
     sudo adduser deploy
     sudo usermod -aG sudo deploy
     ```
   - Configure SSH key authentication and basic firewall (ufw).

2. **Install base packages**
   - Install runtime and utilities:
     ```
     sudo apt update
     sudo apt install -y python3.10 python3-venv python3-pip nginx postgresql git
     sudo apt install -y ntp ufw
     ```

3. **Directory layout & code checkout**
   - Create per-service directories under `/opt`:
     ```
     sudo mkdir -p /opt/user-service /opt/automation-service /opt/notification-service /opt/simulation-service /opt/logging-service
     sudo chown -R deploy:deploy /opt
     ```
   - Clone each service repository into its directory:
     ```
     git clone <repo-url> /opt/user-service
     ```

4. **Virtualenv & dependencies**
   - For each service:
     ```
     cd /opt/<service>
     python3 -m venv venv
     source venv/bin/activate
     pip install -r requirements.txt
     ```
   - Keep service-specific requirements files in each repo.

5. **Configure environment & databases**
   - Create `.env` files (outside VCS) with service configuration:
     - `DATABASE_URL`, `SECRET_KEY`, `AUTOMATION_URL`, etc.
   - Create separate databases (Postgres) for each service:
     - `UserDB`, `AutomationDB`, `LogDB`
   - Run migrations (Alembic / ORM scripts) per service.

6. **Process supervision (systemd)**
   - Create a `systemd` unit for each FastAPI service to run uvicorn:
     - Example unit `/etc/systemd/system/user-service.service`:
       ```ini
       [Unit]
       Description=User Service (FastAPI)
       After=network.target

       [Service]
       User=deploy
       WorkingDirectory=/opt/user-service
       EnvironmentFile=/opt/user-service/.env
       ExecStart=/opt/user-service/venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000 --workers 3
       Restart=on-failure
       RestartSec=5

       [Install]
       WantedBy=multi-user.target
       ```
   - Enable and start services:
     ```
     sudo systemctl enable user-service
     sudo systemctl start user-service
     ```

7. **Nginx as API Gateway / reverse proxy**
   - Configure Nginx to proxy paths to local service ports and expose HTTPS:
     - Example `location` blocks:
       ```
       location /api/users/     { proxy_pass http://127.0.0.1:8000/; }
       location /api/automation/ { proxy_pass http://127.0.0.1:8001/; }
       location /api/notify/    { proxy_pass http://127.0.0.1:8002/; }
       ```
   - Use Let’s Encrypt (certbot) to enable TLS for client ↔ gateway encryption.

8. **Inter-service API configuration**
   - Services communicate via REST/JSON over HTTP to `127.0.0.1:<port>` (internal calls).
   - Maintain stable OpenAPI/Swagger contracts (FastAPI auto-generates these).
   - Use health checks: each service exposes `/health` for Nginx/monitoring.

9. **Logging & monitoring**
   - Services send structured events to Logging Service endpoint (`POST /logs`) and also write to `systemd` journal.
   - Use `journalctl -u <service>` and cron-based alerts or simple scripts to monitor service health.

10. **Deploy / update workflow**
    - Pull new code, run migrations, restart service:
      ```
      git pull
      source venv/bin/activate
      pip install -r requirements.txt
      alembic upgrade head   # if using alembic
      sudo systemctl restart <service>
      ```

Security (minimal measures)
---------------------------------------

- **Expose only Nginx externally**:
  - Block direct access to service ports using `ufw`:
    ```
    sudo ufw allow 'Nginx Full'   # 80,443
    sudo ufw deny 8000:8010/tcp
    ```
- **HTTPS on gateway**:
  - Use Let’s Encrypt (certbot) for TLS termination at Nginx.
- **Token-based authentication**:
  - Enforce JWT tokens for user APIs; validate at gateway or per service using FastAPI dependencies.
- **Secrets management**:
  - Keep DB passwords and keys in `.env` owned by deploy user, not in source control.
- **SSH & admin access**:
  - Restrict SSH to admin IPs and use key-based authentication only.

Trade-offs & future scaling
---------------------------

- **Single-server pros (college-level)**:
  - Simple to deploy and manage on the college server.
  - Lower operational overhead; good for development and lab demonstrations.
- **Single-server cons**:
  - Single point of failure; limited horizontal scaling.
- **Future migration**:
  - Because services are independent processes with stable APIs, they can later be moved to separate servers or cloud VMs (or containerized) with minimal code changes.



