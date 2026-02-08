1. Introduction
===============

Introduction
============

1.1 Purpose
-----------

This Software Requirements Specification (SRS) document describes the requirements of the *Factory Floor Visualization and Control System* for a small manufacturing unit producing packaged consumer goods (soft drinks).

The purpose of this document is to clearly define the system's functionality, scope, and constraints so that all stakeholders share a common understanding of the system before design, development, and testing activities begin.

1.2 Intended Audience
---------------------

This document is intended for the following stakeholders:

- Factory Owner (Client)
- Software Developers
- System Testers and Quality Assurance Engineers
- System Integrators
- Maintenance and Support Personnel
- Academic Evaluators and Instructors

1.3 Intended Use
----------------

The Factory Floor Visualization and Control System is used to monitor, control, and analyze factory floor operations from a centralized interface.

Authorized users use the system to:

- Visualize the factory layout and operational status of machines
- Monitor live values such as speed, temperature, and item counts
- Control conveyor belts and processing stations
- Automatically handle predefined fault and abnormal scenarios
- Receive alerts and notifications during critical events
- Review historical logs for diagnostics and performance analysis
- Test automation logic and fault scenarios using a simulation mode

1.4 Product Scope
-----------------

The system provides a digital supervisory view of the factory floor to improve operational efficiency, fault handling, and decision-making.

The product includes the following capabilities:

- 2D visualization of machines, conveyor belts, and stations
- Real-time monitoring of machine states and sensor values
- Manual control of belts and stations, including start, stop, and speed adjustment
- Rule-based automation to respond to predefined scenarios such as jams, overheating, and downstream blockages
- Alert and notification mechanisms for abnormal and emergency events
- Logging and history management for future analysis
- Simulation mode for testing automation rules and fault conditions

The system functions as a supervisory control layer and does not replace low-level industrial controllers such as PLCs.

1.5 Definitions and Acronyms
----------------------------

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Term / Acronym
     - Description
   * - SRS
     - Software Requirements Specification
   * - Factory Floor Visualization
     - Graphical 2D representation of machines, conveyors, and stations
   * - Conveyor Belt
     - Mechanized belt used to transport items between stations
   * - Station
     - Machine that performs a specific operation such as Filling, Packaging, Inspection, or Labeling
   * - RPM
     - Revolutions Per Minute, indicating motor speed
   * - Automation Rule
     - Predefined condition-action logic executed automatically by the system
   * - Live Mode
     - Mode in which the system interacts with real factory equipment
   * - Simulation Mode
     - Mode used to test automation logic and fault scenarios virtually
   * - Jam Detection
     - Sensor-based detection of item blockage on belts or stations
   * - RBAC
     - Role-Based Access Control for managing user permissions
   * - Alert
     - Notification generated in response to abnormal or critical events


2. Overall Description
======================

This system is intended for a small manufacturing unit producing packaged consumer goods (soft drinks). It focuses on real-time monitoring, basic control, rule-based automation, alerting, and simulation of industrial processes using a 2D digital representation of the factory floor.


2.1 User Needs
--------------

The primary users of the system are the owner and on-site personnel of a small manufacturing unit. Their needs are outlined below.

* The user needs a **centralized visual interface** to view the factory floor layout and monitor the operational status of machines, conveyors, and stations in real time.
* The user needs the ability to **remotely control basic machine operations**, such as starting and stopping conveyor belts and adjusting operating speeds.
* The user needs the system to **automatically handle common fault scenarios**, including conveyor jams, machine faults, overheating, and downstream blockages, without requiring immediate manual intervention.
* The user needs **real-time alerts and notifications** to be generated when abnormal events or critical faults occur.
* The user needs the system to **maintain historical logs** of machine states, faults, and automation actions for later analysis and decision-making.
* The user needs a **simulation mode** that allows testing of automation rules and fault scenarios in a virtual environment before applying them to the live system.
* Different users need **role-based access control**, ensuring that operators, supervisors, and administrators have appropriate permissions based on their responsibilities.
* Supervisors and administrators need a **rule configuration interface** to create, modify, enable, or disable automation rules as required.
* The user needs the ability to **switch between live mode and simulation mode** in a controlled and safe manner.


2.2 Assumptions and Dependencies
--------------------------------

The following assumptions and dependencies have been considered during the design and development of the system:

* The manufacturing unit is a **small-scale facility**, and the system is not intended to replace full-scale industrial SCADA solutions.
* The digital twin represents the **logical and operational state** of the plant using a 2D visualization rather than a detailed 3D physical model.
* All sensors, machines, and conveyors are **simulated in software**, and no real industrial hardware or PLC integration is required.
* Sensor data such as temperature, speed, jam detection, and item count are assumed to be **available or generated virtually** by the system.
* Automation is implemented using **deterministic rule-based logic** (If–Then conditions) and does not involve machine learning or artificial intelligence.
* The system assumes a **stable network connection** between backend services and the frontend dashboard.
* Alerts are assumed to be delivered through **software-based notification mechanisms** (dashboard alerts, logs), not physical alarms.
* The system depends on standard software components such as a database for logging, backend services for automation and control, and a frontend interface for visualization and interaction.
* The system is intended for **educational and demonstrative purposes** as part of a software engineering laboratory project.


3. System Features and Requirements
===================================

3.1 Functional Requirements
---------------------------
This section describes the functional behavior of the system. Each requirement
defines what the system does under specific conditions.


3.1.1 Numbered and Described
^^^^^^^^^^^^^^^^^^^^^^^^^^^^
FR-1: Factory Floor Visualization  
The system displays a 2D layout of the factory floor, showing conveyor belts,
stations, and their current operational status.

FR-2: Live Status Monitoring  
The system shows live machine states such as Running, Idle, or Fault, along
with values like speed, temperature, and item count.

FR-3: Machine and Conveyor Control  
The system allows authorized users to start, stop, and adjust the speed of
conveyor belts and stations.

FR-4: Automation Handling  
The system executes predefined automation rules when specific fault or
operational conditions occur.

FR-5: Alerts and Notifications  
The system generates alerts for abnormal events such as jams, overheating,
or emergency shutdowns.

FR-6: Logging and History  
The system records operational events and sensor data for future analysis.

FR-7: Simulation Mode  
The system provides a simulation mode to test automation logic and fault
scenarios without affecting live operations.


3.1.2 EARS Format
^^^^^^^^^^^^^^^^^
When [event], the system shall [response]

- When a jam is detected on a conveyor belt, the system stops the affected belt
  and generates an alert.
- When a machine temperature exceeds the safe limit, the system triggers an
  automatic shutdown and notifies the on-site team.
- When a downstream station is unavailable, the system pauses upstream
  conveyors to prevent item buildup.
- When the system operates in simulation mode, the system processes virtual
  sensor inputs instead of real hardware data.


3.1.3 Specification by Example / BDD
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
(e.g., Gherkin)

**Scenario: Conveyor jam handling**

Given the conveyor belt is running  
And items move through the belt  
When a jam is detected  
Then the system stops the conveyor belt  
And the system sends an alert to the operators  

**Scenario: Simulation mode execution**

Given the system is in simulation mode  
When a fault scenario is triggered  
Then the system executes automation rules  
And no real machines are affected 


3.2 Non-Functional Requirements
-------------------------------
This section defines quality attributes and constraints of the system.

3.2.1 Performance
^^^^^^^^^^^^^^^^^

* The visualization must work with a minimum of 30 frames per second (FPS).

Example: 95% of requests shall return in under 2 seconds

3.2.2 Security
^^^^^^^^^^^^^^

- The system allows access only to authenticated users.
- The system enforces role-based access control for Operators, Supervisors,
  and Administrators.
- Only administrators access system configuration and automation rules.

3.2.3 Usability, Reliability, Compliance
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- The user interface remains simple and easy to understand.
- The system continues operating during minor faults without crashing.
- The system maintains logs to support audits and analysis.
- The system follows basic industrial safety and data protection practices.


3.3 External Interface Requirements
-----------------------------------

3.3.1 Performance Requirements
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
- The system communicates with sensors and machines with minimal delay.
- Data exchange supports continuous monitoring without loss of updates.


3.3.2 Safety Requirements
^^^^^^^^^^^^^^^^^^^^^^^^^
- The system supports emergency stop scenarios.
- The system prevents unsafe operations during fault conditions.
- The system avoids conflicting control commands.

3.3.3 Security Requirements
^^^^^^^^^^^^^^^^^^^^^^^^^^^
- External interfaces accept requests only from authorized sources.
- Communication between system components uses secure channels.


3.3.4 Software Quality Attributes
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- Reliability: The system operates consistently under normal conditions.
- Maintainability: The system allows easy updates to rules and configurations.
- Scalability: The system supports adding new machines and sensors.

3.3.5 Business Rules
^^^^^^^^^^^^^^^^^^^^
- Only supervisors and administrators modify automation rules.
- Simulation mode is disabled for regular operators.
- Live mode and simulation mode do not operate simultaneously.


3.4 System Features
-------------------
The system includes the following major features:

- Factory floor visualization
- Live monitoring of machines and sensors
- Centralized control of belts and stations
- Rule-based automation
- Alert and notification handling
- Historical logs and analysis
- Simulation for testing and validation



4. Other Requirements
=====================

4.1 Database Requirements
-------------------------
The system uses a centralized database to store operational and configuration
data.

The database stores the following information:

- User accounts, roles, and access privileges
- Machine and conveyor configuration details
- Automation rules and their current status
- System logs, alerts, and event history
- Simulation data used for testing scenarios

The database ensures data consistency and supports read and write operations
in near real time. Logged data remains available for future analysis and
troubleshooting.

4.2 Legal and Regulatory Requirements
-------------------------------------

4.3 Internationalization and Localization
-----------------------------------------

4.4 Risk Management (FMEA Matrix)
---------------------------------



5. Appendices
=============

5.1 Glossary
------------

5.2 Use Cases and Diagrams
--------------------------

5.3 To Be Determined (TBD) List
-------------------------------




