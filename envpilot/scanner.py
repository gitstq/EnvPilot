"""
EnvPilot Scanner Module - Environment Variable Leak Detection Engine
环境变量泄露检测引擎
"""

import re
import os
from pathlib import Path
from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class LeakSeverity(Enum):
    """Severity levels for detected leaks."""
    CRITICAL = "critical"      # API keys, passwords, tokens
    HIGH = "high"             # Database URLs, secrets
    MEDIUM = "medium"         # Internal URLs, usernames
    LOW = "low"               # Non-sensitive config
    INFO = "info"             # Potential issues


@dataclass
class LeakFinding:
    """Represents a detected leak or potential issue."""
    file_path: str
    line_number: int
    key_name: str
    value_preview: str
    severity: LeakSeverity
    pattern_type: str
    description: str
    recommendation: str
    
    def to_dict(self) -> Dict:
        return {
            "file_path": self.file_path,
            "line_number": self.line_number,
            "key_name": self.key_name,
            "value_preview": self.value_preview,
            "severity": self.severity.value,
            "pattern_type": self.pattern_type,
            "description": self.description,
            "recommendation": self.recommendation
        }


class LeakScanner:
    """
    Environment variable leak detection engine.
    环境变量泄露检测引擎。
    
    Features:
    - Scan code files for hardcoded secrets
    - Detect various secret patterns (API keys, tokens, passwords)
    - Check .env file permissions
    - Find potential .env file exposures in git history
    - Generate security reports
    """
    
    # Secret patterns with severity levels
    SECRET_PATTERNS = [
        # AWS
        (
            r'(?:A3T[A-Z0-9]|AKIA|AGPA|AIDA|AROA|AIPA|ANPA|ANVA|ASIA)[0-9A-Z]{16}',
            "AWS Access Key",
            LeakSeverity.CRITICAL,
            "AWS access key detected"
        ),
        (
            r'aws_secret_access_key\s*[=:]\s*["\']?([A-Za-z0-9/+=]{40})["\']?',
            "AWS Secret Key",
            LeakSeverity.CRITICAL,
            "AWS secret access key detected"
        ),
        # GitHub
        (
            r'ghp_[A-Za-z0-9]{36}',
            "GitHub Personal Token",
            LeakSeverity.CRITICAL,
            "GitHub personal access token detected"
        ),
        (
            r'github_pat_[A-Za-z0-9]{22}_[A-Za-z0-9]{59}',
            "GitHub Fine-grained Token",
            LeakSeverity.CRITICAL,
            "GitHub fine-grained token detected"
        ),
        # Generic API Keys
        (
            r'(?i)(?:api[_-]?key|apikey)\s*[=:]\s*["\']?([A-Za-z0-9_-]{20,})["\']?',
            "API Key",
            LeakSeverity.CRITICAL,
            "API key detected"
        ),
        # Private Keys
        (
            r'-----BEGIN (?:RSA |DSA |EC |OPENSSH )?PRIVATE KEY-----',
            "Private Key",
            LeakSeverity.CRITICAL,
            "Private key detected"
        ),
        # Database URLs
        (
            r'(?:mysql|postgres|mongodb|redis)://[^\s"\']+:[^\s"\']+@[^\s"\']+',
            "Database URL",
            LeakSeverity.HIGH,
            "Database URL with credentials detected"
        ),
        # JWT Secrets
        (
            r'(?i)jwt[_-]?secret\s*[=:]\s*["\']?([A-Za-z0-9_-]{20,})["\']?',
            "JWT Secret",
            LeakSeverity.HIGH,
            "JWT secret detected"
        ),
        # Passwords
        (
            r'(?i)(?:password|passwd|pwd)\s*[=:]\s*["\']?([^\s"\']{8,})["\']?',
            "Password",
            LeakSeverity.HIGH,
            "Password detected"
        ),
        # Secrets
        (
            r'(?i)(?:secret|token)\s*[=:]\s*["\']?([A-Za-z0-9_-]{16,})["\']?',
            "Secret/Token",
            LeakSeverity.HIGH,
            "Secret or token detected"
        ),
        # Stripe
        (
            r'sk_live_[0-9a-zA-Z]{24}',
            "Stripe Secret Key",
            LeakSeverity.CRITICAL,
            "Stripe live secret key detected"
        ),
        (
            r'rk_live_[0-9a-zA-Z]{24}',
            "Stripe Restricted Key",
            LeakSeverity.CRITICAL,
            "Stripe live restricted key detected"
        ),
        # Slack
        (
            r'xox[baprs]-[0-9]{10,13}-[0-9]{10,13}-[a-zA-Z0-9]{24}',
            "Slack Token",
            LeakSeverity.HIGH,
            "Slack token detected"
        ),
        # Google
        (
            r'AIza[0-9A-Za-z-_]{35}',
            "Google API Key",
            LeakSeverity.HIGH,
            "Google API key detected"
        ),
        # Generic sensitive patterns
        (
            r'(?i)(?:auth|credential|private)[_-]?(?:key|token)\s*[=:]\s*["\']?([^\s"\']+)["\']?',
            "Auth Credential",
            LeakSeverity.HIGH,
            "Authentication credential detected"
        ),
    ]
    
    # File patterns to scan
    SCAN_EXTENSIONS = {
        '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.go', '.rb', '.php',
        '.json', '.yaml', '.yml', '.xml', '.toml', '.ini', '.conf', '.config',
        '.sh', '.bash', '.zsh', '.env', '.env.local', '.env.development',
        '.env.production', '.env.staging', '.env.example'
    }
    
    # Files to skip
    SKIP_PATTERNS = {
        'node_modules', '.git', '__pycache__', 'venv', '.venv', 'env',
        '.envpilot', 'dist', 'build', '.idea', '.vscode', 'vendor',
        'package-lock.json', 'yarn.lock', 'poetry.lock'
    }
    
    def __init__(self, project_path: Path):
        """
        Initialize the scanner.
        
        Args:
            project_path: Root path of the project to scan
        """
        self.project_path = Path(project_path)
        self._compiled_patterns = [
            (re.compile(pattern), name, severity, desc)
            for pattern, name, severity, desc in self.SECRET_PATTERNS
        ]
    
    def _should_skip(self, path: Path) -> bool:
        """Check if path should be skipped."""
        for part in path.parts:
            if part in self.SKIP_PATTERNS:
                return True
        return False
    
    def _get_value_preview(self, value: str, max_len: int = 20) -> str:
        """Get a safe preview of a value."""
        if len(value) <= max_len:
            return value[:max_len] + "..." if len(value) > max_len else value
        return value[:max_len] + "..."
    
    def scan_file(self, file_path: Path) -> List[LeakFinding]:
        """
        Scan a single file for leaks.
        
        Args:
            file_path: Path to the file to scan
            
        Returns:
            List of LeakFinding objects
        """
        findings = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
        except (IOError, PermissionError):
            return findings
        
        for line_num, line in enumerate(lines, 1):
            for pattern, name, severity, desc in self._compiled_patterns:
                matches = pattern.finditer(line)
                for match in matches:
                    # Get the matched value
                    value = match.group(0)
                    if match.lastindex:
                        value = match.group(match.lastindex)
                    
                    findings.append(LeakFinding(
                        file_path=str(file_path.relative_to(self.project_path)),
                        line_number=line_num,
                        key_name=name,
                        value_preview=self._get_value_preview(value),
                        severity=severity,
                        pattern_type=name,
                        description=desc,
                        recommendation=f"Move this {name} to environment variables or use a secrets manager"
                    ))
        
        return findings
    
    def scan_directory(
        self,
        max_depth: int = 10,
        extensions: Optional[Set[str]] = None
    ) -> List[LeakFinding]:
        """
        Scan entire directory for leaks.
        
        Args:
            max_depth: Maximum directory depth to scan
            extensions: File extensions to scan (default: all known extensions)
            
        Returns:
            List of all LeakFinding objects
        """
        all_findings = []
        extensions = extensions or self.SCAN_EXTENSIONS
        
        for root, dirs, files in os.walk(self.project_path):
            # Calculate depth
            rel_path = Path(root).relative_to(self.project_path)
            depth = len(rel_path.parts)
            if depth > max_depth:
                continue
            
            # Filter out skipped directories
            dirs[:] = [d for d in dirs if d not in self.SKIP_PATTERNS]
            
            for file in files:
                file_path = Path(root) / file
                
                if self._should_skip(file_path):
                    continue
                
                # Check extension
                if file_path.suffix.lower() in extensions or file_path.name.startswith('.env'):
                    findings = self.scan_file(file_path)
                    all_findings.extend(findings)
        
        return all_findings
    
    def check_env_file_permissions(self) -> List[LeakFinding]:
        """
        Check .env file permissions.
        
        Returns:
            List of findings for insecure permissions
        """
        findings = []
        
        for env_file in self.project_path.rglob('.env*'):
            if self._should_skip(env_file):
                continue
            
            try:
                stat_info = env_file.stat()
                # Check if file is world-readable (Unix)
                if stat_info.st_mode & 0o004:
                    findings.append(LeakFinding(
                        file_path=str(env_file.relative_to(self.project_path)),
                        line_number=0,
                        key_name="File Permission",
                        value_preview="world-readable",
                        severity=LeakSeverity.MEDIUM,
                        pattern_type="File Permission",
                        description=".env file is world-readable",
                        recommendation="Run: chmod 600 <file> to restrict access"
                    ))
            except (OSError, PermissionError):
                pass
        
        return findings
    
    def find_env_files(self) -> List[Path]:
        """
        Find all .env files in the project.
        
        Returns:
            List of .env file paths
        """
        env_files = []
        
        for env_file in self.project_path.rglob('.env*'):
            if not self._should_skip(env_file):
                env_files.append(env_file)
        
        return env_files
    
    def check_gitignore(self) -> List[LeakFinding]:
        """
        Check if .env files are properly ignored by git.
        
        Returns:
            List of findings for exposed .env files
        """
        findings = []
        
        gitignore_path = self.project_path / '.gitignore'
        env_files = self.find_env_files()
        
        if not env_files:
            return findings
        
        # Check if .gitignore exists
        if not gitignore_path.exists():
            findings.append(LeakFinding(
                file_path=".gitignore",
                line_number=0,
                key_name="Git Ignore",
                value_preview="missing",
                severity=LeakSeverity.MEDIUM,
                pattern_type="Git Configuration",
                description="No .gitignore file found",
                recommendation="Create a .gitignore file and add .env entries"
            ))
            return findings
        
        # Read gitignore patterns
        try:
            with open(gitignore_path, 'r') as f:
                gitignore_patterns = set(line.strip() for line in f if line.strip())
        except IOError:
            return findings
        
        # Check if .env is ignored
        env_ignored = any(
            pattern in gitignore_patterns
            for pattern in ['.env', '.env*', '*.env', '.env.*']
        )
        
        if not env_ignored:
            findings.append(LeakFinding(
                file_path=".gitignore",
                line_number=0,
                key_name="Git Ignore",
                value_preview=".env not ignored",
                severity=LeakSeverity.HIGH,
                pattern_type="Git Configuration",
                description=".env files are not in .gitignore",
                recommendation="Add '.env' and '.env.*' to your .gitignore file"
            ))
        
        return findings
    
    def generate_report(
        self,
        findings: List[LeakFinding],
        format: str = "text"
    ) -> str:
        """
        Generate a security report.
        
        Args:
            findings: List of findings to report
            format: Output format (text, json, markdown)
            
        Returns:
            Formatted report string
        """
        if format == "json":
            import json
            return json.dumps([f.to_dict() for f in findings], indent=2)
        
        if format == "markdown":
            lines = ["# 🔒 EnvPilot Security Report\n"]
            
            # Summary
            severity_counts = {}
            for f in findings:
                sev = f.severity.value
                severity_counts[sev] = severity_counts.get(sev, 0) + 1
            
            lines.append("## 📊 Summary\n")
            lines.append(f"- **Total Findings:** {len(findings)}\n")
            for sev in ["critical", "high", "medium", "low", "info"]:
                if sev in severity_counts:
                    emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢", "info": "ℹ️"}[sev]
                    lines.append(f"- {emoji} **{sev.upper()}:** {severity_counts[sev]}\n")
            
            lines.append("\n## 🔍 Details\n")
            for f in findings:
                emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢", "info": "ℹ️"}[f.severity.value]
                lines.append(f"\n### {emoji} {f.key_name}\n")
                lines.append(f"- **File:** `{f.file_path}:{f.line_number}`\n")
                lines.append(f"- **Severity:** {f.severity.value}\n")
                lines.append(f"- **Description:** {f.description}\n")
                lines.append(f"- **Recommendation:** {f.recommendation}\n")
            
            return "".join(lines)
        
        # Text format
        lines = ["\n" + "=" * 60]
        lines.append("🔒 EnvPilot Security Scan Report")
        lines.append("=" * 60 + "\n")
        
        if not findings:
            lines.append("✅ No security issues found!\n")
            return "\n".join(lines)
        
        # Group by severity
        severity_groups: Dict[LeakSeverity, List[LeakFinding]] = {}
        for f in findings:
            if f.severity not in severity_groups:
                severity_groups[f.severity] = []
            severity_groups[f.severity].append(f)
        
        # Print by severity
        severity_order = [LeakSeverity.CRITICAL, LeakSeverity.HIGH, LeakSeverity.MEDIUM, LeakSeverity.LOW, LeakSeverity.INFO]
        severity_icons = {
            LeakSeverity.CRITICAL: "🔴",
            LeakSeverity.HIGH: "🟠",
            LeakSeverity.MEDIUM: "🟡",
            LeakSeverity.LOW: "🟢",
            LeakSeverity.INFO: "ℹ️"
        }
        
        for severity in severity_order:
            if severity not in severity_groups:
                continue
            
            icon = severity_icons[severity]
            lines.append(f"\n{icon} {severity.value.upper()} ({len(severity_groups[severity])} findings)")
            lines.append("-" * 40)
            
            for f in severity_groups[severity]:
                lines.append(f"\n  📁 {f.file_path}:{f.line_number}")
                lines.append(f"  🔑 {f.key_name}: {f.value_preview}")
                lines.append(f"  💡 {f.recommendation}")
        
        lines.append("\n" + "=" * 60)
        lines.append(f"Total: {len(findings)} findings")
        lines.append("=" * 60 + "\n")
        
        return "\n".join(lines)
    
    def full_scan(self) -> Tuple[List[LeakFinding], str]:
        """
        Run a full security scan.
        
        Returns:
            Tuple of (findings list, formatted report)
        """
        all_findings = []
        
        # Scan for hardcoded secrets
        all_findings.extend(self.scan_directory())
        
        # Check file permissions
        all_findings.extend(self.check_env_file_permissions())
        
        # Check gitignore
        all_findings.extend(self.check_gitignore())
        
        return all_findings, self.generate_report(all_findings)
