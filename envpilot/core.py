"""
EnvPilot Core Module - Environment Variables Management Engine
环境变量管理核心模块
"""

import os
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field, asdict
from enum import Enum

from envpilot.crypto import CryptoEngine


class EnvEnvironment(Enum):
    """Environment types for variable management."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"
    LOCAL = "local"
    CUSTOM = "custom"


@dataclass
class EnvVariable:
    """
    Represents a single environment variable with metadata.
    环境变量数据结构，包含元数据信息。
    """
    key: str
    value: str
    encrypted: bool = False
    description: str = ""
    tags: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EnvVariable':
        """Create from dictionary."""
        return cls(**data)
    
    def update(self, value: str, description: Optional[str] = None) -> None:
        """Update the variable value and timestamp."""
        self.value = value
        self.updated_at = datetime.now().isoformat()
        if description is not None:
            self.description = description


@dataclass
class EnvProject:
    """
    Represents a project with multiple environments.
    项目配置，支持多环境管理。
    """
    name: str
    description: str = ""
    environments: Dict[str, Dict[str, EnvVariable]] = field(default_factory=dict)
    current_environment: str = "development"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "description": self.description,
            "environments": {
                env: {k: v.to_dict() for k, v in vars.items()}
                for env, vars in self.environments.items()
            },
            "current_environment": self.current_environment,
            "created_at": self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EnvProject':
        """Create from dictionary."""
        environments = {}
        for env, vars in data.get("environments", {}).items():
            environments[env] = {
                k: EnvVariable.from_dict(v) for k, v in vars.items()
            }
        return cls(
            name=data["name"],
            description=data.get("description", ""),
            environments=environments,
            current_environment=data.get("current_environment", "development"),
            created_at=data.get("created_at", datetime.now().isoformat())
        )


class EnvManager:
    """
    Main environment variables management engine.
    环境变量智能管理引擎。
    
    Features:
    - Multi-project support
    - Multi-environment management
    - AES-256-GCM encryption for sensitive values
    - Import/Export (.env, JSON, YAML)
    - Variable validation and leak detection
    - Search and filter capabilities
    """
    
    DEFAULT_STORAGE_PATH = Path.home() / ".envpilot" / "storage.json"
    
    def __init__(
        self,
        storage_path: Optional[Path] = None,
        master_password: Optional[str] = None
    ):
        """
        Initialize the environment manager.
        
        Args:
            storage_path: Path to storage file (default: ~/.envpilot/storage.json)
            master_password: Master password for encryption (required for encrypted vars)
        """
        self.storage_path = Path(storage_path) if storage_path else self.DEFAULT_STORAGE_PATH
        self._master_password = master_password
        self._crypto: Optional[CryptoEngine] = None
        self._projects: Dict[str, EnvProject] = {}
        self._current_project: Optional[str] = None
        self._password_hash: Optional[str] = None
        
        self._load_storage()
    
    @property
    def crypto(self) -> CryptoEngine:
        """Get crypto engine (lazy initialization)."""
        if self._crypto is None:
            if self._master_password is None:
                raise ValueError("Master password required for encryption operations")
            self._crypto = CryptoEngine(self._master_password)
        return self._crypto
    
    def _load_storage(self) -> None:
        """Load storage from disk."""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self._password_hash = data.get("password_hash")
                self._current_project = data.get("current_project")
                
                for name, proj_data in data.get("projects", {}).items():
                    self._projects[name] = EnvProject.from_dict(proj_data)
            except (json.JSONDecodeError, KeyError):
                # Corrupted storage, start fresh
                self._projects = {}
    
    def _save_storage(self) -> None:
        """Save storage to disk."""
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            "version": "1.0.0",
            "password_hash": self._password_hash,
            "current_project": self._current_project,
            "projects": {name: proj.to_dict() for name, proj in self._projects.items()}
        }
        
        with open(self.storage_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def set_master_password(self, password: str) -> None:
        """
        Set or update the master password.
        
        Args:
            password: New master password
        """
        self._master_password = password
        self._crypto = CryptoEngine(password)
        self._password_hash = CryptoEngine.hash_password(password)
        self._save_storage()
    
    def verify_master_password(self, password: str) -> bool:
        """Verify if the provided password matches the stored hash."""
        if self._password_hash is None:
            return True  # No password set yet
        return CryptoEngine.hash_password(password) == self._password_hash
    
    # ==================== Project Management ====================
    
    def create_project(
        self,
        name: str,
        description: str = "",
        environments: Optional[List[str]] = None
    ) -> EnvProject:
        """
        Create a new project.
        
        Args:
            name: Project name
            description: Project description
            environments: List of environment names to create
            
        Returns:
            Created EnvProject
        """
        if name in self._projects:
            raise ValueError(f"Project '{name}' already exists")
        
        project = EnvProject(name=name, description=description)
        
        # Create default environments
        default_envs = environments or ["development", "staging", "production"]
        for env in default_envs:
            project.environments[env] = {}
        
        self._projects[name] = project
        self._current_project = name
        self._save_storage()
        
        return project
    
    def get_project(self, name: str) -> Optional[EnvProject]:
        """Get a project by name."""
        return self._projects.get(name)
    
    def list_projects(self) -> List[str]:
        """List all project names."""
        return list(self._projects.keys())
    
    def delete_project(self, name: str) -> bool:
        """Delete a project."""
        if name not in self._projects:
            return False
        
        del self._projects[name]
        if self._current_project == name:
            self._current_project = next(iter(self._projects), None)
        self._save_storage()
        return True
    
    def set_current_project(self, name: str) -> None:
        """Set the current active project."""
        if name not in self._projects:
            raise ValueError(f"Project '{name}' not found")
        self._current_project = name
        self._save_storage()
    
    @property
    def current_project(self) -> Optional[EnvProject]:
        """Get the current active project."""
        if self._current_project:
            return self._projects.get(self._current_project)
        return None
    
    # ==================== Environment Management ====================
    
    def add_environment(self, project: str, environment: str) -> None:
        """Add a new environment to a project."""
        if project not in self._projects:
            raise ValueError(f"Project '{project}' not found")
        
        if environment in self._projects[project].environments:
            raise ValueError(f"Environment '{environment}' already exists")
        
        self._projects[project].environments[environment] = {}
        self._save_storage()
    
    def list_environments(self, project: Optional[str] = None) -> List[str]:
        """List all environments in a project."""
        proj = self._projects.get(project) if project else self.current_project
        if proj:
            return list(proj.environments.keys())
        return []
    
    def delete_environment(self, project: str, environment: str) -> bool:
        """Delete an environment from a project."""
        if project not in self._projects:
            return False
        
        proj = self._projects[project]
        if environment not in proj.environments:
            return False
        
        del proj.environments[environment]
        self._save_storage()
        return True
    
    def switch_environment(self, environment: str, project: Optional[str] = None) -> None:
        """Switch to a different environment."""
        proj = self._projects.get(project) if project else self.current_project
        if not proj:
            raise ValueError("No project selected")
        
        if environment not in proj.environments:
            raise ValueError(f"Environment '{environment}' not found")
        
        proj.current_environment = environment
        self._save_storage()
    
    # ==================== Variable Management ====================
    
    def set_var(
        self,
        key: str,
        value: str,
        project: Optional[str] = None,
        environment: Optional[str] = None,
        description: str = "",
        tags: Optional[List[str]] = None,
        encrypt: bool = False
    ) -> EnvVariable:
        """
        Set an environment variable.
        
        Args:
            key: Variable name
            value: Variable value
            project: Project name (uses current if not specified)
            environment: Environment name (uses current if not specified)
            description: Variable description
            tags: Tags for categorization
            encrypt: Whether to encrypt the value
            
        Returns:
            Created or updated EnvVariable
        """
        proj = self._projects.get(project) if project else self.current_project
        if not proj:
            raise ValueError("No project selected")
        
        env = environment or proj.current_environment
        if env not in proj.environments:
            proj.environments[env] = {}
        
        # Encrypt value if requested
        stored_value = value
        if encrypt:
            stored_value = self.crypto.encrypt(value)
        
        var = EnvVariable(
            key=key,
            value=stored_value,
            encrypted=encrypt,
            description=description,
            tags=tags or []
        )
        
        proj.environments[env][key] = var
        self._save_storage()
        
        return var
    
    def get_var(
        self,
        key: str,
        project: Optional[str] = None,
        environment: Optional[str] = None,
        decrypt: bool = True
    ) -> Optional[str]:
        """
        Get an environment variable value.
        
        Args:
            key: Variable name
            project: Project name
            environment: Environment name
            decrypt: Whether to decrypt encrypted values
            
        Returns:
            Variable value or None if not found
        """
        proj = self._projects.get(project) if project else self.current_project
        if not proj:
            return None
        
        env = environment or proj.current_environment
        if env not in proj.environments:
            return None
        
        var = proj.environments[env].get(key)
        if not var:
            return None
        
        if var.encrypted and decrypt:
            return self.crypto.decrypt(var.value)
        
        return var.value
    
    def get_var_info(
        self,
        key: str,
        project: Optional[str] = None,
        environment: Optional[str] = None
    ) -> Optional[EnvVariable]:
        """Get full variable information (including metadata)."""
        proj = self._projects.get(project) if project else self.current_project
        if not proj:
            return None
        
        env = environment or proj.current_environment
        if env not in proj.environments:
            return None
        
        return proj.environments[env].get(key)
    
    def delete_var(
        self,
        key: str,
        project: Optional[str] = None,
        environment: Optional[str] = None
    ) -> bool:
        """Delete an environment variable."""
        proj = self._projects.get(project) if project else self.current_project
        if not proj:
            return False
        
        env = environment or proj.current_environment
        if env not in proj.environments:
            return False
        
        if key not in proj.environments[env]:
            return False
        
        del proj.environments[env][key]
        self._save_storage()
        return True
    
    def list_vars(
        self,
        project: Optional[str] = None,
        environment: Optional[str] = None,
        tag: Optional[str] = None,
        show_encrypted: bool = True
    ) -> Dict[str, EnvVariable]:
        """
        List all variables in an environment.
        
        Args:
            project: Project name
            environment: Environment name
            tag: Filter by tag
            show_encrypted: Include encrypted variables
            
        Returns:
            Dictionary of variables
        """
        proj = self._projects.get(project) if project else self.current_project
        if not proj:
            return {}
        
        env = environment or proj.current_environment
        if env not in proj.environments:
            return {}
        
        result = {}
        for key, var in proj.environments[env].items():
            if not show_encrypted and var.encrypted:
                continue
            if tag and tag not in var.tags:
                continue
            result[key] = var
        
        return result
    
    def search_vars(
        self,
        query: str,
        project: Optional[str] = None
    ) -> Dict[str, Dict[str, EnvVariable]]:
        """
        Search variables across all environments.
        
        Args:
            query: Search query (searches key and description)
            project: Project to search in (all projects if not specified)
            
        Returns:
            Dictionary mapping environment names to matching variables
        """
        query_lower = query.lower()
        results: Dict[str, Dict[str, EnvVariable]] = {}
        
        projects_to_search = (
            {project: self._projects[project]} 
            if project and project in self._projects 
            else self._projects
        )
        
        for proj_name, proj in projects_to_search.items():
            for env_name, vars in proj.environments.items():
                for key, var in vars.items():
                    if (query_lower in key.lower() or 
                        query_lower in var.description.lower()):
                        full_env = f"{proj_name}/{env_name}"
                        if full_env not in results:
                            results[full_env] = {}
                        results[full_env][key] = var
        
        return results
    
    # ==================== Import/Export ====================
    
    def import_env_file(
        self,
        file_path: Path,
        project: Optional[str] = None,
        environment: Optional[str] = None,
        encrypt_sensitive: bool = True
    ) -> int:
        """
        Import variables from a .env file.
        
        Args:
            file_path: Path to .env file
            project: Target project
            environment: Target environment
            encrypt_sensitive: Auto-encrypt sensitive-looking values
            
        Returns:
            Number of variables imported
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Sensitive key patterns
        sensitive_patterns = [
            r'password', r'secret', r'key', r'token', r'api_key',
            r'private', r'credential', r'auth'
        ]
        
        count = 0
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                
                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue
                
                # Parse key=value
                if '=' not in line:
                    continue
                
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                # Remove quotes
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]
                
                # Check if sensitive
                should_encrypt = encrypt_sensitive and any(
                    re.search(pattern, key, re.IGNORECASE)
                    for pattern in sensitive_patterns
                )
                
                self.set_var(
                    key=key,
                    value=value,
                    project=project,
                    environment=environment,
                    encrypt=should_encrypt
                )
                count += 1
        
        return count
    
    def export_env_file(
        self,
        file_path: Path,
        project: Optional[str] = None,
        environment: Optional[str] = None,
        include_encrypted: bool = True,
        include_descriptions: bool = True
    ) -> int:
        """
        Export variables to a .env file.
        
        Args:
            file_path: Output file path
            project: Source project
            environment: Source environment
            include_encrypted: Include encrypted variables (decrypted)
            include_descriptions: Add comments with descriptions
            
        Returns:
            Number of variables exported
        """
        vars = self.list_vars(project, environment)
        
        count = 0
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f"# Generated by EnvPilot\n")
            f.write(f"# Environment: {environment or 'current'}\n")
            f.write(f"# Date: {datetime.now().isoformat()}\n\n")
            
            for key, var in vars.items():
                if var.encrypted and not include_encrypted:
                    continue
                
                # Get decrypted value
                value = self.get_var(key, project, environment)
                if value is None:
                    continue
                
                # Write description as comment
                if include_descriptions and var.description:
                    f.write(f"# {var.description}\n")
                
                # Escape value if needed
                if ' ' in value or '"' in value or "'" in value:
                    value = f'"{value}"'
                
                f.write(f"{key}={value}\n")
                count += 1
        
        return count
    
    def export_json(
        self,
        file_path: Path,
        project: Optional[str] = None,
        environment: Optional[str] = None,
        decrypt: bool = False
    ) -> int:
        """Export variables to JSON format."""
        vars = self.list_vars(project, environment)
        
        data = {}
        for key, var in vars.items():
            value = var.value
            if var.encrypted and decrypt:
                value = self.crypto.decrypt(var.value)
            
            data[key] = {
                "value": value,
                "encrypted": var.encrypted,
                "description": var.description,
                "tags": var.tags
            }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return len(data)
    
    def copy_environment(
        self,
        source_env: str,
        target_env: str,
        project: Optional[str] = None
    ) -> int:
        """
        Copy all variables from one environment to another.
        
        Args:
            source_env: Source environment name
            target_env: Target environment name
            project: Project name
            
        Returns:
            Number of variables copied
        """
        proj = self._projects.get(project) if project else self.current_project
        if not proj:
            raise ValueError("No project selected")
        
        if source_env not in proj.environments:
            raise ValueError(f"Source environment '{source_env}' not found")
        
        if target_env not in proj.environments:
            proj.environments[target_env] = {}
        
        count = 0
        for key, var in proj.environments[source_env].items():
            # Create a copy of the variable
            new_var = EnvVariable(
                key=var.key,
                value=var.value,
                encrypted=var.encrypted,
                description=var.description,
                tags=var.tags.copy(),
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat()
            )
            proj.environments[target_env][key] = new_var
            count += 1
        
        self._save_storage()
        return count
    
    # ==================== Shell Integration ====================
    
    def export_shell(
        self,
        project: Optional[str] = None,
        environment: Optional[str] = None,
        shell: str = "bash"
    ) -> str:
        """
        Generate shell export commands.
        
        Args:
            project: Project name
            environment: Environment name
            shell: Shell type (bash, zsh, fish, powershell)
            
        Returns:
            Shell commands to export variables
        """
        vars = self.list_vars(project, environment)
        
        lines = []
        for key, var in vars.items():
            value = self.get_var(key, project, environment)
            if value is None:
                continue
            
            if shell in ("bash", "zsh"):
                lines.append(f'export {key}="{value}"')
            elif shell == "fish":
                lines.append(f'set -gx {key} "{value}"')
            elif shell == "powershell":
                lines.append(f'$env:{key} = "{value}"')
        
        return "\n".join(lines)
    
    def load_to_os_environ(
        self,
        project: Optional[str] = None,
        environment: Optional[str] = None
    ) -> int:
        """
        Load variables into os.environ.
        
        Returns:
            Number of variables loaded
        """
        vars = self.list_vars(project, environment)
        
        count = 0
        for key, var in vars.items():
            value = self.get_var(key, project, environment)
            if value is not None:
                os.environ[key] = value
                count += 1
        
        return count
