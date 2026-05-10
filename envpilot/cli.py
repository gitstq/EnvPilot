"""
EnvPilot CLI Module - Command Line Interface
命令行接口模块
"""

import argparse
import sys
import json
from pathlib import Path
from typing import Optional

from envpilot import __version__
from envpilot.core import EnvManager
from envpilot.scanner import LeakScanner


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        prog="envpilot",
        description="🔐 EnvPilot - Lightweight Environment Variables Intelligent Management Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  envpilot init myproject                    Create a new project
  envpilot set DATABASE_URL "postgres://..." Set a variable
  envpilot set API_KEY "secret" --encrypt    Set and encrypt a variable
  envpilot get DATABASE_URL                  Get a variable value
  envpilot list                              List all variables
  envpilot switch production                 Switch to production environment
  envpilot export .env                       Export to .env file
  envpilot import .env.example               Import from .env file
  envpilot scan                              Scan for security leaks
  envpilot tui                               Launch interactive TUI
"""
    )
    
    parser.add_argument(
        "-v", "--version",
        action="version",
        version=f"%(prog)s {__version__}"
    )
    
    parser.add_argument(
        "-p", "--project",
        help="Project name (uses current project if not specified)"
    )
    
    parser.add_argument(
        "-e", "--environment",
        help="Environment name (uses current environment if not specified)"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # init command
    init_parser = subparsers.add_parser("init", help="Initialize a new project")
    init_parser.add_argument("name", help="Project name")
    init_parser.add_argument("-d", "--description", help="Project description")
    
    # set command
    set_parser = subparsers.add_parser("set", help="Set an environment variable")
    set_parser.add_argument("key", help="Variable name")
    set_parser.add_argument("value", help="Variable value")
    set_parser.add_argument("--description", help="Variable description")
    set_parser.add_argument("--tags", help="Comma-separated tags")
    set_parser.add_argument("--encrypt", action="store_true", help="Encrypt the value")
    
    # get command
    get_parser = subparsers.add_parser("get", help="Get an environment variable")
    get_parser.add_argument("key", help="Variable name")
    get_parser.add_argument("--no-decrypt", action="store_true", help="Don't decrypt encrypted values")
    
    # delete command
    delete_parser = subparsers.add_parser("delete", help="Delete an environment variable")
    delete_parser.add_argument("key", help="Variable name")
    
    # list command
    list_parser = subparsers.add_parser("list", help="List all variables")
    list_parser.add_argument("--tag", help="Filter by tag")
    list_parser.add_argument("--json", action="store_true", help="Output as JSON")
    
    # search command
    search_parser = subparsers.add_parser("search", help="Search variables")
    search_parser.add_argument("query", help="Search query")
    
    # switch command
    switch_parser = subparsers.add_parser("switch", help="Switch environment")
    switch_parser.add_argument("environment", help="Environment name")
    
    # env command (environment management)
    env_parser = subparsers.add_parser("env", help="Manage environments")
    env_parser.add_argument("action", choices=["list", "add", "delete", "copy"])
    env_parser.add_argument("name", nargs="?", help="Environment name")
    env_parser.add_argument("--source", help="Source environment for copy")
    
    # project command
    project_parser = subparsers.add_parser("project", help="Manage projects")
    project_parser.add_argument("action", choices=["list", "delete", "switch"])
    project_parser.add_argument("name", nargs="?", help="Project name")
    
    # import command
    import_parser = subparsers.add_parser("import", help="Import variables from file")
    import_parser.add_argument("file", help="Path to .env file")
    import_parser.add_argument("--no-encrypt-sensitive", action="store_true", 
                               help="Don't auto-encrypt sensitive values")
    
    # export command
    export_parser = subparsers.add_parser("export", help="Export variables")
    export_parser.add_argument("file", nargs="?", help="Output file path")
    export_parser.add_argument("--format", choices=["env", "json", "shell"], 
                               default="env", help="Export format")
    export_parser.add_argument("--shell", choices=["bash", "zsh", "fish", "powershell"],
                               default="bash", help="Shell type for shell format")
    export_parser.add_argument("--no-decrypt", action="store_true", 
                               help="Don't decrypt encrypted values")
    
    # scan command
    scan_parser = subparsers.add_parser("scan", help="Scan for security leaks")
    scan_parser.add_argument("path", nargs="?", default=".", help="Directory to scan")
    scan_parser.add_argument("--format", choices=["text", "json", "markdown"],
                             default="text", help="Output format")
    
    # tui command
    subparsers.add_parser("tui", help="Launch interactive TUI")
    
    # password command
    password_parser = subparsers.add_parser("password", help="Set master password")
    password_parser.add_argument("--verify", action="store_true", help="Verify existing password")
    
    return parser


def get_manager(args) -> EnvManager:
    """Get the EnvManager instance."""
    return EnvManager()


def cmd_init(args, manager: EnvManager):
    """Initialize a new project."""
    try:
        project = manager.create_project(
            name=args.name,
            description=args.description or ""
        )
        print(f"✅ Project '{args.name}' created successfully!")
        print(f"   Environments: {', '.join(project.environments.keys())}")
    except ValueError as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_set(args, manager: EnvManager):
    """Set an environment variable."""
    # Check if encryption is requested
    if args.encrypt and not manager._master_password:
        import getpass
        password = getpass.getpass("Enter master password: ")
        if not manager.verify_master_password(password):
            manager.set_master_password(password)
        else:
            manager._master_password = password
            manager._crypto = None  # Reset crypto to use new password
    
    try:
        tags = args.tags.split(",") if args.tags else []
        manager.set_var(
            key=args.key,
            value=args.value,
            project=args.project,
            environment=args.environment,
            description=args.description or "",
            tags=tags,
            encrypt=args.encrypt
        )
        enc_status = " (encrypted)" if args.encrypt else ""
        print(f"✅ Variable '{args.key}' saved{enc_status}")
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_get(args, manager: EnvManager):
    """Get an environment variable."""
    value = manager.get_var(
        key=args.key,
        project=args.project,
        environment=args.environment,
        decrypt=not args.no_decrypt
    )
    
    if value is not None:
        print(value)
    else:
        print(f"❌ Variable '{args.key}' not found", file=sys.stderr)
        sys.exit(1)


def cmd_delete(args, manager: EnvManager):
    """Delete an environment variable."""
    if manager.delete_var(args.key, args.project, args.environment):
        print(f"✅ Variable '{args.key}' deleted")
    else:
        print(f"❌ Variable '{args.key}' not found", file=sys.stderr)
        sys.exit(1)


def cmd_list(args, manager: EnvManager):
    """List all variables."""
    vars = manager.list_vars(
        project=args.project,
        environment=args.environment,
        tag=args.tag
    )
    
    if not vars:
        print("No variables found")
        return
    
    if args.json:
        data = {}
        for key, var in vars.items():
            value = manager.get_var(key, args.project, args.environment)
            data[key] = {
                "value": value,
                "encrypted": var.encrypted,
                "description": var.description,
                "tags": var.tags
            }
        print(json.dumps(data, indent=2))
    else:
        print(f"\n📋 Variables ({len(vars)}):\n")
        for key, var in vars.items():
            enc = "🔒 " if var.encrypted else "  "
            value = "••••••" if var.encrypted else var.value
            if len(value) > 40:
                value = value[:37] + "..."
            print(f"  {enc}{key} = {value}")
            if var.description:
                print(f"      └─ {var.description}")


def cmd_search(args, manager: EnvManager):
    """Search variables."""
    results = manager.search_vars(args.query, args.project)
    
    if not results:
        print("No matching variables found")
        return
    
    for env_path, vars in results.items():
        print(f"\n📁 {env_path}:")
        for key, var in vars.items():
            print(f"  • {key}: {var.description or var.value[:30]}")


def cmd_switch(args, manager: EnvManager):
    """Switch environment."""
    try:
        manager.switch_environment(args.environment, args.project)
        print(f"✅ Switched to environment '{args.environment}'")
    except ValueError as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_env(args, manager: EnvManager):
    """Manage environments."""
    if args.action == "list":
        envs = manager.list_environments(args.project)
        project = manager.get_project(args.project) if args.project else manager.current_project
        
        if project:
            print(f"\n📁 Environments in '{project.name}':\n")
            for env in envs:
                current = " ← current" if env == project.current_environment else ""
                var_count = len(project.environments.get(env, {}))
                print(f"  • {env} ({var_count} variables){current}")
        else:
            print("No project selected")
    
    elif args.action == "add":
        if not args.name:
            print("❌ Environment name required", file=sys.stderr)
            sys.exit(1)
        try:
            manager.add_environment(args.project or manager._current_project, args.name)
            print(f"✅ Environment '{args.name}' added")
        except ValueError as e:
            print(f"❌ Error: {e}", file=sys.stderr)
            sys.exit(1)
    
    elif args.action == "delete":
        if not args.name:
            print("❌ Environment name required", file=sys.stderr)
            sys.exit(1)
        if manager.delete_environment(args.project or manager._current_project, args.name):
            print(f"✅ Environment '{args.name}' deleted")
        else:
            print(f"❌ Environment '{args.name}' not found", file=sys.stderr)
            sys.exit(1)
    
    elif args.action == "copy":
        if not args.name or not args.source:
            print("❌ Source and target environment names required", file=sys.stderr)
            sys.exit(1)
        try:
            count = manager.copy_environment(args.source, args.name, args.project)
            print(f"✅ Copied {count} variables to '{args.name}'")
        except ValueError as e:
            print(f"❌ Error: {e}", file=sys.stderr)
            sys.exit(1)


def cmd_project(args, manager: EnvManager):
    """Manage projects."""
    if args.action == "list":
        projects = manager.list_projects()
        print(f"\n📁 Projects ({len(projects)}):\n")
        for name in projects:
            current = " ← current" if name == manager._current_project else ""
            proj = manager.get_project(name)
            env_count = len(proj.environments) if proj else 0
            print(f"  • {name} ({env_count} environments){current}")
    
    elif args.action == "switch":
        if not args.name:
            print("❌ Project name required", file=sys.stderr)
            sys.exit(1)
        try:
            manager.set_current_project(args.name)
            print(f"✅ Switched to project '{args.name}'")
        except ValueError as e:
            print(f"❌ Error: {e}", file=sys.stderr)
            sys.exit(1)
    
    elif args.action == "delete":
        if not args.name:
            print("❌ Project name required", file=sys.stderr)
            sys.exit(1)
        if manager.delete_project(args.name):
            print(f"✅ Project '{args.name}' deleted")
        else:
            print(f"❌ Project '{args.name}' not found", file=sys.stderr)
            sys.exit(1)


def cmd_import(args, manager: EnvManager):
    """Import variables from file."""
    file_path = Path(args.file)
    if not file_path.exists():
        print(f"❌ File not found: {args.file}", file=sys.stderr)
        sys.exit(1)
    
    try:
        count = manager.import_env_file(
            file_path,
            project=args.project,
            environment=args.environment,
            encrypt_sensitive=not args.no_encrypt_sensitive
        )
        print(f"✅ Imported {count} variables from {args.file}")
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_export(args, manager: EnvManager):
    """Export variables."""
    if args.format == "shell":
        commands = manager.export_shell(
            project=args.project,
            environment=args.environment,
            shell=args.shell
        )
        print(commands)
    else:
        file_path = Path(args.file) if args.file else Path(".env")
        
        if args.format == "env":
            count = manager.export_env_file(
                file_path,
                project=args.project,
                environment=args.environment,
                include_encrypted=not args.no_decrypt
            )
        else:  # json
            count = manager.export_json(
                file_path,
                project=args.project,
                environment=args.environment,
                decrypt=not args.no_decrypt
            )
        
        print(f"✅ Exported {count} variables to {file_path}")


def cmd_scan(args, manager: EnvManager):
    """Scan for security leaks."""
    scan_path = Path(args.path)
    if not scan_path.exists():
        print(f"❌ Path not found: {args.path}", file=sys.stderr)
        sys.exit(1)
    
    scanner = LeakScanner(scan_path)
    findings, report = scanner.full_scan()
    
    if args.format == "json":
        import json
        print(json.dumps([f.to_dict() for f in findings], indent=2))
    else:
        print(report)


def cmd_tui(args, manager: EnvManager):
    """Launch interactive TUI."""
    from envpilot.tui import TUI
    tui = TUI(manager)
    tui.run()


def cmd_password(args, manager: EnvManager):
    """Set or verify master password."""
    import getpass
    
    if args.verify:
        password = getpass.getpass("Enter master password: ")
        if manager.verify_master_password(password):
            print("✅ Password verified")
        else:
            print("❌ Incorrect password", file=sys.stderr)
            sys.exit(1)
    else:
        password = getpass.getpass("Enter new master password: ")
        confirm = getpass.getpass("Confirm password: ")
        if password != confirm:
            print("❌ Passwords do not match", file=sys.stderr)
            sys.exit(1)
        manager.set_master_password(password)
        print("✅ Master password set")


def main():
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(0)
    
    manager = get_manager(args)
    
    commands = {
        "init": cmd_init,
        "set": cmd_set,
        "get": cmd_get,
        "delete": cmd_delete,
        "list": cmd_list,
        "search": cmd_search,
        "switch": cmd_switch,
        "env": cmd_env,
        "project": cmd_project,
        "import": cmd_import,
        "export": cmd_export,
        "scan": cmd_scan,
        "tui": cmd_tui,
        "password": cmd_password,
    }
    
    if args.command in commands:
        commands[args.command](args, manager)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
