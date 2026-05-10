"""
EnvPilot TUI Module - Terminal User Interface
终端用户界面模块
"""

import sys
from typing import Optional, List, Dict
from datetime import datetime

from envpilot.core import EnvManager, EnvVariable, EnvProject


class Colors:
    """ANSI color codes for terminal output."""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    
    # Foreground colors
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    
    # Background colors
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"


def clear_screen():
    """Clear the terminal screen."""
    print("\033[2J\033[H", end="")


def print_header():
    """Print the application header."""
    header = f"""
{Colors.CYAN}╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   {Colors.BOLD}{Colors.WHITE}🔐 EnvPilot - Environment Variables Manager{Colors.RESET}{Colors.CYAN}              ║
║   {Colors.DIM}Lightweight • Secure • Multi-Environment{Colors.RESET}{Colors.CYAN}                  ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝{Colors.RESET}
"""
    print(header)


def print_menu(items: List[tuple], title: str = "Menu"):
    """
    Print a menu with numbered options.
    
    Args:
        items: List of (key, label) tuples
        title: Menu title
    """
    print(f"\n{Colors.BOLD}{Colors.WHITE}{title}{Colors.RESET}")
    print("─" * 40)
    
    for i, (key, label) in enumerate(items, 1):
        print(f"  {Colors.CYAN}[{i}]{Colors.RESET} {label}")
    
    print(f"  {Colors.DIM}[q] Back / Quit{Colors.RESET}")
    print()


def print_table(headers: List[str], rows: List[List[str]], title: str = ""):
    """
    Print a formatted table.
    
    Args:
        headers: Column headers
        rows: Table rows
        title: Optional table title
    """
    if title:
        print(f"\n{Colors.BOLD}{Colors.WHITE}{title}{Colors.RESET}")
    
    # Calculate column widths
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            if i < len(widths):
                widths[i] = max(widths[i], len(str(cell)))
    
    # Print header
    header_line = " │ ".join(h.ljust(w) for h, w in zip(headers, widths))
    separator = "─┼─".join("─" * w for w in widths)
    
    print(f"  {Colors.BOLD}{header_line}{Colors.RESET}")
    print(f"  {separator}")
    
    # Print rows
    for row in rows:
        row_line = " │ ".join(str(cell).ljust(w) for cell, w in zip(row, widths))
        print(f"  {row_line}")


def print_var(var: EnvVariable, key: str, show_value: bool = True):
    """Print a single variable with formatting."""
    encrypted_badge = f"{Colors.YELLOW}[ENCRYPTED]{Colors.RESET} " if var.encrypted else ""
    tags_str = f" {Colors.DIM}[{', '.join(var.tags)}]{Colors.RESET}" if var.tags else ""
    
    print(f"\n  {Colors.BOLD}{Colors.CYAN}{key}{Colors.RESET} {encrypted_badge}{tags_str}")
    
    if show_value:
        if var.encrypted:
            print(f"  {Colors.DIM}Value: ••••••••••••{Colors.RESET}")
        else:
            # Truncate long values
            value_display = var.value if len(var.value) <= 50 else var.value[:47] + "..."
            print(f"  {Colors.WHITE}Value: {value_display}{Colors.RESET}")
    
    if var.description:
        print(f"  {Colors.DIM}Description: {var.description}{Colors.RESET}")
    
    print(f"  {Colors.DIM}Updated: {var.updated_at}{Colors.RESET}")


def print_success(message: str):
    """Print a success message."""
    print(f"\n{Colors.GREEN}✓ {message}{Colors.RESET}\n")


def print_error(message: str):
    """Print an error message."""
    print(f"\n{Colors.RED}✗ {message}{Colors.RESET}\n")


def print_warning(message: str):
    """Print a warning message."""
    print(f"\n{Colors.YELLOW}⚠ {message}{Colors.RESET}\n")


def print_info(message: str):
    """Print an info message."""
    print(f"\n{Colors.BLUE}ℹ {message}{Colors.RESET}\n")


def get_input(prompt: str, default: str = "") -> str:
    """Get user input with optional default value."""
    if default:
        prompt_text = f"{prompt} [{default}]: "
    else:
        prompt_text = f"{prompt}: "
    
    try:
        value = input(f"{Colors.CYAN}{prompt_text}{Colors.RESET}").strip()
        return value if value else default
    except (EOFError, KeyboardInterrupt):
        print()
        return ""


def get_password(prompt: str) -> str:
    """Get password input without echoing."""
    import getpass
    try:
        return getpass.getpass(f"{Colors.CYAN}{prompt}: {Colors.RESET}")
    except (EOFError, KeyboardInterrupt):
        print()
        return ""


def confirm(prompt: str, default: bool = False) -> bool:
    """Get yes/no confirmation."""
    default_str = "Y/n" if default else "y/N"
    try:
        response = input(f"{Colors.CYAN}{prompt} [{default_str}]: {Colors.RESET}").strip().lower()
        if not response:
            return default
        return response in ('y', 'yes', '是')
    except (EOFError, KeyboardInterrupt):
        print()
        return False


class TUI:
    """
    Terminal User Interface for EnvPilot.
    EnvPilot终端用户界面。
    """
    
    def __init__(self, manager: EnvManager):
        self.manager = manager
        self.running = True
    
    def run(self):
        """Run the main TUI loop."""
        while self.running:
            clear_screen()
            print_header()
            self._show_status()
            self._main_menu()
    
    def _show_status(self):
        """Show current status."""
        project = self.manager.current_project
        if project:
            env = project.current_environment
            print(f"  {Colors.DIM}Project:{Colors.RESET} {Colors.BOLD}{project.name}{Colors.RESET}")
            print(f"  {Colors.DIM}Environment:{Colors.RESET} {Colors.GREEN}{env}{Colors.RESET}")
        else:
            print(f"  {Colors.DIM}No project selected{Colors.RESET}")
        print()
    
    def _main_menu(self):
        """Show main menu."""
        items = [
            ("projects", "📁 Project Management"),
            ("vars", "📝 Variable Management"),
            ("envs", "🔄 Environment Management"),
            ("import", "📥 Import Variables"),
            ("export", "📤 Export Variables"),
            ("scan", "🔍 Security Scan"),
            ("shell", "💻 Shell Integration"),
        ]
        
        print_menu(items, "Main Menu")
        
        choice = get_input("Select option")
        
        actions = {
            "1": self._projects_menu,
            "2": self._vars_menu,
            "3": self._envs_menu,
            "4": self._import_menu,
            "5": self._export_menu,
            "6": self._scan_menu,
            "7": self._shell_menu,
            "q": self._quit,
        }
        
        if choice in actions:
            actions[choice]()
    
    def _projects_menu(self):
        """Project management menu."""
        while True:
            clear_screen()
            print_header()
            
            projects = self.manager.list_projects()
            if projects:
                rows = []
                for name in projects:
                    proj = self.manager.get_project(name)
                    current = "✓" if name == self.manager._current_project else ""
                    env_count = len(proj.environments) if proj else 0
                    rows.append([current, name, str(env_count), proj.description[:30] if proj else ""])
                
                print_table(["", "Project", "Envs", "Description"], rows, "Projects")
            else:
                print_info("No projects yet. Create one to get started!")
            
            items = [
                ("create", "➕ Create Project"),
                ("switch", "🔄 Switch Project"),
                ("delete", "🗑️ Delete Project"),
            ]
            
            print_menu(items, "Project Actions")
            
            choice = get_input("Select option")
            
            if choice == "1":
                self._create_project()
            elif choice == "2":
                self._switch_project()
            elif choice == "3":
                self._delete_project()
            elif choice.lower() == "q":
                break
    
    def _create_project(self):
        """Create a new project."""
        name = get_input("Project name")
        if not name:
            print_error("Project name is required")
            get_input("Press Enter to continue")
            return
        
        description = get_input("Description (optional)")
        
        try:
            self.manager.create_project(name, description)
            print_success(f"Project '{name}' created successfully!")
        except ValueError as e:
            print_error(str(e))
        
        get_input("Press Enter to continue")
    
    def _switch_project(self):
        """Switch to a different project."""
        projects = self.manager.list_projects()
        if not projects:
            print_warning("No projects available")
            get_input("Press Enter to continue")
            return
        
        print("\nAvailable projects:")
        for i, name in enumerate(projects, 1):
            current = " (current)" if name == self.manager._current_project else ""
            print(f"  {i}. {name}{current}")
        
        choice = get_input("Select project number")
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(projects):
                self.manager.set_current_project(projects[idx])
                print_success(f"Switched to project '{projects[idx]}'")
        except ValueError:
            print_error("Invalid selection")
        
        get_input("Press Enter to continue")
    
    def _delete_project(self):
        """Delete a project."""
        projects = self.manager.list_projects()
        if not projects:
            print_warning("No projects to delete")
            get_input("Press Enter to continue")
            return
        
        print("\nAvailable projects:")
        for i, name in enumerate(projects, 1):
            print(f"  {i}. {name}")
        
        choice = get_input("Select project to delete")
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(projects):
                if confirm(f"Delete project '{projects[idx]}'?", default=False):
                    self.manager.delete_project(projects[idx])
                    print_success(f"Project '{projects[idx]}' deleted")
        except ValueError:
            print_error("Invalid selection")
        
        get_input("Press Enter to continue")
    
    def _vars_menu(self):
        """Variable management menu."""
        project = self.manager.current_project
        if not project:
            print_warning("Please select a project first")
            get_input("Press Enter to continue")
            return
        
        while True:
            clear_screen()
            print_header()
            self._show_status()
            
            vars = self.manager.list_vars()
            if vars:
                rows = []
                for key, var in vars.items():
                    enc = "🔒" if var.encrypted else "  "
                    val_preview = "••••••" if var.encrypted else (var.value[:20] + "..." if len(var.value) > 20 else var.value)
                    rows.append([enc, key, val_preview, var.description[:25] if var.description else ""])
                
                print_table(["", "Key", "Value", "Description"], rows, f"Variables ({project.current_environment})")
            else:
                print_info("No variables in this environment")
            
            items = [
                ("set", "➕ Add/Update Variable"),
                ("get", "🔍 View Variable"),
                ("delete", "🗑️ Delete Variable"),
                ("search", "🔎 Search Variables"),
            ]
            
            print_menu(items, "Variable Actions")
            
            choice = get_input("Select option")
            
            if choice == "1":
                self._set_var()
            elif choice == "2":
                self._get_var()
            elif choice == "3":
                self._delete_var()
            elif choice == "4":
                self._search_vars()
            elif choice.lower() == "q":
                break
    
    def _set_var(self):
        """Add or update a variable."""
        key = get_input("Variable name")
        if not key:
            print_error("Variable name is required")
            get_input("Press Enter to continue")
            return
        
        # Check if variable exists
        existing = self.manager.get_var_info(key)
        if existing:
            print_info(f"Variable '{key}' exists. Updating...")
        
        value = get_input("Value")
        if not value:
            print_error("Value is required")
            get_input("Press Enter to continue")
            return
        
        description = get_input("Description (optional)")
        tags_str = get_input("Tags (comma-separated, optional)")
        tags = [t.strip() for t in tags_str.split(",") if t.strip()] if tags_str else []
        
        encrypt = confirm("Encrypt this value?", default=False)
        
        if encrypt and not self.manager._master_password:
            password = get_password("Set master password for encryption")
            if password:
                self.manager.set_master_password(password)
        
        try:
            self.manager.set_var(key, value, description=description, tags=tags, encrypt=encrypt)
            print_success(f"Variable '{key}' saved successfully!")
        except Exception as e:
            print_error(str(e))
        
        get_input("Press Enter to continue")
    
    def _get_var(self):
        """View a variable."""
        key = get_input("Variable name")
        if not key:
            return
        
        var = self.manager.get_var_info(key)
        if var:
            value = self.manager.get_var(key)
            print_var(var, key)
            if var.encrypted:
                if confirm("Show decrypted value?", default=False):
                    print(f"\n  {Colors.WHITE}Decrypted: {value}{Colors.RESET}")
        else:
            print_error(f"Variable '{key}' not found")
        
        get_input("Press Enter to continue")
    
    def _delete_var(self):
        """Delete a variable."""
        key = get_input("Variable name to delete")
        if not key:
            return
        
        var = self.manager.get_var_info(key)
        if not var:
            print_error(f"Variable '{key}' not found")
            get_input("Press Enter to continue")
            return
        
        if confirm(f"Delete variable '{key}'?", default=False):
            self.manager.delete_var(key)
            print_success(f"Variable '{key}' deleted")
        
        get_input("Press Enter to continue")
    
    def _search_vars(self):
        """Search variables."""
        query = get_input("Search query")
        if not query:
            return
        
        results = self.manager.search_vars(query)
        
        if results:
            for env_path, vars in results.items():
                print(f"\n{Colors.BOLD}{env_path}:{Colors.RESET}")
                for key, var in vars.items():
                    print(f"  • {key}: {var.description or var.value[:30]}")
        else:
            print_info("No matching variables found")
        
        get_input("Press Enter to continue")
    
    def _envs_menu(self):
        """Environment management menu."""
        project = self.manager.current_project
        if not project:
            print_warning("Please select a project first")
            get_input("Press Enter to continue")
            return
        
        while True:
            clear_screen()
            print_header()
            self._show_status()
            
            envs = self.manager.list_environments()
            if envs:
                rows = []
                for env in envs:
                    current = "✓" if env == project.current_environment else ""
                    var_count = len(project.environments.get(env, {}))
                    rows.append([current, env, str(var_count)])
                
                print_table(["", "Environment", "Variables"], rows, "Environments")
            
            items = [
                ("add", "➕ Add Environment"),
                ("switch", "🔄 Switch Environment"),
                ("copy", "📋 Copy Environment"),
                ("delete", "🗑️ Delete Environment"),
            ]
            
            print_menu(items, "Environment Actions")
            
            choice = get_input("Select option")
            
            if choice == "1":
                env_name = get_input("Environment name")
                if env_name:
                    try:
                        self.manager.add_environment(project.name, env_name)
                        print_success(f"Environment '{env_name}' added")
                    except ValueError as e:
                        print_error(str(e))
                get_input("Press Enter to continue")
            elif choice == "2":
                env_name = get_input("Environment name")
                if env_name:
                    try:
                        self.manager.switch_environment(env_name)
                        print_success(f"Switched to '{env_name}'")
                    except ValueError as e:
                        print_error(str(e))
                get_input("Press Enter to continue")
            elif choice == "3":
                source = get_input("Source environment")
                target = get_input("Target environment")
                if source and target:
                    try:
                        count = self.manager.copy_environment(source, target)
                        print_success(f"Copied {count} variables")
                    except ValueError as e:
                        print_error(str(e))
                get_input("Press Enter to continue")
            elif choice == "4":
                env_name = get_input("Environment to delete")
                if env_name and confirm(f"Delete '{env_name}'?", default=False):
                    if self.manager.delete_environment(project.name, env_name):
                        print_success(f"Environment '{env_name}' deleted")
                    else:
                        print_error("Failed to delete environment")
                get_input("Press Enter to continue")
            elif choice.lower() == "q":
                break
    
    def _import_menu(self):
        """Import variables menu."""
        project = self.manager.current_project
        if not project:
            print_warning("Please select a project first")
            get_input("Press Enter to continue")
            return
        
        clear_screen()
        print_header()
        self._show_status()
        
        print(f"\n{Colors.BOLD}📥 Import Variables{Colors.RESET}")
        print("─" * 40)
        
        file_path = get_input("Path to .env file")
        if not file_path:
            return
        
        from pathlib import Path
        try:
            count = self.manager.import_env_file(Path(file_path))
            print_success(f"Imported {count} variables")
        except FileNotFoundError:
            print_error(f"File not found: {file_path}")
        except Exception as e:
            print_error(str(e))
        
        get_input("Press Enter to continue")
    
    def _export_menu(self):
        """Export variables menu."""
        project = self.manager.current_project
        if not project:
            print_warning("Please select a project first")
            get_input("Press Enter to continue")
            return
        
        clear_screen()
        print_header()
        self._show_status()
        
        print(f"\n{Colors.BOLD}📤 Export Variables{Colors.RESET}")
        print("─" * 40)
        
        print("\n  [1] Export to .env file")
        print("  [2] Export to JSON file")
        print("  [3] Export shell commands")
        
        choice = get_input("Select format")
        
        from pathlib import Path
        
        if choice == "1":
            file_path = get_input("Output file path", ".env")
            count = self.manager.export_env_file(Path(file_path))
            print_success(f"Exported {count} variables to {file_path}")
        elif choice == "2":
            file_path = get_input("Output file path", "env.json")
            decrypt = confirm("Include decrypted values?", default=False)
            count = self.manager.export_json(Path(file_path), decrypt=decrypt)
            print_success(f"Exported {count} variables to {file_path}")
        elif choice == "3":
            shell = get_input("Shell type (bash/zsh/fish/powershell)", "bash")
            commands = self.manager.export_shell(shell=shell)
            print(f"\n{Colors.CYAN}# Add to your shell config or run directly:{Colors.RESET}")
            print(commands)
        
        get_input("Press Enter to continue")
    
    def _scan_menu(self):
        """Security scan menu."""
        clear_screen()
        print_header()
        
        print(f"\n{Colors.BOLD}🔍 Security Scan{Colors.RESET}")
        print("─" * 40)
        
        scan_path = get_input("Directory to scan", ".")
        
        from pathlib import Path
        from envpilot.scanner import LeakScanner
        
        scanner = LeakScanner(Path(scan_path))
        
        print_info("Scanning for security issues...")
        findings, report = scanner.full_scan()
        
        print(report)
        
        get_input("Press Enter to continue")
    
    def _shell_menu(self):
        """Shell integration menu."""
        project = self.manager.current_project
        if not project:
            print_warning("Please select a project first")
            get_input("Press Enter to continue")
            return
        
        clear_screen()
        print_header()
        self._show_status()
        
        print(f"\n{Colors.BOLD}💻 Shell Integration{Colors.RESET}")
        print("─" * 40)
        
        print("\n  [1] Generate export commands (bash/zsh)")
        print("  [2] Generate export commands (fish)")
        print("  [3] Generate export commands (PowerShell)")
        print("  [4] Load into current process")
        
        choice = get_input("Select option")
        
        if choice == "1":
            commands = self.manager.export_shell(shell="bash")
            print(f"\n{Colors.CYAN}# Run these commands or add to ~/.bashrc/~/.zshrc:{Colors.RESET}")
            print(commands)
        elif choice == "2":
            commands = self.manager.export_shell(shell="fish")
            print(f"\n{Colors.CYAN}# Run these commands or add to ~/.config/fish/config.fish:{Colors.RESET}")
            print(commands)
        elif choice == "3":
            commands = self.manager.export_shell(shell="powershell")
            print(f"\n{Colors.CYAN}# Run these commands in PowerShell:{Colors.RESET}")
            print(commands)
        elif choice == "4":
            count = self.manager.load_to_os_environ()
            print_success(f"Loaded {count} variables into current process")
        
        get_input("Press Enter to continue")
    
    def _quit(self):
        """Quit the application."""
        self.running = False
        print(f"\n{Colors.GREEN}👋 Goodbye!{Colors.RESET}\n")
