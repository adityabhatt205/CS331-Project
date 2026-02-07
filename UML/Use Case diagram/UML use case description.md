# UML Use Case Diagram – Digital Twin Based Industrial Automation System

## Overview

This Use Case Diagram models the functional behavior of a **Digital Twin–Based Industrial Automation System** used in a small manufacturing environment.  
The diagram captures how different human users and external systems interact with the digital twin to monitor the factory floor, control machines, handle abnormal events, execute automation rules, and analyze system behavior.

The system acts as a centralized platform that integrates live sensor data, automation logic, machine control, alerting mechanisms, and simulation capabilities.

---

## Actors

### Human Actors

- **Admin**
  - Responsible for system-level access and high-level monitoring.
  - Can view the factory floor and live operational status.

- **Supervisor**
  - Oversees operations and handles abnormal situations.
  - Interacts with automation, alerts, and system logs.

- **Operator**
  - Performs day-to-day monitoring and machine interactions.
  - Has limited control and visibility compared to the supervisor.

### External System Actors

- **Machine / PLC System**
  - Represents physical machines and programmable logic controllers.
  - Executes control commands issued by the digital twin.

- **Sensor Network**
  - Provides real-time data such as temperature, speed, and fault signals.
  - Triggers detection of abnormal events.

- **Notification Service**
  - External service used to deliver alerts to users.
  - Can include email, SMS, or push notification systems.

---

## Core Use Cases

### Login
All interactive system functionalities require authentication.  
Login is modeled as a mandatory use case that is included by other user-initiated actions.

---

### View Factory Floor
Allows users to visualize the factory layout in a digital twin view.  
This use case includes viewing live operational data, as static visualization alone is insufficient.

---

### View Live Status
Displays real-time operational information such as machine states, production metrics, and sensor readings.  
This serves as the primary monitoring interface and acts as a base use case for advanced actions like control and automation.

---

### Control Machines
Enables authorized users to start, stop, or adjust machine parameters.  
This functionality is optional and extends the live monitoring process.  
Machine control inherently involves automation logic to ensure safe and consistent operation.

---

### Execute Automation Rules
Represents the execution of predefined automation logic in response to machine control actions or abnormal events.  
These rules define system behavior such as fault handling, safety actions, and automatic responses.

---

### Detect Abnormal Events
Triggered by the sensor network when abnormal conditions such as overheating, jams, or failures are detected.  
This use case always includes the execution of automation rules to decide the appropriate system response.

---

### Send Alerts
Responsible for notifying users about critical events or system actions.  
Alerting is conditional and occurs only when automation rules determine that user intervention or awareness is required.

---

### Run Simulation
Allows users to simulate factory behavior and automation rules in a virtual environment without affecting real machines.  
This is useful for testing, training, and validation purposes.

---

### View Logs
Provides access to historical system data, including events, alerts, automation actions, and simulation results.  
Logs support monitoring, debugging, and post-incident analysis.

---

## Use Case Relationships

### Include Relationships (`<<include>>`)
Include relationships represent mandatory functionality that must always be executed as part of another use case.

- Viewing the factory floor includes viewing live status.
- User actions such as monitoring and control include login.
- Detecting abnormal events includes executing automation rules.
- Running simulations includes viewing logs.
- Sending alerts includes interaction with the notification service.

---

### Extend Relationships (`<<extend>>`)
Extend relationships represent optional or conditional behavior that occurs only under specific circumstances.

- Controlling machines extends viewing live status.
- Sending alerts extends automation rule execution.
- Viewing logs extends alerting and simulation activities when further analysis is required.

---

## Design Rationale

The diagram separates **monitoring**, **control**, **automation**, and **analysis** concerns to maintain clarity and scalability.  
Mandatory system behavior is modeled using `<<include>>` relationships, while conditional or situational behavior is modeled using `<<extend>>`.

External systems such as sensors, machines, and notification services are modeled as actors to clearly distinguish system boundaries and responsibilities.

This structure ensures that the digital twin remains a reliable, safe, and extensible platform for industrial automation.

---


