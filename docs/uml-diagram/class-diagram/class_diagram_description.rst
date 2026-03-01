==============================================
UML Class Diagram Documentation
==============================================
Digital Twin–Based Industrial Automation System
==============================================


1. Overview
===========

This document describes the **UML Class Diagram** designed for the
*Digital Twin–Based Industrial Automation System*.

The class diagram captures the **structural aspects** of the software by
identifying key classes, their attributes, methods, visibility, and the
relationships among them.

The design emphasizes:

- Clear **separation of responsibilities**
- **Role-based access control** for security
- Modular and scalable architecture
- Alignment with the UML use case diagram


2. Design Principles Followed
=============================

- **Encapsulation**: Sensitive data is kept private
- **Inheritance**: Used to impose hierarchy among users
- **Modularity**: Each subsystem has a clear responsibility
- **Security-aware design**: Visibility modifiers are used intentionally
- **Traceability**: Classes map directly to system use cases


3. User Hierarchy and Security
==============================

3.1 Abstract Class: ``User``
----------------------------

The ``User`` class defines the common structure for all system users and
acts as the foundation for authentication and authorization.

**Attributes**

+---------------+----------+-------------+-------------------------------+
| Attribute     | Type     | Visibility  | Description                   |
+===============+==========+=============+===============================+
| userId        | int      | private     | Unique user identifier        |
+---------------+----------+-------------+-------------------------------+
| username      | String   | private     | Login username                |
+---------------+----------+-------------+-------------------------------+
| passwordHash  | String   | private     | Encrypted password            |
+---------------+----------+-------------+-------------------------------+
| role          | String   | protected   | Role used for authorization   |
+---------------+----------+-------------+-------------------------------+

**Methods**

+------------------+------------+----------------------------------------+
| Method           | Visibility | Description                            |
+==================+============+========================================+
| login()          | public     | Authenticates the user                 |
+------------------+------------+----------------------------------------+
| logout()         | public     | Ends the user session                  |
+------------------+------------+----------------------------------------+
| hasPermission()  | protected  | Checks role-based permissions          |
+------------------+------------+----------------------------------------+

Sensitive information is marked **private**, while authorization logic is
**protected** to allow controlled access by subclasses.


3.2 Specialized User Roles
--------------------------

**Admin**

- Manages users
- Configures automation rules

**Supervisor**

- Monitors factory operations
- Approves automation actions

**Operator**

- Controls machines
- Views live system status

**Relationship Used**

- ``Admin``, ``Supervisor``, and ``Operator`` **inherit** from ``User``,
  enforcing a clear hierarchy and role-based access control.


4. Visualization and Monitoring
===============================

FactoryFloorVisualization
-------------------------

Responsible for presenting the factory layout, machine states, and
simulation results.

**Attributes**

- ``layoutMap : String`` *(private)*

**Methods**

- ``renderFloor()`` *(public)*
- ``displayLiveStatus()`` *(public)*
- ``displaySimulationResult()`` *(public)*

Visualization is kept independent from control logic to improve
maintainability.


LiveStatus
----------

Represents real-time operational data.

**Attributes**

- temperature *(private)*
- speed *(private)*
- machineState *(private)*

**Method**

- ``updateStatus()`` *(public)*


5. Machines, PLC, and Sensors
=============================

Machine
-------

Represents a physical machine on the factory floor.

**Attributes**

- machineId *(private)*
- status *(private)*

**Methods**

- ``start()``, ``stop()``, ``adjustSpeed()`` *(public)*
- ``validateCommand()`` *(protected)*

Each machine is associated with:

- One PLC controller
- Multiple sensors


PLCController
-------------

Handles communication and control commands.

**Methods**

- ``sendControlCommand()`` *(public)*
- ``readMachineStatus()`` *(public)*
- ``authenticateCommand()`` *(protected)*


Sensor and SensorNetwork
------------------------

- Sensors collect physical measurements
- ``SensorNetwork`` aggregates sensor data

**Relationship Used**

- Aggregation (``o--``), since sensors can exist independently of the
  network.


6. Automation and Event Handling
================================

AutomationRule
--------------

Defines condition–action pairs for automation.

**Attributes**

- ruleId *(private)*
- condition *(private)*
- action *(private)*

**Method**

- ``evaluate()`` *(public)*


RuleEngine
----------

Executes automation rules.

**Methods**

- ``executeRules()`` *(public)*
- ``validateRule()`` *(protected)*

**Relationship Used**

- Aggregation with ``AutomationRule``, allowing dynamic rule management.


EventDetector
-------------

Detects abnormal or fault conditions.

**Method**

- ``detectAbnormalEvent()`` *(public)*


7. Alerts, Logs, and Simulation
===============================

NotificationService
-------------------

- Sends alerts and notifications

**Method**

- ``sendAlert()`` *(public)*


Log and LogManager
------------------

Used for audit trails and historical analysis.

**Log Attributes**

- logId *(private)*
- timestamp *(private)*
- message *(private)*

**LogManager Methods**

- ``storeLog()`` *(public)*
- ``retrieveLogs()`` *(public)*
- ``encryptLog()`` *(private)*

Logs are kept private to ensure confidentiality and integrity.


SimulationEngine
----------------

Allows virtual testing of factory scenarios.

**Method**

- ``runSimulation()`` *(public)*


8. Core System Controller
=========================

DigitalTwinSystem
-----------------

Acts as the **central coordinator** of all subsystems.

**Methods**

- ``processSensorData()`` *(public)*
- ``controlMachines()`` *(public)*
- ``triggerAutomation()`` *(public)*
- ``authenticateUser()`` *(protected)*

**Relationship Used**

- Composition (``*--``) with core subsystems, indicating strong ownership
  and lifecycle dependency.


9. Relationship Summary
=======================

+-------------------+------------------------------------------------------+
| Relationship Type | Used Between                                         |
+===================+======================================================+
| Inheritance       | User → Admin / Supervisor / Operator                 |
+-------------------+------------------------------------------------------+
| Aggregation       | Machine → Sensor, RuleEngine → AutomationRule        |
+-------------------+------------------------------------------------------+
| Composition       | DigitalTwinSystem → Core Modules                     |
+-------------------+------------------------------------------------------+
| Association       | User → DigitalTwinSystem                             |
+-------------------+------------------------------------------------------+

Cardinality is explicitly defined where applicable.
