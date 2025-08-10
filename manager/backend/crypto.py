import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from .config import manager_config

class CryptoManager:
    """Encryption manager for API key encryption and decryption"""
    
    def __init__(self):
        self._key = None
    
    def _get_key(self) -> bytes:
        """Get encryption key"""
        if self._key is None:
            # Get key from environment variable, generate if not available
            secret = manager_config.CRYPTO_SECRET
            salt = manager_config.CRYPTO_SALT.encode()
            
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(secret.encode()))
            self._key = key
        
        return self._key
    
    def encrypt(self, plaintext: str) -> str:
        """Encrypt string"""
        if not plaintext:
            return ""
        
        f = Fernet(self._get_key())
        encrypted = f.encrypt(plaintext.encode())
        return base64.urlsafe_b64encode(encrypted).decode()
    
    def decrypt(self, ciphertext: str) -> str:
        """Decrypt string"""
        if not ciphertext:
            return ""
        
        try:
            f = Fernet(self._get_key())
            encrypted_data = base64.urlsafe_b64decode(ciphertext.encode())
            decrypted = f.decrypt(encrypted_data)
            return decrypted.decode()
        except Exception:
            # If decryption fails, it might be old data stored in plaintext, return as-is
            return ciphertext


# Global crypto manager instance
crypto_manager = CryptoManager()
