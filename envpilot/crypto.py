"""
EnvPilot Crypto Module - AES-256-GCM Encryption Engine
环境变量加密模块 - AES-256-GCM加密引擎
"""

import os
import base64
import hashlib
from typing import Optional, Tuple
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class CryptoEngine:
    """
    AES-256-GCM encryption engine for secure environment variable storage.
    使用AES-256-GCM加密算法安全存储环境变量。
    
    Features:
    - AES-256-GCM authenticated encryption
    - PBKDF2 key derivation with 100,000 iterations
    - Random salt and nonce for each encryption
    - Base64 encoding for safe storage
    """
    
    KEY_SIZE = 32  # 256 bits
    NONCE_SIZE = 12  # 96 bits (recommended for GCM)
    SALT_SIZE = 16  # 128 bits
    ITERATIONS = 100_000
    
    def __init__(self, master_password: str):
        """
        Initialize the crypto engine with a master password.
        
        Args:
            master_password: The master password for encryption/decryption
        """
        self._master_password = master_password.encode('utf-8')
    
    def _derive_key(self, salt: bytes) -> bytes:
        """
        Derive encryption key from master password using PBKDF2.
        
        Args:
            salt: Random salt for key derivation
            
        Returns:
            32-byte encryption key
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=self.KEY_SIZE,
            salt=salt,
            iterations=self.ITERATIONS,
        )
        return kdf.derive(self._master_password)
    
    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt a string value using AES-256-GCM.
        
        Args:
            plaintext: The string to encrypt
            
        Returns:
            Base64-encoded encrypted data (salt + nonce + ciphertext)
        """
        # Generate random salt and nonce
        salt = os.urandom(self.SALT_SIZE)
        nonce = os.urandom(self.NONCE_SIZE)
        
        # Derive key from password and salt
        key = self._derive_key(salt)
        
        # Encrypt with AES-GCM
        aesgcm = AESGCM(key)
        ciphertext = aesgcm.encrypt(nonce, plaintext.encode('utf-8'), None)
        
        # Combine salt + nonce + ciphertext and encode
        combined = salt + nonce + ciphertext
        return base64.b64encode(combined).decode('ascii')
    
    def decrypt(self, encrypted_data: str) -> str:
        """
        Decrypt a previously encrypted string.
        
        Args:
            encrypted_data: Base64-encoded encrypted data
            
        Returns:
            Original plaintext string
            
        Raises:
            ValueError: If decryption fails (wrong password or corrupted data)
        """
        try:
            # Decode base64
            combined = base64.b64decode(encrypted_data)
            
            # Extract salt, nonce, and ciphertext
            salt = combined[:self.SALT_SIZE]
            nonce = combined[self.SALT_SIZE:self.SALT_SIZE + self.NONCE_SIZE]
            ciphertext = combined[self.SALT_SIZE + self.NONCE_SIZE:]
            
            # Derive key
            key = self._derive_key(salt)
            
            # Decrypt
            aesgcm = AESGCM(key)
            plaintext = aesgcm.decrypt(nonce, ciphertext, None)
            
            return plaintext.decode('utf-8')
        except Exception as e:
            raise ValueError(f"Decryption failed: {str(e)}")
    
    @staticmethod
    def generate_master_key() -> str:
        """
        Generate a random master key suitable for use as a password.
        
        Returns:
            32-character random hex string
        """
        return os.urandom(16).hex()
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        Create a SHA-256 hash of a password for verification.
        
        Args:
            password: Password to hash
            
        Returns:
            Hex-encoded SHA-256 hash
        """
        return hashlib.sha256(password.encode('utf-8')).hexdigest()
    
    def verify_password(self, password_hash: str) -> bool:
        """
        Verify if the provided password matches the stored hash.
        
        Args:
            password_hash: Previously stored password hash
            
        Returns:
            True if password matches
        """
        return self.hash_password(self._master_password.decode('utf-8')) == password_hash
