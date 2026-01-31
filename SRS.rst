1. Introduction
===============

Introduction
============

1.1 Purpose
-----------

This Software Requirements Specification (SRS) document describes the
requirements of the *Factory Floor Visualization and Control System* for a
small manufacturing unit producing packaged consumer goods (soft drinks).

The purpose of this document is to clearly define the system’s functionality,
scope, and constraints so that all stakeholders share a common understanding
of the system before design, development, and testing activities begin.

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

The Factory Floor Visualization and Control System is used to monitor, control,
and analyze factory floor operations from a centralized interface.

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

The system provides a digital supervisory view of the factory floor to improve
operational efficiency, fault handling, and decision-making.

The product includes the following capabilities:

- 2D visualization of machines, conveyor belts, and stations
- Real-time monitoring of machine states and sensor values
- Manual control of belts and stations, including start, stop, and speed
  adjustment
- Rule-based automation to respond to predefined scenarios such as jams,
  overheating, and downstream blockages
- Alert and notification mechanisms for abnormal and emergency events
- Logging and history management for future analysis
- Simulation mode for testing automation rules and fault conditions

The system functions as a supervisory control layer and does not replace
low-level industrial controllers such as PLCs.

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
     - Machine that performs a specific operation such as Filling,
       Packaging, Inspection, or Labeling
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

3.1.1 Numbered and Described
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

3.1.2 EARS Format
^^^^^^^^^^^^^^^^^
When [event], the system shall [response]

3.1.3 Specification by Example / BDD
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
(e.g., Gherkin)


3.2 Non-Functional Requirements
-------------------------------

3.2.1 Performance
^^^^^^^^^^^^^^^^^
Example: 95% of requests shall return in under 2 seconds

3.2.2 Security
^^^^^^^^^^^^^^
Example: Only authenticated users can access admin API

3.2.3 Usability, Reliability, Compliance
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


3.3 External Interface Requirements
-----------------------------------

3.3.1 Performance Requirements
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

3.3.2 Safety Requirements
^^^^^^^^^^^^^^^^^^^^^^^^^

3.3.3 Security Requirements
^^^^^^^^^^^^^^^^^^^^^^^^^^^

3.3.4 Software Quality Attributes
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

3.3.5 Business Rules
^^^^^^^^^^^^^^^^^^^^


3.4 System Features
-------------------



4. Other Requirements
=====================

4.1 Database Requirements
-------------------------

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


