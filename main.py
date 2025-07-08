import sys
import os
import click # We will use click, so it's good practice to import it here or at least know it's a dependency

# Add the project root directory to the Python path.
# This allows Python to find modules within `pkg/`, `cmd/`, and `internal/`
# when you run `python main.py` from the root.
project_root = os.path.abspath(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import the main CLI group from your cmd/cli.py file.
# We'll define this 'cli' object in the next steps when we build cmd/cli.py.
try:
    from cmd.cli import cli
except ImportError as e:
    print(f"Error importing CLI: {e}")
    print("Please ensure 'cmd/cli.py' exists and contains a 'cli' Click group.")
    sys.exit(1)

if __name__ == '__main__':
    # This is the standard way to invoke a Click command group.
    # Click handles parsing command-line arguments and dispatching to the correct function.
    cli()