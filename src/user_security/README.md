# User Security Module

## Overview

The User Security module provides comprehensive Role-Based Access Control (RBAC) for the Factory Floor System. It implements database-persistent authentication, authorization, session management, and user administration functionality with enterprise-grade security features.

## Architecture

### Core Components

#### Database Layer
- **database.py**: SQLite database with comprehensive schema for users, sessions, audit logs, and system settings
- Connection pooling and transaction management
- Automatic schema migrations and backup capabilities

#### Security Layer
- **security.py**: PBKDF2 password hashing with salt (100,000 iterations)
- Password strength validation and rate limiting for brute force protection

#### Session Management
- **session_manager.py**: Database-persisted sessions with configurable timeouts
- Activity tracking and automatic cleanup of expired sessions

#### Authentication Manager
- **auth_manager.py**: Centralized user management with database-backed operations
- Comprehensive audit logging and system monitoring capabilities

#### User Classes
- **user.py**: Abstract base User class with database persistence
- **admin.py, supervisor.py, operator.py**: Role-specific implementations with enhanced security

#### Permission System
- **permissions.py**: Comprehensive permission enumeration and role-based mappings
- **decorators.py**: Security decorators for method protection

## User Roles and Permissions

### Admin (Full System Access)
- User Management: Create, delete, update users
- System Configuration: Database backup, system settings
- Automation: Complete automation rule management
- Machine Control: Full control over all machines
- Monitoring: Access to all logs, reports, and system data

### Supervisor (Elevated Operations Access)
- Approval Authority: Approve automation rules and critical operations
- Operations Monitoring: Comprehensive factory oversight
- Reporting: Export logs and generate reports
- Machine Control: Start/stop machines, emergency procedures
- Limited Admin: View users and some configuration access

### Operator (Basic Operations Access)
- Machine Operation: Start/stop machines, control conveyors
- Status Monitoring: View live status, sensor data
- Alert Management: View and acknowledge alerts
- Safety: Emergency stop capabilities

## Key Features

### Database Persistence
- All user data, sessions, and audit logs stored in SQLite database
- Automatic backup and recovery capabilities
- Database schema migrations and optimization

### Enhanced Security
- PBKDF2 password hashing with cryptographically secure salts
- Rate limiting for brute force protection
- Account lockout mechanisms
- Comprehensive audit logging for compliance

### Session Management
- Database-persisted sessions that survive application restarts
- Configurable session timeouts and activity tracking
- Multiple concurrent session support

### Monitoring and Statistics
- Real-time system statistics and health monitoring
- User activity tracking and audit trails
- Session analytics and cleanup utilities

## Usage Examples

### Basic Authentication Flow
```python
from user_security import auth_manager, Permission

# Authenticate user
session_id = auth_manager.authenticate_user("admin", "admin123", "192.168.1.100")

# Check permissions
if auth_manager.check_permission(session_id, Permission.START_MACHINE):
    # Perform authorized action
    pass

# Logout
auth_manager.logout_user("admin")
```

### User Management
```python
# Create new user (Admin only)
new_user = auth_manager.create_user(
    admin_session_id, "operator1", "SecurePass123!", "OPERATOR"
)

# Get system statistics
stats = auth_manager.get_system_stats()
print(f"Total users: {stats['total_users']}")

# Backup database
auth_manager.backup_database(admin_session_id, "backup.db")
```

### Using Security Decorators
```python
from user_security.decorators import require_permission, admin_only

@require_permission(Permission.START_MACHINE)
def start_machine(session_id, machine_id):
    print(f"Starting machine {machine_id}")

@admin_only()
def system_configuration(session_id, setting, value):
    print(f"Updating {setting} = {value}")
```

## Database Schema

### Users Table
- user_id, username, password_hash, salt, role
- created_at, last_login, failed_login_attempts
- locked_until, deleted_at

### Sessions Table
- session_id, user_id, username, ip_address
- created_at, last_activity, expires_at, is_active

### Audit Log Table
- id, user_id, username, action, resource
- ip_address, timestamp, success, details

### System Settings Table
- key, value, updated_at, updated_by

## Default Users

The system initializes with three default users:

1. **admin** / admin123 (ADMIN role)
2. **supervisor** / super123 (SUPERVISOR role)
3. **operator** / op123 (OPERATOR role)

## Files Structure

```
src/user_security/
├── __init__.py              # Module exports and initialization
├── database.py              # SQLite database operations
├── security.py              # Password hashing and rate limiting
├── session_manager.py       # Session management functionality
├── auth_manager.py          # Central authentication manager
├── user.py                  # Abstract User base class
├── admin.py                 # Admin user implementation
├── supervisor.py            # Supervisor user implementation
├── operator.py              # Operator user implementation
├── permissions.py           # Permission definitions and role mappings
├── decorators.py            # Security decorators and utilities
├── quick_test.py            # System integration test
└── README.md                # This documentation
```

## Testing

Run the system integration test:
```bash
python -m src.user_security.quick_test
```

## Configuration

### Database Configuration
- DATABASE_PATH: "factory_auth.db"
- CONNECTION_TIMEOUT: 30 seconds
- BACKUP_RETENTION: 30 days

### Security Configuration
- MIN_PASSWORD_LENGTH: 8
- PBKDF2_ITERATIONS: 100,000
- MAX_LOGIN_ATTEMPTS: 3
- LOCKOUT_DURATION: 30 minutes

### Session Configuration
- DEFAULT_SESSION_TIMEOUT: 1 hour
- MAX_CONCURRENT_SESSIONS: 5
- SESSION_CLEANUP_INTERVAL: 5 minutes

## Security Features

- Password hashing with PBKDF2 and cryptographically secure salts
- Rate limiting and account lockout for brute force protection
- Database-persistent sessions with automatic expiry
- Comprehensive audit logging for security compliance
- Regular session cleanup and database optimization
- Database backup capabilities for data protection

## Integration Points

The user security module provides authentication and authorization for:
- Digital Twin System operations
- Machine Controller access
- Alert and Notification System
- Production Monitoring and Reporting
- System Configuration and Maintenance

This implementation provides enterprise-grade security suitable for industrial factory floor environments while maintaining performance and usability.