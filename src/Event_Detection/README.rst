Event Detection Service
=======================

.. image:: https://img.shields.io/badge/Python-3.12-blue?style=flat-square&logo=python
.. image:: https://img.shields.io/badge/FastAPI-0.115.0-009688?style=flat-square&logo=fastapi
.. image:: https://img.shields.io/badge/Database-SQLite-003B57?style=flat-square&logo=sqlite
.. image:: https://img.shields.io/badge/Architecture-Microservice-FF6B6B?style=flat-square

| **Digital Twin — Industrial Automation System**
| The **"Brain"** of the system. Ingests raw sensor data from production stations,
  evaluates it against a 17-rule fault detection engine, persists fault events to a
  local database, and automatically forwards alerts to the Notification Service.

----

.. contents:: Table of Contents
   :depth: 2
   :local:
   :backlinks: none

----

Overview
--------

The Event Detection Service is a standalone **FastAPI microservice** running on
port ``8001``. It is the entry point for all sensor data in the Digital Twin system.

**Responsibilities:**

- Accept sensor readings from production stations via REST API
- Evaluate each reading against 17 prioritised fault detection rules
- Persist every detected fault to a local SQLite database
- Forward fault alerts to the Notification Service via HTTP with automatic retries
- Expose fault history for querying and audit

The service operates **independently** — it has its own database, its own process,
and interacts with the Notification Service only through HTTP REST calls.

----

Architecture
------------

.. code-block:: text

    PLC / IoT Sensor  (simulated via curl)
            │
            │  POST /api/v1/sensor-data
            │  { station_id, conveyor_speed, item_count,
            │    temperature_c, fill_volume_ml, pressure_bar ... }
            ▼
    ┌────────────────────────────────────────────┐
    │           EVENT DETECTION SERVICE          │
    │                                            │
    │   ┌──────────┐      ┌──────────────────┐   │
    │   │ REST API │─────>│  Rules Engine    │   |
    │   │ (FastAPI)│      │  (17 rules)      │   │
    │   └──────────┘      └──────────────────┘   │
    │         │                    │             │
    │         ▼                    ▼             │
    │   ┌──────────┐      ┌──────────────────┐   │
    │   │automation│      │   HTTP Client    │   │
    │   │   .db    │      │ (httpx+tenacity) │   │
    │   └──────────┘      └──────────────────┘   │
    │                              │             │
    └──────────────────────────────┼─────────────┘
                                   │
                                   │  POST /api/v1/alerts
                                   ▼
                        Notification Service :8002

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
     - Validates incoming sensor JSON — rejects malformed data automatically
   * - ``sqlalchemy``
     - 2.0.36
     - ORM layer for all database read/write operations
   * - ``aiosqlite``
     - 0.20.0
     - Async SQLite driver so DB operations never block the server
   * - ``httpx``
     - 0.27.2
     - Async HTTP client for calling the Notification Service
   * - ``tenacity``
     - 9.0.0
     - Automatic retry with exponential backoff on inter-service calls
   * - ``python-dotenv``
     - 1.0.1
     - Loads ``.env`` file into environment at startup

----

Project Structure
-----------------

.. code-block:: text

    event_detection_service/
    ├── main.py              ← Entire service — rules engine, DB, API, HTTP client
    ├── requirements.txt     ← All dependencies
    ├── .env                 ← Thresholds and config (never commit)
    └── automation.db        ← Auto-created SQLite database on first run

----

API Endpoints
-------------

POST ``/api/v1/sensor-data``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The core endpoint. Receives a sensor reading, runs it through the rules engine,
persists any detected fault, and triggers a notification.

**Request Body:**

.. code-block:: json

    {
      "station_id": "FILL-01",
      "conveyor_speed": 15.0,
      "item_count": 0,
      "temperature_c": 25.0,
      "fill_volume_ml": 340.0,
      "pressure_bar": 3.2,
      "vibration_g": 1.5,
      "motor_current_amps": 10.0,
      "motor_rated_amps": 12.0,
      "bottles_inspected": 100,
      "bottles_rejected": 3,
      "label_feed_ok": true,
      "cap_feed_ok": true,
      "co2_pressure_bar": 3.0,
      "emergency_stop_triggered": false
    }

.. note::

   All fields except ``station_id``, ``conveyor_speed``, ``item_count``,
   and ``temperature_c`` are **optional**. Omitted fields simply skip the
   rules that depend on them.

**Response — Fault Detected:**

.. code-block:: json

    {
      "station_id": "FILL-01",
      "fault_detected": true,
      "event_type": "jam",
      "severity": "critical",
      "description": "[FILL-01] JAM detected: conveyor at 15.0 units/min but item count is 0.",
      "notification_sent": true,
      "event_id": 1
    }

**Response — No Fault:**

.. code-block:: json

    {
      "station_id": "FILL-01",
      "fault_detected": false,
      "event_type": "normal",
      "severity": "info",
      "description": "[FILL-01] All parameters nominal.",
      "notification_sent": false,
      "event_id": null
    }

----

GET ``/api/v1/events``
~~~~~~~~~~~~~~~~~~~~~~~

Returns persisted fault event history from the database.

**Query Parameters:**

.. list-table::
   :header-rows: 1
   :widths: 20 15 15 50

   * - Parameter
     - Type
     - Default
     - Description
   * - ``station_id``
     - string
     - —
     - Filter results to a specific station
   * - ``limit``
     - integer
     - 50
     - Max records to return (max: 500)

**Example:**

.. code-block:: bash

    curl "http://localhost:8001/api/v1/events?station_id=FILL-01&limit=20"

----

GET ``/health``
~~~~~~~~~~~~~~~~

Returns service status.

.. code-block:: json

    {
      "status": "ok",
      "service": "automation"
    }

----

Rules Engine
------------

The rules engine is the core of this service. It evaluates 17 rules in strict
priority order — the **first matching rule wins** and its result is returned.
No fault detected means the reading is normal.

.. list-table::
   :header-rows: 1
   :widths: 8 35 35 15

   * - Priority
     - Rule
     - Condition
     - Severity
   * - 1
     - Emergency Stop
     - ``emergency_stop_triggered = true``
     - EMERGENCY
   * - 2
     - Extreme Overheat
     - ``temperature_c >= 110°C``
     - EMERGENCY
   * - 3
     - Overheat Critical
     - ``temperature_c >= 90°C``
     - CRITICAL
   * - 4
     - Pressure Critical
     - ``pressure_bar >= 6.0``
     - CRITICAL
   * - 5
     - Motor Overload
     - ``current >= 130% of rated``
     - CRITICAL
   * - 6
     - Vibration Critical
     - ``vibration_g >= 6.0``
     - CRITICAL
   * - 7
     - JAM Detection
     - ``item_count = 0`` AND ``conveyor_speed > 0``
     - CRITICAL
   * - 8
     - Label Feed Fault
     - ``label_feed_ok = false``
     - CRITICAL
   * - 9
     - Cap Feed Fault
     - ``cap_feed_ok = false``
     - CRITICAL
   * - 10
     - Underfill
     - ``fill_volume_ml < 330``
     - CRITICAL
   * - 11
     - High Rejection Rate
     - ``rejected / inspected >= 15%``
     - CRITICAL
   * - 12
     - Overheat Warning
     - ``temperature_c >= 70°C``
     - WARNING
   * - 13
     - Pressure Warning
     - ``pressure_bar >= 4.5``
     - WARNING
   * - 14
     - Conveyor Overspeed
     - ``conveyor_speed > 100 units/min``
     - WARNING
   * - 15
     - Vibration Warning
     - ``vibration_g >= 3.0``
     - WARNING
   * - 16
     - Overfill
     - ``fill_volume_ml > 370``
     - WARNING
   * - 17
     - CO2 Pressure Low
     - ``co2_pressure_bar < co2_min_bar``
     - WARNING

.. note::

   All thresholds are configurable via environment variables. No code change
   is needed to adjust a threshold — update ``.env`` and restart the service.

**Adding a new rule** requires only two steps:

1. Write a function: ``def rule_name(p: SensorPayload) -> Optional[RuleResult]``
2. Append it to the ``RULES`` list at the desired priority position

----

Inter-Service Communication
----------------------------

When a fault is detected, the service automatically calls the Notification
Service via HTTP POST. This is handled by the ``notify()`` function using
``httpx`` wrapped with ``tenacity`` for resilience.

.. code-block:: text

    Retry Strategy:
    ├── Max attempts : 3
    ├── Backoff      : exponential (1s → 2s → 4s)
    └── Retries on   : ConnectError, TimeoutException

If all retries fail, the fault is still saved to the database with
``notified = false``. The system **never loses a fault record** due to
a network failure.

----

Setup & Run
-----------

Step 1 — Create virtual environment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    cd event_detection_service
    python3 -m venv venv
    source venv/bin/activate

Step 2 — Install dependencies
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    pip install -r requirements.txt

Step 3 — Configure environment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Create a ``.env`` file in the service directory:

.. code-block:: ini

    # Notification Service URL
    NOTIFICATION_SERVICE_URL=http://localhost:8002

    # Temperature thresholds (Celsius)
    TEMP_WARN_C=70
    TEMP_CRIT_C=90
    TEMP_EXTREME_C=110

    # Pressure thresholds (bar)
    PRESSURE_WARN_BAR=4.5
    PRESSURE_CRIT_BAR=6.0

    # Fill volume (millilitres)
    FILL_UNDERFILL_ML=330
    FILL_OVERFILL_ML=370

    # Conveyor speed (units/min)
    CONVEYOR_MAX_SPEED=100

    # Vibration (G-force)
    VIBRATION_WARN_G=3.0
    VIBRATION_CRIT_G=6.0

    # Vision rejection rate (decimal)
    REJECT_RATE_WARN=0.05
    REJECT_RATE_CRIT=0.15

    # Retry config
    HTTP_RETRY_ATTEMPTS=3

Step 4 — Run the service
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    python3 main.py

**Expected output:**

.. code-block:: text

    INFO  Automation Service ready on port 8001

Interactive API docs available at:

.. code-block:: text

    http://localhost:8001/docs

----

Environment Variables
---------------------

.. list-table::
   :header-rows: 1
   :widths: 30 25 45

   * - Variable
     - Default
     - Description
   * - ``NOTIFICATION_SERVICE_URL``
     - ``http://localhost:8002``
     - URL of the Notification Service
   * - ``DATABASE_URL``
     - ``sqlite+aiosqlite:///./automation.db``
     - Database connection string
   * - ``HTTP_RETRY_ATTEMPTS``
     - ``3``
     - Max retries for inter-service HTTP calls
   * - ``TEMP_WARN_C``
     - ``70``
     - Overheat warning threshold (°C)
   * - ``TEMP_CRIT_C``
     - ``90``
     - Overheat critical threshold (°C)
   * - ``TEMP_EXTREME_C``
     - ``110``
     - Extreme overheat / emergency threshold (°C)
   * - ``PRESSURE_WARN_BAR``
     - ``4.5``
     - Pressure warning threshold (bar)
   * - ``PRESSURE_CRIT_BAR``
     - ``6.0``
     - Pressure critical threshold (bar)
   * - ``FILL_UNDERFILL_ML``
     - ``330``
     - Minimum acceptable fill volume (ml)
   * - ``FILL_OVERFILL_ML``
     - ``370``
     - Maximum acceptable fill volume (ml)
   * - ``CONVEYOR_MAX_SPEED``
     - ``100``
     - Maximum conveyor speed (units/min)
   * - ``VIBRATION_WARN_G``
     - ``3.0``
     - Vibration warning threshold (G)
   * - ``VIBRATION_CRIT_G``
     - ``6.0``
     - Vibration critical threshold (G)
   * - ``REJECT_RATE_WARN``
     - ``0.05``
     - Bottle rejection rate warning (5%)
   * - ``REJECT_RATE_CRIT``
     - ``0.15``
     - Bottle rejection rate critical (15%)

----

Test Scenarios
--------------

Use these ``curl`` commands to trigger each fault type:

**JAM Detection:**

.. code-block:: bash

    curl -s -X POST http://localhost:8001/api/v1/sensor-data \
      -H "Content-Type: application/json" \
      -d '{"station_id":"FILL-01","conveyor_speed":15,"item_count":0,
           "temperature_c":25,"label_feed_ok":true,"cap_feed_ok":true}'

**Critical Overheat:**

.. code-block:: bash

    curl -s -X POST http://localhost:8001/api/v1/sensor-data \
      -H "Content-Type: application/json" \
      -d '{"station_id":"BOIL-02","conveyor_speed":10,"item_count":8,
           "temperature_c":95,"label_feed_ok":true,"cap_feed_ok":true}'

**Emergency Stop:**

.. code-block:: bash

    curl -s -X POST http://localhost:8001/api/v1/sensor-data \
      -H "Content-Type: application/json" \
      -d '{"station_id":"CAP-01","conveyor_speed":0,"item_count":0,
           "temperature_c":30,"emergency_stop_triggered":true,
           "label_feed_ok":true,"cap_feed_ok":true}'

**Motor Overload:**

.. code-block:: bash

    curl -s -X POST http://localhost:8001/api/v1/sensor-data \
      -H "Content-Type: application/json" \
      -d '{"station_id":"CONV-03","conveyor_speed":10,"item_count":5,
           "temperature_c":40,"motor_current_amps":18.5,
           "motor_rated_amps":12,"label_feed_ok":true,"cap_feed_ok":true}'

**Query fault history:**

.. code-block:: bash

    curl "http://localhost:8001/api/v1/events?limit=10"

----

.. warning::

   Never commit your ``.env`` file to version control.
   The ``.gitignore`` is already configured to exclude it.
