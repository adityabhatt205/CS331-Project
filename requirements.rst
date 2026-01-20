Project Requirements
====================

Client
------
Owner of a Small Manufacturing Unit producing packaged consumer goods
(Soft Drinks).

Requirements Requested by Client
--------------------------------
- Tool to visualize the factory floor, showing the layout of machines and
  their operational status, allowing basic control of machines from a
  single location.
- Capability to handle basic scenarios automatically such as jams,
  machine faults, overheating, and downstream blockage.
- Support for virtual testing including fault scenarios and automation
  rules.
- Alert on-site team in case of abnormal events.
- Maintain logs for future analysis.

Core Functionalities
-------------------
1. Factory Floor Visualisation  
   - 2D map showing machines, conveyors, and stations.

2. Live Status and Values  
   - Machine states: Running, Idle, Fault  
   - Metrics: Speed, Item Count, Temperature

3. Control System  
   - Start/Stop conveyor belts and stations  
   - Increase/Decrease operational speed

4. Automation  
   - Execute predefined rules in response to predefined scenarios.

5. Alert and Notification  
   - Push alerts for faults, emergency stops, and automatic shutdowns
     to the on-site team.

6. History and Logs  
   - Store operational data and events for analysis.

7. Simulation  
   - Test automation logic and fault scenarios in a virtual environment.

Additional Requirements
-----------------------
- Role-based privileges with Authentication and Authorisation  
  (Operators, Supervisors, Admins).
- Rule Configuration Interface to create, modify, delete, and
  enable/disable automation rules.
- Mode switching between live mode and simulation mode.

Physical Components in the Unit
-------------------------------

Conveyor Belts
^^^^^^^^^^^^^
- Parameters:
  - Speed (Units per minute / RPM)
  - Direction
- Components:
  - Motors (RPM, temperature)
  - Sensors (item present, jam detected)

Stations (Machines)
^^^^^^^^^^^^^^^^^^
- Types:
  - Filling
  - Packaging
  - Inspection
  - Labeling
- Parameters:
  - Status
  - Item processed count
  - Rate of processing
- Sensors:
  - Item present
  - Jam detection

Other Sensors
^^^^^^^^^^^^^
- Jam detection sensors
- Temperature sensors
- Speed sensors
