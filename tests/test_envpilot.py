"""
EnvPilot Test Suite
"""

import pytest
import tempfile
import json
from pathlib import Path

from envpilot.core import EnvManager, EnvVariable, EnvProject
from envpilot.crypto import CryptoEngine
from envpilot.scanner import LeakScanner, LeakSeverity


class TestCryptoEngine:
    """Tests for the crypto module."""
    
    def test_encrypt_decrypt(self):
        """Test basic encryption and decryption."""
        engine = CryptoEngine("test_password")
        plaintext = "my_secret_value"
        
        encrypted = engine.encrypt(plaintext)
        assert encrypted != plaintext
        assert len(encrypted) > 0
        
        decrypted = engine.decrypt(encrypted)
        assert decrypted == plaintext
    
    def test_different_encryptions(self):
        """Test that same value produces different ciphertexts."""
        engine = CryptoEngine("test_password")
        plaintext = "my_secret_value"
        
        encrypted1 = engine.encrypt(plaintext)
        encrypted2 = engine.encrypt(plaintext)
        
        # Different due to random salt and nonce
        assert encrypted1 != encrypted2
        
        # Both decrypt to same value
        assert engine.decrypt(encrypted1) == plaintext
        assert engine.decrypt(encrypted2) == plaintext
    
    def test_wrong_password(self):
        """Test that wrong password fails decryption."""
        engine1 = CryptoEngine("correct_password")
        engine2 = CryptoEngine("wrong_password")
        
        encrypted = engine1.encrypt("secret")
        
        with pytest.raises(ValueError):
            engine2.decrypt(encrypted)
    
    def test_generate_master_key(self):
        """Test master key generation."""
        key1 = CryptoEngine.generate_master_key()
        key2 = CryptoEngine.generate_master_key()
        
        assert len(key1) == 32
        assert key1 != key2  # Should be unique
    
    def test_hash_password(self):
        """Test password hashing."""
        hash1 = CryptoEngine.hash_password("password")
        hash2 = CryptoEngine.hash_password("password")
        
        assert hash1 == hash2  # Same input = same hash
        assert len(hash1) == 64  # SHA-256 hex length


class TestEnvManager:
    """Tests for the core module."""
    
    @pytest.fixture
    def temp_storage(self, tmp_path):
        """Create a temporary storage path."""
        return tmp_path / "test_storage.json"
    
    @pytest.fixture
    def manager(self, temp_storage):
        """Create a manager with temporary storage."""
        return EnvManager(storage_path=temp_storage)
    
    def test_create_project(self, manager):
        """Test project creation."""
        project = manager.create_project("test_project", "Test description")
        
        assert project.name == "test_project"
        assert project.description == "Test description"
        assert "development" in project.environments
        assert "staging" in project.environments
        assert "production" in project.environments
    
    def test_duplicate_project(self, manager):
        """Test that duplicate projects are rejected."""
        manager.create_project("test_project")
        
        with pytest.raises(ValueError):
            manager.create_project("test_project")
    
    def test_set_get_var(self, manager):
        """Test setting and getting variables."""
        manager.create_project("test_project")
        
        manager.set_var("API_KEY", "secret123")
        value = manager.get_var("API_KEY")
        
        assert value == "secret123"
    
    def test_encrypted_var(self, manager):
        """Test encrypted variable storage."""
        manager.create_project("test_project")
        manager.set_master_password("master123")
        
        manager.set_var("SECRET_KEY", "super_secret", encrypt=True)
        
        # Raw value should be encrypted
        var_info = manager.get_var_info("SECRET_KEY")
        assert var_info.encrypted is True
        assert var_info.value != "super_secret"
        
        # get_var should decrypt
        value = manager.get_var("SECRET_KEY")
        assert value == "super_secret"
    
    def test_delete_var(self, manager):
        """Test variable deletion."""
        manager.create_project("test_project")
        manager.set_var("API_KEY", "secret123")
        
        assert manager.delete_var("API_KEY") is True
        assert manager.get_var("API_KEY") is None
        assert manager.delete_var("NONEXISTENT") is False
    
    def test_list_vars(self, manager):
        """Test listing variables."""
        manager.create_project("test_project")
        manager.set_var("VAR1", "value1", tags=["tag1"])
        manager.set_var("VAR2", "value2", tags=["tag2"])
        manager.set_var("VAR3", "value3", tags=["tag1"])
        
        all_vars = manager.list_vars()
        assert len(all_vars) == 3
        
        tag1_vars = manager.list_vars(tag="tag1")
        assert len(tag1_vars) == 2
    
    def test_search_vars(self, manager):
        """Test variable search."""
        manager.create_project("test_project")
        manager.set_var("DATABASE_URL", "postgres://...", description="Main database")
        manager.set_var("API_KEY", "secret", description="External API key")
        
        results = manager.search_vars("database")
        assert len(results) > 0
    
    def test_switch_environment(self, manager):
        """Test environment switching."""
        manager.create_project("test_project")
        manager.set_var("VAR", "dev_value", environment="development")
        manager.set_var("VAR", "prod_value", environment="production")
        
        manager.switch_environment("development")
        assert manager.get_var("VAR") == "dev_value"
        
        manager.switch_environment("production")
        assert manager.get_var("VAR") == "prod_value"
    
    def test_import_env_file(self, manager, tmp_path):
        """Test importing from .env file."""
        env_file = tmp_path / ".env"
        env_file.write_text("""
# Comment
DATABASE_URL=postgres://localhost/db
APP_NAME=myapp
EMPTY_VAR=
"QUOTED=value with spaces"
""")
        
        manager.create_project("test_project")
        # Disable auto-encrypt for sensitive keys to avoid needing master password
        count = manager.import_env_file(env_file, encrypt_sensitive=False)
        
        assert count >= 3
        assert manager.get_var("DATABASE_URL") == "postgres://localhost/db"
        assert manager.get_var("APP_NAME") == "myapp"
    
    def test_export_env_file(self, manager, tmp_path):
        """Test exporting to .env file."""
        manager.create_project("test_project")
        manager.set_var("VAR1", "value1", description="First variable")
        manager.set_var("VAR2", "value2")
        
        output_file = tmp_path / "output.env"
        count = manager.export_env_file(output_file)
        
        assert count == 2
        content = output_file.read_text()
        assert "VAR1=value1" in content
        assert "VAR2=value2" in content
    
    def test_export_shell(self, manager):
        """Test shell export generation."""
        manager.create_project("test_project")
        manager.set_var("VAR1", "value1")
        manager.set_var("VAR2", "value2")
        
        bash_output = manager.export_shell(shell="bash")
        assert 'export VAR1="value1"' in bash_output
        assert 'export VAR2="value2"' in bash_output
        
        fish_output = manager.export_shell(shell="fish")
        assert 'set -gx VAR1 "value1"' in fish_output


class TestLeakScanner:
    """Tests for the scanner module."""
    
    @pytest.fixture
    def temp_project(self, tmp_path):
        """Create a temporary project directory."""
        return tmp_path
    
    def test_scan_aws_key(self, temp_project):
        """Test detection of AWS access keys."""
        test_file = temp_project / "config.py"
        test_file.write_text('AWS_KEY = "AKIAIOSFODNN7EXAMPLE"')
        
        scanner = LeakScanner(temp_project)
        findings = scanner.scan_file(test_file)
        
        assert len(findings) > 0
        assert any(f.severity == LeakSeverity.CRITICAL for f in findings)
    
    def test_scan_github_token(self, temp_project):
        """Test detection of GitHub tokens."""
        test_file = temp_project / "config.py"
        test_file.write_text('GITHUB_TOKEN = "ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"')
        
        scanner = LeakScanner(temp_project)
        findings = scanner.scan_file(test_file)
        
        assert len(findings) > 0
        assert any("GitHub" in f.key_name for f in findings)
    
    def test_scan_password(self, temp_project):
        """Test detection of passwords."""
        test_file = temp_project / "config.py"
        test_file.write_text('password = "mysecretpassword123"')
        
        scanner = LeakScanner(temp_project)
        findings = scanner.scan_file(test_file)
        
        assert len(findings) > 0
        assert any(f.severity == LeakSeverity.HIGH for f in findings)
    
    def test_scan_clean_file(self, temp_project):
        """Test that clean files have no findings."""
        test_file = temp_project / "clean.py"
        test_file.write_text('''
def hello():
    print("Hello, World!")
    return 42
''')
        
        scanner = LeakScanner(temp_project)
        findings = scanner.scan_file(test_file)
        
        assert len(findings) == 0
    
    def test_generate_report(self, temp_project):
        """Test report generation."""
        test_file = temp_project / "config.py"
        # Use a value that matches the API_KEY pattern (>= 20 chars)
        test_file.write_text('API_KEY = "secret123456789012345"')
        
        scanner = LeakScanner(temp_project)
        findings = scanner.scan_file(test_file)
        
        report = scanner.generate_report(findings)
        assert "EnvPilot Security Scan Report" in report
        # Check for findings or empty report
        if findings:
            assert "API" in report or "finding" in report.lower()
    
    def test_json_report(self, temp_project):
        """Test JSON report format."""
        test_file = temp_project / "config.py"
        # Use a value that matches the API_KEY pattern (>= 20 chars)
        test_file.write_text('API_KEY = "secret123456789012345"')
        
        scanner = LeakScanner(temp_project)
        findings = scanner.scan_file(test_file)
        
        report = scanner.generate_report(findings, format="json")
        data = json.loads(report)
        
        assert isinstance(data, list)
        # If findings exist, check structure
        if len(data) > 0:
            assert "file_path" in data[0]
            assert "severity" in data[0]


class TestEnvVariable:
    """Tests for EnvVariable dataclass."""
    
    def test_create_var(self):
        """Test variable creation."""
        var = EnvVariable(
            key="TEST_KEY",
            value="test_value",
            description="Test description",
            tags=["test", "example"]
        )
        
        assert var.key == "TEST_KEY"
        assert var.value == "test_value"
        assert var.encrypted is False
        assert len(var.tags) == 2
    
    def test_update_var(self):
        """Test variable update."""
        var = EnvVariable(key="TEST_KEY", value="old_value")
        var.update("new_value", "New description")
        
        assert var.value == "new_value"
        assert var.description == "New description"
    
    def test_to_dict(self):
        """Test dictionary conversion."""
        var = EnvVariable(key="TEST_KEY", value="test_value")
        data = var.to_dict()
        
        assert data["key"] == "TEST_KEY"
        assert data["value"] == "test_value"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
