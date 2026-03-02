Notification Service
====================

.. image:: https://img.shields.io/badge/Python-3.12-blue?style=flat-square&logo=python
.. image:: https://img.shields.io/badge/FastAPI-0.115.0-009688?style=flat-square&logo=fastapi
.. image:: https://img.shields.io/badge/SMTP-Gmail-EA4335?style=flat-square&logo=gmail
.. image:: https://img.shields.io/badge/Architecture-Microservice-FF6B6B?style=flat-square

| **Digital Twin — Industrial Automation System**
| The **"Voice"** of the system. Receives fault alerts from the Event Detection
  Service, routes them to the correct recipients based on severity, and dispatches
  styled HTML emails via Gmail SMTP — without blocking the main request thread.

----

.. contents:: Table of Contents
   :depth: 2
   :local:
   :backlinks: none

----

Overview
--------

The Notification Service is a standalone **FastAPI microservice** running on
port ``8002``. It is responsible for all outbound communication in the
Digital Twin system.

**Responsibilities:**

- Receive structured fault alerts from the Event Detection Service via REST API
- Resolve the correct email recipients based on alert severity
- Dispatch styled HTML alert emails asynchronously via Gmail SMTP
- Log every notification to a local SQLite database
- Provide real-time console output for every alert received

The service operates **independently** — it has its own database, its own
process, and is called by the Event Detection Service through HTTP only.

----

Architecture
------------

.. code-block:: text

    Event Detection Service
            │
            │  POST /api/v1/alerts
            │  { event_type, severity, station_id,
            │    description, sensor_snapshot }
            ▼
    ┌─────────────────────────────────────────────┐
    │           NOTIFICATION SERVICE              │
    │                                             │
    │  ┌─────────────┐    ┌───────────────────┐   │
    │  │  REST API   │───>│ Recipient Router  │   │
    │  │  (FastAPI)  │    │ (recipients.json) │   │
    │  └─────────────┘    └───────────────────┘   │
    │         │                     │             │
    │         ▼                     ▼             │
    │  ┌──────────────┐   ┌───────────────────┐   │
    │  │ notification │   │  Email Dispatcher │   │
    │  │    .db       │   │  (aiosmtplib)     │   │
    │  └──────────────┘   └───────────────────┘   │
    │                               │             │
    └───────────────────────────────┼─────────────┘
                                    │
                                    ▼
                           Gmail SMTP :587
                                    │
                                    ▼
                          📧 Recipient Inboxes

----

Tech Stack
----------

.. list-table::
   :header-rows: 1
   :widths: 20 15 50

   * - Library
     - Version
     - Purpose
   * - ``fastapi``
     - 0.115.0
     - REST API framework — creates and serves all endpoints
   * - ``uvicorn``
     - 0.30.6
     - ASGI server that runs the FastAPI application
   * - ``pydantic``
     - 2.9.2
     - Validates incoming alert JSON — rejects malformed requests automatically
   * - ``aiosmtplib``
     - 3.0.1
     - Async SMTP client for dispatching emails via Gmail
   * - ``sqlalchemy``
     - 2.0.36
     - ORM layer for all database read/write operations
   * - ``aiosqlite``
     - 0.20.0
     - Async SQLite driver so DB operations never block the server
   * - ``python-dotenv``
     - 1.0.1
     - Loads ``.env`` credentials file at startup

----

Project Structure
-----------------

.. code-block:: text

    notification_service/
    ├── main.py              ← Entire service in one file
    ├── recipients.json      ← Severity-to-recipient routing map
    ├── requirements.txt     ← All dependencies
    ├── .env                 ← SMTP credentials (never commit this)
    └── notification.db      ← Auto-created SQLite database on first run

----

API Endpoints
-------------

POST ``/api/v1/alerts``
~~~~~~~~~~~~~~~~~~~~~~~~

The primary endpoint. Called automatically by the Event Detection Service
when a fault is detected. Logs the alert, sends console output immediately,
and dispatches email in the background.

**Request Body:**

.. code-block:: json

    {
      "event_id": 1,
      "event_type": "jam",
      "severity": "critical",
      "station_id": "FILL-01",
      "description": "[FILL-01] JAM detected: conveyor at 15.0 units/min but item count is 0.",
      "sensor_snapshot": {
        "conveyor_speed": 15.0,
        "item_count": 0,
        "temperature_c": 25.0,
        "label_feed_ok": true,
        "cap_feed_ok": true
      }
    }

**Response:**

.. code-block:: json

    {
      "accepted": true,
      "log_id": 1,
      "channels_used": ["console", "email"],
      "email_sent": false,
      "email_recipients": ["admin@plant.com", "manager@plant.com"]
    }

.. note::

   ``email_sent`` is initially ``false`` and is updated to ``true``
   by the background task after SMTP delivery is confirmed.
   Check ``GET /api/v1/logs`` to see the final delivery status.

----

GET ``/api/v1/logs``
~~~~~~~~~~~~~~~~~~~~~

Returns notification history from the database.

**Query Parameters:**

.. list-table::
   :header-rows: 1
   :widths: 20 15 15 50

   * - Parameter
     - Type
     - Default
     - Description
   * - ``severity``
     - string
     - —
     - Filter by: ``info``, ``warning``, ``critical``, ``emergency``
   * - ``limit``
     - integer
     - 50
     - Max records to return (max: 500)

**Example:**

.. code-block:: bash

    curl "http://localhost:8002/api/v1/logs?severity=critical&limit=10"

----

POST ``/api/v1/recipients/reload``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Hot-reloads ``recipients.json`` without restarting the service.
Use this after editing recipient addresses during a live session.

.. code-block:: bash

    curl -X POST http://localhost:8002/api/v1/recipients/reload

**Response:**

.. code-block:: json

    {
      "reloaded": true,
      "routing_summary": {
        "emergency": 2,
        "critical": 1,
        "warning": 1,
        "info": 1
      }
    }

----

GET ``/health``
~~~~~~~~~~~~~~~~

Returns service status and SMTP configuration state.

.. code-block:: json

    {
      "status": "ok",
      "service": "notification",
      "email_enabled": true,
      "smtp_configured": true
    }

----

Recipient Routing
-----------------

Recipients are defined in ``recipients.json``. Edit this file to control
who receives notifications at each severity level.

.. code-block:: json

    {
      "emergency": ["plant-manager@company.com", "safety-officer@company.com"],
      "critical":  ["production-admin@company.com"],
      "warning":   ["shift-supervisor@company.com"],
      "info":      ["operator@company.com"]
    }

Severity Inheritance
~~~~~~~~~~~~~~~~~~~~~

Higher severity alerts automatically include recipients from all tiers above them:

.. list-table::
   :header-rows: 1
   :widths: 20 60

   * - Alert Severity
     - Who Receives the Email
   * - ``EMERGENCY``
     - emergency tier only
   * - ``CRITICAL``
     - critical tier + emergency tier
   * - ``WARNING``
     - warning tier + critical tier + emergency tier
   * - ``INFO``
     - all tiers

.. note::

   Duplicate addresses are automatically removed. If the same email
   appears in multiple tiers, that person receives only one email.

Hot Reload
~~~~~~~~~~

After editing ``recipients.json``, apply changes without restart:

.. code-block:: bash

    curl -X POST http://localhost:8002/api/v1/recipients/reload

----

Email System
------------

Dispatch Flow
~~~~~~~~~~~~~

.. code-block:: text

    Alert arrives at POST /api/v1/alerts
              │
              ├─▶ Console log printed immediately  (synchronous)
              │
              ├─▶ Recipients resolved from recipients.json
              │
              ├─▶ Log entry saved to notification.db
              │   (email_sent = false)
              │
              ├─▶ HTTP 200 response returned to Event Detection Service
              │
              └─▶ Background Task starts:
                        │
                        ├─▶ aiosmtplib sends HTML email via Gmail
                        │
                        └─▶ notification.db updated
                            (email_sent = true)

Non-Blocking Design
~~~~~~~~~~~~~~~~~~~~

Email dispatch uses **FastAPI BackgroundTasks**. The HTTP response is
returned to the Event Detection Service *before* the email is sent.
This ensures slow SMTP connections never delay fault detection or
block the production monitoring pipeline.

Email Format
~~~~~~~~~~~~~

Each alert email contains:

- Coloured header bar matched to severity (dark red → EMERGENCY, red → CRITICAL, orange → WARNING)
- Station ID, Event Type, and UTC timestamp
- Full fault description in a highlighted callout box
- Complete sensor snapshot table with all raw values
- Plain text fallback for mail clients that do not render HTML

Gmail Setup
~~~~~~~~~~~

.. code-block:: text

    Step 1 — Enable 2-Step Verification
            myaccount.google.com/security

    Step 2 — Generate App Password
            myaccount.google.com/apppasswords
            → Click "Create" → name it "digital-twin"
            → Copy the 16-character password

    Step 3 — Paste into .env
            SMTP_PASSWORD=abcd efgh ijkl mnop
            (spaces are fine — Gmail ignores them)

----

Setup & Run
-----------

Step 1 — Create virtual environment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    cd notification_service
    python3 -m venv venv
    source venv/bin/activate

Step 2 — Install dependencies
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    pip install -r requirements.txt

Step 3 — Configure environment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Create a ``.env`` file in the ``notification_service/`` directory:

.. code-block:: ini

    SMTP_HOST=smtp.gmail.com
    SMTP_PORT=587
    SMTP_USERNAME=your-email@gmail.com
    SMTP_PASSWORD=abcd efgh ijkl mnop
    SMTP_FROM=your-email@gmail.com
    SMTP_TLS=true
    EMAIL_ENABLED=true
    RECIPIENTS_FILE=recipients.json

Step 4 — Configure recipients
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Edit ``recipients.json`` and replace placeholder addresses with real inboxes.
For testing, use your own email in all four tiers.

Step 5 — Run the service
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    python3 main.py

**Expected output:**

.. code-block:: text

    INFO  Notification Service ready on port 8002
    INFO  Email enabled: True | SMTP: smtp.gmail.com:587

Interactive API docs available at:

.. code-block:: text

    http://localhost:8002/docs

----

Environment Variables
---------------------

.. list-table::
   :header-rows: 1
   :widths: 28 30 10 32

   * - Variable
     - Default
     - Required
     - Description
   * - ``SMTP_HOST``
     - ``smtp.gmail.com``
     - No
     - SMTP server hostname
   * - ``SMTP_PORT``
     - ``587``
     - No
     - SMTP port number
   * - ``SMTP_USERNAME``
     - —
     - **Yes**
     - Your Gmail address
   * - ``SMTP_PASSWORD``
     - —
     - **Yes**
     - Gmail App Password (16 characters)
   * - ``SMTP_FROM``
     - Same as USERNAME
     - No
     - Sender display address in email
   * - ``SMTP_TLS``
     - ``true``
     - No
     - Enable STARTTLS encryption
   * - ``EMAIL_ENABLED``
     - ``true``
     - No
     - Set ``false`` to disable email in development
   * - ``RECIPIENTS_FILE``
     - ``recipients.json``
     - No
     - Path to the recipient routing config
   * - ``DATABASE_URL``
     - ``sqlite+aiosqlite:///./notification.db``
     - No
     - Database connection string

----

How It Connects to the Event Detection Service
-----------------------------------------------

This service does **not** initiate any calls. The connection is strictly
one-directional:

.. code-block:: text

    Event Detection Service  ──POST /api/v1/alerts──▶  Notification Service

The Event Detection Service calls this service automatically every time a
fault is detected. The Notification Service only needs to be:

1. Running before the Event Detection Service starts
2. Reachable on port ``8002``

No configuration changes are required on the Notification Service side
to establish the connection.

----

Error Handling
--------------

The email dispatcher handles three distinct SMTP failure types with
specific log messages for each:

.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - Error
     - Log Message
   * - Wrong credentials
     - ``SMTP authentication failed for user '...'``
   * - Cannot reach Gmail
     - ``Cannot connect to SMTP server smtp.gmail.com:587``
   * - Any other SMTP error
     - ``SMTP error: <details>``

In all failure cases the notification is still **persisted to the database**
with ``email_sent = false``. No alert record is ever lost due to an SMTP failure.

----

.. warning::

   Never commit your ``.env`` file to version control.
   It contains your Gmail App Password.
   The ``.gitignore`` is already configured to exclude it.
