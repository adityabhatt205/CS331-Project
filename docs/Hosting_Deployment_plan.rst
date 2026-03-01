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
