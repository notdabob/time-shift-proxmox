"""
Secure Token Storage - Enhanced security for GitHub and other tokens
"""

import os
import json
import keyring
from pathlib import Path
from typing import Optional, Dict, Any
from cryptography.fernet import Fernet
import logging

logger = logging.getLogger(__name__)


class SecureTokenStorage:
    """Secure storage for sensitive tokens using system keyring"""
    
    SERVICE_NAME = "time-shift-proxmox"
    
    def __init__(self):
        self.fallback_dir = Path.home() / ".time-shift" / "secure"
        self.fallback_dir.mkdir(parents=True, exist_ok=True)
        
    def store_token(self, name: str, token: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Store a token securely
        
        Args:
            name: Token identifier (e.g., 'github', 'proxmox')
            token: The token value
            metadata: Optional metadata about the token
            
        Returns:
            bool: Success status
        """
        try:
            # Try keyring first
            keyring.set_password(self.SERVICE_NAME, name, token)
            
            # Store metadata separately if provided
            if metadata:
                metadata_key = f"{name}_metadata"
                keyring.set_password(self.SERVICE_NAME, metadata_key, json.dumps(metadata))
            
            logger.info(f"Token '{name}' stored securely in keyring")
            return True
            
        except Exception as e:
            logger.warning(f"Keyring storage failed: {e}, using encrypted file fallback")
            return self._fallback_store(name, token, metadata)
    
    def retrieve_token(self, name: str) -> Optional[str]:
        """
        Retrieve a stored token
        
        Args:
            name: Token identifier
            
        Returns:
            str: Token value if found
        """
        try:
            # Try keyring first
            token = keyring.get_password(self.SERVICE_NAME, name)
            if token:
                logger.info(f"Token '{name}' retrieved from keyring")
                return token
                
        except Exception as e:
            logger.warning(f"Keyring retrieval failed: {e}, trying fallback")
            
        # Try fallback
        return self._fallback_retrieve(name)
    
    def delete_token(self, name: str) -> bool:
        """
        Delete a stored token
        
        Args:
            name: Token identifier
            
        Returns:
            bool: Success status
        """
        success = False
        
        try:
            # Delete from keyring
            keyring.delete_password(self.SERVICE_NAME, name)
            # Delete metadata if exists
            try:
                keyring.delete_password(self.SERVICE_NAME, f"{name}_metadata")
            except:
                pass
            success = True
            logger.info(f"Token '{name}' deleted from keyring")
        except Exception as e:
            logger.warning(f"Keyring deletion failed: {e}")
            
        # Also try to delete from fallback
        fallback_file = self.fallback_dir / f"{name}.enc"
        if fallback_file.exists():
            fallback_file.unlink()
            success = True
            
        return success
    
    def list_tokens(self) -> list[str]:
        """List all stored token names"""
        tokens = set()
        
        # Get from keyring
        try:
            import keyring.backends
            # This is platform-specific, but we'll try to list
            # For now, we'll check known token names
            for name in ['github', 'proxmox', 'gitlab', 'bitbucket']:
                if keyring.get_password(self.SERVICE_NAME, name):
                    tokens.add(name)
        except:
            pass
            
        # Get from fallback
        for enc_file in self.fallback_dir.glob("*.enc"):
            tokens.add(enc_file.stem)
            
        return sorted(list(tokens))
    
    def _fallback_store(self, name: str, token: str, metadata: Optional[Dict[str, Any]]) -> bool:
        """Encrypted file fallback storage"""
        try:
            # Generate a key for this token
            key = Fernet.generate_key()
            fernet = Fernet(key)
            
            # Prepare data
            data = {
                "token": token,
                "metadata": metadata or {}
            }
            
            # Encrypt
            encrypted_data = fernet.encrypt(json.dumps(data).encode())
            
            # Store encrypted data and key separately
            token_file = self.fallback_dir / f"{name}.enc"
            key_file = self.fallback_dir / f"{name}.key"
            
            token_file.write_bytes(encrypted_data)
            key_file.write_bytes(key)
            
            # Set restrictive permissions
            token_file.chmod(0o600)
            key_file.chmod(0o600)
            
            logger.info(f"Token '{name}' stored in encrypted fallback")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store token in fallback: {e}")
            return False
    
    def _fallback_retrieve(self, name: str) -> Optional[str]:
        """Retrieve from encrypted file fallback"""
        try:
            token_file = self.fallback_dir / f"{name}.enc"
            key_file = self.fallback_dir / f"{name}.key"
            
            if not token_file.exists() or not key_file.exists():
                return None
                
            # Read key and encrypted data
            key = key_file.read_bytes()
            encrypted_data = token_file.read_bytes()
            
            # Decrypt
            fernet = Fernet(key)
            decrypted_data = fernet.decrypt(encrypted_data)
            data = json.loads(decrypted_data.decode())
            
            logger.info(f"Token '{name}' retrieved from encrypted fallback")
            return data["token"]
            
        except Exception as e:
            logger.error(f"Failed to retrieve token from fallback: {e}")
            return None


# Convenience functions for GitHub token management
def store_github_token(token: str) -> bool:
    """Store GitHub token securely"""
    storage = SecureTokenStorage()
    return storage.store_token("github", token, {"type": "personal_access_token"})


def get_github_token() -> Optional[str]:
    """Retrieve GitHub token"""
    storage = SecureTokenStorage()
    
    # Try secure storage first
    token = storage.retrieve_token("github")
    if token:
        return token
        
    # Check legacy locations
    legacy_locations = [
        Path.home() / ".time-shift-proxmox-token",
        Path.home() / ".pat",
        Path(".pat"),
    ]
    
    for location in legacy_locations:
        if location.exists():
            try:
                token = location.read_text().strip()
                if token:
                    logger.info(f"Found token in legacy location: {location}")
                    # Migrate to secure storage
                    if storage.store_token("github", token):
                        logger.info("Migrated token to secure storage")
                        # Optionally delete the legacy file
                        # location.unlink()
                    return token
            except Exception as e:
                logger.warning(f"Failed to read legacy token from {location}: {e}")
                
    return None


def migrate_legacy_tokens():
    """Migrate tokens from legacy storage to secure storage"""
    storage = SecureTokenStorage()
    migrations = 0
    
    # Legacy file patterns
    legacy_patterns = [
        ("~/.time-shift-proxmox-token", "github"),
        ("~/.pat", "github"),
        ("./pat", "github"),
        ("~/.git-credentials", "git-credentials"),
    ]
    
    for pattern, token_name in legacy_patterns:
        path = Path(pattern).expanduser()
        if path.exists():
            try:
                content = path.read_text().strip()
                if content and storage.store_token(token_name, content):
                    logger.info(f"Migrated {token_name} from {path}")
                    migrations += 1
                    # Create backup before deletion
                    backup_path = path.with_suffix(path.suffix + ".backup")
                    path.rename(backup_path)
                    logger.info(f"Created backup at {backup_path}")
            except Exception as e:
                logger.error(f"Failed to migrate from {path}: {e}")
                
    return migrations


if __name__ == "__main__":
    # Example usage
    storage = SecureTokenStorage()
    
    # Test storage
    test_token = "ghp_test123456789"
    if storage.store_token("test", test_token):
        print("Token stored successfully")
        
    # Test retrieval
    retrieved = storage.retrieve_token("test")
    if retrieved == test_token:
        print("Token retrieved successfully")
        
    # List tokens
    print(f"Stored tokens: {storage.list_tokens()}")
    
    # Clean up test
    storage.delete_token("test")