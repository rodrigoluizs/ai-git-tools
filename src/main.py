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
      ai-git-tools [options]

    Description:
      AI-powered Git tools for automating common Git tasks like generating GitHub pull requests.

    Options:
      -h, --help      Show this help message and exit.

    Examples:
      ai-git-tools      Automatically create a GitHub pull request using code changes.
    """
    print(help_text)


def main():
    """
    Main entry point for the command-line tool.
    """
    parser = argparse.ArgumentParser(
        description="AI Git Tools - Command Line Tool",
        usage="ai-git-tools [options]",
        add_help=False
    )

    parser.add_argument(
        "-h", "--help",
        action="store_true",
        help="Show this help message and exit."
    )

    args = parser.parse_args()

    if args.help:
        display_help()
        sys.exit(0)

    try:
        git_change_manager.main()
    except subprocess.CalledProcessError as e:
        print(f"Error executing GitHub PR workflow: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
