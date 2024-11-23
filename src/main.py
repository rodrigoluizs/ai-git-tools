import argparse
import subprocess
import sys

from src.core import git_change_manager


def display_help():
    """
    Display help documentation for the command-line tool.
    """
    help_text = """
    AI Git Tools - Command Line Tool

    Usage:
      ai-git-tools <command> [options]

    Commands:
      github-pr       Generate a GitHub pull request based on code changes.
      
    Options:
      -h, --help      Show this help message and exit.

    Examples:
      ai-git-tools github-pr      Create a GitHub pull request using code changes.
    """
    print(help_text)


def main():
    """
    Main entry point for the command-line tool.
    """
    parser = argparse.ArgumentParser(
        description="AI Git Tools - Command Line Tool",
        usage="ai-git-tools <command> [options]",
        add_help=False
    )

    parser.add_argument(
        "command",
        help="The command to execute (e.g., github-pr).",
        nargs="?"
    )
    parser.add_argument(
        "-h", "--help",
        action="store_true",
        help="Show this help message and exit."
    )

    args = parser.parse_args()

    if args.help or not args.command:
        display_help()
        sys.exit(0)

    if args.command == "github-pr":
        # Call the GitHub PR command (execute the git_change_manager script)
        try:
            git_change_manager.main()
        except subprocess.CalledProcessError as e:
            print(f"Error executing 'github-pr': {e}")
            sys.exit(1)
    else:
        print(f"Unknown command: {args.command}")
        display_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
