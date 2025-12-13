"""
Authentication and Security Layer
Implements SSH, OTP email authentication, and secure communication
"""

import os
import hashlib
import hmac
import secrets
import smtplib
import time
import logging
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import pyotp
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend

logger = logging.getLogger(__name__)


class OTPManager:
    """
    One-Time Password (OTP) Manager for email authentication
    Implements time-based OTP (TOTP) for secure access
    """
    
    def __init__(self, email: str):
        """
        Initialize OTP manager
        
        Args:
            email: User email address
        """
        self.email = email
        self.secret_key = pyotp.random_base32()
        self.totp = pyotp.TOTP(self.secret_key)
        self.backup_codes: List[str] = self._generate_backup_codes()
        self.last_used_codes: Dict[str, float] = {}  # code -> timestamp
        
        logger.info(f"[OTP] Manager initialized for {email}")
    
    def _generate_backup_codes(self, count: int = 10) -> List[str]:
        """Generate backup codes for account recovery"""
        codes = []
        for _ in range(count):
            code = secrets.token_hex(4).upper()
            codes.append(code)
        return codes
    
    def get_current_code(self) -> str:
        """Get current valid OTP code"""
        return self.totp.now()
    
    def verify_code(self, code: str, time_window: int = 1) -> Tuple[bool, str]:
        """
        Verify OTP code
        
        Args:
            code: Code to verify
            time_window: Number of time windows to check (for clock drift tolerance)
            
        Returns:
            Tuple of (is_valid, message)
        """
        # Check if code was already used (prevent replay attacks)
        if code in self.last_used_codes:
            if time.time() - self.last_used_codes[code] < 30:  # 30 second window
                return False, "Code already used"
        
        # Verify code
        is_valid = self.totp.verify(code, valid_window=time_window)
        
        if is_valid:
            self.last_used_codes[code] = time.time()
            return True, "Code verified successfully"
        else:
            return False, "Invalid code"
    
    def verify_backup_code(self, code: str) -> Tuple[bool, str]:
        """Verify backup code"""
        if code in self.backup_codes:
            self.backup_codes.remove(code)  # Use once
            return True, "Backup code verified"
        else:
            return False, "Invalid backup code"
    
    def get_provisioning_uri(self) -> str:
        """Get provisioning URI for QR code generation"""
        return self.totp.provisioning_uri(self.email, issuer_name="P2P_Storage")


class EmailNotifier:
    """
    Email notification system for OTP and alerts
    """
    
    def __init__(self, smtp_server: str = "smtp.gmail.com", 
                 smtp_port: int = 587,
                 sender_email: str = None,
                 sender_password: str = None):
        """
        Initialize email notifier
        
        Args:
            smtp_server: SMTP server address
            smtp_port: SMTP port
            sender_email: Sender email address
            sender_password: Sender email password
        """
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.sender_email = sender_email or os.getenv('SENDER_EMAIL')
        self.sender_password = sender_password or os.getenv('SENDER_PASSWORD')
    
    def send_otp_email(self, recipient_email: str, otp_code: str) -> bool:
        """Send OTP code via email"""
        try:
            subject = "P2P Storage - Your One-Time Password"
            
            body = f"""
            <html>
                <body>
                    <h2>P2P Storage Authentication</h2>
                    <p>Your One-Time Password (OTP) is:</p>
                    <h1 style="color: #2196F3;">{otp_code}</h1>
                    <p>This code will expire in 30 seconds.</p>
                    <p>Do not share this code with anyone.</p>
                    <hr>
                    <p><small>If you did not request this, please ignore this email.</small></p>
                </body>
            </html>
            """
            
            self._send_email(recipient_email, subject, body, is_html=True)
            logger.info(f"[Email] OTP sent to {recipient_email}")
            return True
        
        except Exception as e:
            logger.error(f"[Email] Error sending OTP: {e}")
            return False
    
    def send_login_alert(self, recipient_email: str, login_info: Dict) -> bool:
        """Send login alert email"""
        try:
            subject = "P2P Storage - Login Alert"
            
            body = f"""
            <html>
                <body>
                    <h2>Login Detected</h2>
                    <p>A login to your P2P Storage account was detected:</p>
                    <ul>
                        <li><strong>Time:</strong> {login_info.get('timestamp')}</li>
                        <li><strong>Node:</strong> {login_info.get('node_id')}</li>
                        <li><strong>IP Address:</strong> {login_info.get('ip_address')}</li>
                    </ul>
                    <p>If this wasn't you, please change your password immediately.</p>
                </body>
            </html>
            """
            
            self._send_email(recipient_email, subject, body, is_html=True)
            logger.info(f"[Email] Login alert sent to {recipient_email}")
            return True
        
        except Exception as e:
            logger.error(f"[Email] Error sending login alert: {e}")
            return False
    
    def _send_email(self, recipient_email: str, subject: str, 
                    body: str, is_html: bool = False) -> bool:
        """
        Send email message
        
        Args:
            recipient_email: Recipient email address
            subject: Email subject
            body: Email body
            is_html: Whether body is HTML
            
        Returns:
            True if successful
        """
        if not self.sender_email or not self.sender_password:
            logger.warning("[Email] Email credentials not configured")
            return False
        
        try:
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = self.sender_email
            message["To"] = recipient_email
            
            if is_html:
                part = MIMEText(body, "html")
            else:
                part = MIMEText(body, "plain")
            
            message.attach(part)
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(message)
            
            return True
        
        except Exception as e:
            logger.error(f"[Email] SMTP error: {e}")
            return False


class PasswordManager:
    """
    Secure password management with hashing and salting
    """
    
    @staticmethod
    def hash_password(password: str, salt: Optional[bytes] = None) -> Tuple[str, str]:
        """
        Hash password with salt using PBKDF2
        
        Args:
            password: Password to hash
            salt: Optional salt (generated if not provided)
            
        Returns:
            Tuple of (hashed_password_hex, salt_hex)
        """
        if salt is None:
            salt = os.urandom(32)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        
        key = kdf.derive(password.encode())
        return key.hex(), salt.hex()
    
    @staticmethod
    def verify_password(password: str, hashed_password: str, salt_hex: str) -> bool:
        """
        Verify password against hash
        
        Args:
            password: Password to verify
            hashed_password: Stored hash
            salt_hex: Salt as hex string
            
        Returns:
            True if password matches
        """
        salt = bytes.fromhex(salt_hex)
        computed_hash, _ = PasswordManager.hash_password(password, salt)
        return hmac.compare_digest(computed_hash, hashed_password)


class User:
    """Represents a user in the P2P storage system"""
    
    def __init__(self, username: str, email: str, password: str):
        """
        Initialize user
        
        Args:
            username: Username
            email: Email address
            password: Plain password (will be hashed)
        """
        self.username = username
        self.email = email
        self.created_at = datetime.now()
        self.last_login: Optional[datetime] = None
        
        # Hash password
        self.password_hash, self.password_salt = PasswordManager.hash_password(password)
        
        # OTP setup
        self.otp_enabled = False
        self.otp_manager: Optional[OTPManager] = None
        
        # Session tokens
        self.session_tokens: Dict[str, Tuple[float, str]] = {}  # token -> (timestamp, ip_address)
        
        logger.info(f"[User] User created: {username}")
    
    def enable_otp(self):
        """Enable OTP authentication for user"""
        self.otp_manager = OTPManager(self.email)
        self.otp_enabled = True
        logger.info(f"[User] OTP enabled for {self.username}")
    
    def verify_password(self, password: str) -> bool:
        """Verify user password"""
        return PasswordManager.verify_password(password, self.password_hash, self.password_salt)
    
    def create_session(self, ip_address: str) -> str:
        """Create a new session token"""
        token = secrets.token_urlsafe(32)
        self.session_tokens[token] = (time.time(), ip_address)
        logger.info(f"[User] Session token created for {self.username}")
        return token
    
    def validate_session(self, token: str, ip_address: str = None) -> bool:
        """Validate a session token"""
        if token not in self.session_tokens:
            return False
        
        timestamp, orig_ip = self.session_tokens[token]
        
        # Check if token expired (24 hour expiry)
        if time.time() - timestamp > 24 * 3600:
            del self.session_tokens[token]
            return False
        
        # Check IP if provided
        if ip_address and ip_address != orig_ip:
            logger.warning(f"[User] Session IP mismatch for {self.username}")
            return False
        
        return True
    
    def get_user_info(self) -> Dict:
        """Get user information"""
        return {
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.isoformat(),
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'otp_enabled': self.otp_enabled,
            'active_sessions': len(self.session_tokens)
        }


class AuthenticationManager:
    """
    Central authentication manager for the P2P system
    """
    
    def __init__(self):
        """Initialize authentication manager"""
        self.users: Dict[str, User] = {}
        self.email_notifier = EmailNotifier()
        
        logger.info("[Auth] Authentication manager initialized")
    
    def register_user(self, username: str, email: str, password: str) -> Tuple[bool, str]:
        """
        Register a new user
        
        Args:
            username: Username
            email: Email address
            password: Password
            
        Returns:
            Tuple of (success, message)
        """
        if username in self.users:
            return False, "Username already exists"
        
        if any(u.email == email for u in self.users.values()):
            return False, "Email already registered"
        
        user = User(username, email, password)
        self.users[username] = user
        
        logger.info(f"[Auth] User registered: {username}")
        return True, "User registered successfully"
    
    def login(self, username: str, password: str, node_ip: str = None) -> Tuple[bool, Optional[str], str]:
        """
        Authenticate user and create session
        
        Args:
            username: Username
            password: Password
            node_ip: IP address of node logging in
            
        Returns:
            Tuple of (success, session_token, message)
        """
        if username not in self.users:
            return False, None, "Invalid username"
        
        user = self.users[username]
        
        if not user.verify_password(password):
            return False, None, "Invalid password"
        
        # If OTP enabled, require OTP verification
        if user.otp_enabled:
            return False, None, "OTP verification required"
        
        # Create session
        token = user.create_session(node_ip or "unknown")
        user.last_login = datetime.now()
        
        # Send login alert
        self.email_notifier.send_login_alert(user.email, {
            'timestamp': datetime.now().isoformat(),
            'node_id': username,
            'ip_address': node_ip or "unknown"
        })
        
        logger.info(f"[Auth] User logged in: {username}")
        return True, token, "Login successful"
    
    def verify_otp_and_login(self, username: str, password: str, 
                             otp_code: str, node_ip: str = None) -> Tuple[bool, Optional[str], str]:
        """
        Login with OTP verification
        
        Args:
            username: Username
            password: Password
            otp_code: OTP code
            node_ip: IP address of node logging in
            
        Returns:
            Tuple of (success, session_token, message)
        """
        if username not in self.users:
            return False, None, "Invalid username"
        
        user = self.users[username]
        
        if not user.verify_password(password):
            return False, None, "Invalid password"
        
        if not user.otp_enabled or not user.otp_manager:
            return False, None, "OTP not enabled"
        
        # Verify OTP
        is_valid, msg = user.otp_manager.verify_code(otp_code)
        if not is_valid:
            return False, None, msg
        
        # Create session
        token = user.create_session(node_ip or "unknown")
        user.last_login = datetime.now()
        
        logger.info(f"[Auth] User logged in with OTP: {username}")
        return True, token, "Login successful"
