"""
Secure password utilities for the Factory Floor System.
Provides salted password hashing and verification using industry best practices.
"""

import hashlib
import secrets
import logging
from typing import Tuple
import time


class PasswordSecurity:
    """Secure password hashing and verification utilities."""
    
    def __init__(self, iterations: int = 100000, hash_algorithm: str = 'pbkdf2_hmac'):
        """
        Initialize password security manager.
        
        Args:
            iterations: Number of PBKDF2 iterations (default: 100,000)
            hash_algorithm: Hashing algorithm to use
        """
        self.iterations = iterations
        self.hash_algorithm = hash_algorithm
        self.salt_length = 32  # 256 bits
        self._logger = logging.getLogger(__name__)
    
    def generate_salt(self) -> bytes:
        """
        Generate a cryptographically secure random salt.
        
        Returns:
            Random salt bytes
        """
        return secrets.token_bytes(self.salt_length)
    
    def hash_password(self, password: str, salt: bytes = None) -> Tuple[str, str]:
        """
        Hash password with salt using PBKDF2.
        
        Args:
            password: Plain text password
            salt: Optional salt (generates new one if not provided)
            
        Returns:
            Tuple of (hex_encoded_hash, hex_encoded_salt)
        """
        if salt is None:
            salt = self.generate_salt()
        
        # Ensure salt is bytes
        if isinstance(salt, str):
            salt = bytes.fromhex(salt)
        
        # Use PBKDF2 with HMAC-SHA256
        password_bytes = password.encode('utf-8')
        password_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password_bytes,
            salt,
            self.iterations
        )
        
        return password_hash.hex(), salt.hex()
    
    def verify_password(self, password: str, stored_hash: str, stored_salt: str) -> bool:
        """
        Verify password against stored hash and salt.
        
        Args:
            password: Plain text password to verify
            stored_hash: Stored password hash (hex encoded)
            stored_salt: Stored salt (hex encoded)
            
        Returns:
            True if password is correct, False otherwise
        """
        try:
            # Convert hex strings back to bytes
            salt_bytes = bytes.fromhex(stored_salt)
            
            # Hash the provided password with the stored salt
            computed_hash, _ = self.hash_password(password, salt_bytes)
            
            # Use secure comparison to prevent timing attacks
            return self._secure_compare(computed_hash, stored_hash)
            
        except Exception as e:
            self._logger.error(f"Password verification error: {e}")
            return False
    
    def _secure_compare(self, a: str, b: str) -> bool:
        """
        Secure string comparison to prevent timing attacks.
        
        Args:
            a: First string
            b: Second string
            
        Returns:
            True if strings are equal, False otherwise
        """
        if len(a) != len(b):
            return False
        
        result = 0
        for x, y in zip(a, b):
            result |= ord(x) ^ ord(y)
        
        return result == 0
    
    def is_password_strong(self, password: str) -> Tuple[bool, List[str]]:
        """
        Check if password meets complexity requirements.
        
        Args:
            password: Password to check
            
        Returns:
            Tuple of (is_strong, list_of_issues)
        """
        issues = []
        
        if len(password) < 8:
            issues.append("Password must be at least 8 characters long")
        
        if not any(c.isupper() for c in password):
            issues.append("Password must contain at least one uppercase letter")
        
        if not any(c.islower() for c in password):
            issues.append("Password must contain at least one lowercase letter")
        
        if not any(c.isdigit() for c in password):
            issues.append("Password must contain at least one digit")
        
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            issues.append("Password must contain at least one special character")
        
        # Check for common patterns
        if password.lower() in ['password', '123456', 'admin', 'user', 'test']:
            issues.append("Password is too common")
        
        return len(issues) == 0, issues
    
    def generate_secure_password(self, length: int = 16) -> str:
        """
        Generate a cryptographically secure random password.
        
        Args:
            length: Length of password to generate
            
        Returns:
            Secure random password
        """
        import string
        
        # Define character sets
        lowercase = string.ascii_lowercase
        uppercase = string.ascii_uppercase
        digits = string.digits
        special = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        
        # Ensure at least one character from each set
        password = [
            secrets.choice(lowercase),
            secrets.choice(uppercase),
            secrets.choice(digits),
            secrets.choice(special)
        ]
        
        # Fill remaining length with random characters from all sets
        all_chars = lowercase + uppercase + digits + special
        for _ in range(length - 4):
            password.append(secrets.choice(all_chars))
        
        # Shuffle the password list
        secrets.SystemRandom().shuffle(password)
        
        return ''.join(password)
    
    def hash_password_legacy(self, password: str) -> str:
        """
        Legacy SHA-256 password hashing for backward compatibility.
        
        Args:
            password: Plain text password
            
        Returns:
            SHA-256 hash of password (hex encoded)
        """
        return hashlib.sha256(password.encode()).hexdigest()


class RateLimiter:
    """Rate limiting for login attempts to prevent brute force attacks."""
    
    def __init__(self, max_attempts: int = 5, window_seconds: int = 300):
        """
        Initialize rate limiter.
        
        Args:
            max_attempts: Maximum attempts allowed in time window
            window_seconds: Time window in seconds
        """
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self._attempts = {}  # ip_address -> [(timestamp, success), ...]
        self._logger = logging.getLogger(__name__)
    
    def is_rate_limited(self, identifier: str) -> bool:
        """
        Check if identifier is rate limited.
        
        Args:
            identifier: IP address or user identifier
            
        Returns:
            True if rate limited, False otherwise
        """
        now = time.time()
        cutoff = now - self.window_seconds
        
        # Clean old attempts
        if identifier in self._attempts:
            self._attempts[identifier] = [
                (timestamp, success) for timestamp, success in self._attempts[identifier]
                if timestamp > cutoff
            ]
        
        # Count failed attempts in window
        failed_attempts = sum(
            1 for timestamp, success in self._attempts.get(identifier, [])
            if not success
        )
        
        return failed_attempts >= self.max_attempts
    
    def record_attempt(self, identifier: str, success: bool) -> None:
        """
        Record a login attempt.
        
        Args:
            identifier: IP address or user identifier
            success: Whether the attempt was successful
        """
        now = time.time()
        
        if identifier not in self._attempts:
            self._attempts[identifier] = []
        
        self._attempts[identifier].append((now, success))
    
    def clear_attempts(self, identifier: str) -> None:
        """Clear all attempts for an identifier."""
        if identifier in self._attempts:
            del self._attempts[identifier]


# Global password security instance
password_security = PasswordSecurity()
rate_limiter = RateLimiter()