import os
from cryptography.fernet import Fernet
from typing import Optional


class FieldEncryption:
    """Encrypt/decrypt PII fields (email, mobile) using Fernet symmetric encryption."""
    
    def __init__(self, key: Optional[bytes] = None):
        if key is None:
            # In production, load from secure key management
            key = os.environ.get("FIELD_ENCRYPTION_KEY", "").encode()
            if not key:
                # Generate a key for development (NOT for production!)
                key = Fernet.generate_key()
        self.cipher = Fernet(key)
    
    def encrypt(self, plaintext: str) -> str:
        """Encrypt a plaintext string. Returns base64 encoded ciphertext."""
        if not plaintext:
            return ""
        return self.cipher.encrypt(plaintext.encode()).decode()
    
    def decrypt(self, ciphertext: str) -> str:
        """Decrypt a base64 encoded ciphertext string. Returns plaintext."""
        if not ciphertext:
            return ""
        try:
            return self.cipher.decrypt(ciphertext.encode()).decode()
        except Exception:
            return ""


def mask_email(email: str) -> str:
    """Mask email for display: v***@example.com"""
    if not email or "@" not in email:
        return ""
    local, domain = email.split("@", 1)
    if len(local) <= 2:
        masked_local = local[0] + "**"
    else:
        masked_local = local[0] + "***" + local[-1]
    return f"{masked_local}@{domain}"


def mask_mobile(mobile: str) -> str:
    """Mask mobile for display: 9876****10"""
    if not mobile:
        return ""
    digits = "".join(c for c in mobile if c.isdigit())
    if len(digits) <= 4:
        return "*" * len(digits)
    return digits[:4] + "****" + digits[-2:]


def mask_apaar(apaar_id: str) -> str:
    """Mask APAAR ID for display: 1234****9012"""
    if not apaar_id or len(apaar_id) != 12:
        return apaar_id
    return apaar_id[:4] + "****" + apaar_id[-4:]


# Global instance
_field_encryption: Optional[FieldEncryption] = None


def get_field_encryption() -> FieldEncryption:
    global _field_encryption
    if _field_encryption is None:
        _field_encryption = FieldEncryption()
    return _field_encryption