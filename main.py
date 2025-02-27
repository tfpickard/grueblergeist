#!/usr/bin/env python3
"""
Main entry point for Grüblergeist.
Run in CLI mode, Web mode, Evolve mode, or Debugging Dashboard mode.
"""

import argparse
import logging
import sys

from rich.logging import RichHandler

from assistant.cli import run_cli
from assistant.config import load_config
from assistant.dashboard import run_dashboard  # New Import
from assistant.db import init_db
from assistant.evolve import evolve_code, evolve_self
from assistant.web import run_web


def setup_logging():
    """Configure logging with Rich handler."""
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler()],
    )


def main():
    """Parse CLI arguments and run Grüblergeist in the selected mode."""
    setup_logging()
    load_config()
    init_db()

    parser = argparse.ArgumentParser(description="Grüblergeist Chat Assistant")
    parser.add_argument(
        "--mode",
        choices=["cli", "web", "evolve", "evolve-self", "debug"],
        default="cli",
        help="Run in CLI mode, Web mode, Evolve mode, Self-Evolve mode, or Debug Dashboard mode.",
    )
    parser.add_argument("--source", help="Source file path for evolve.")
    parser.add_argument("--output", help="Output file path for evolve.")
    parser.add_argument(
        "--instructions", help="Custom instructions for code evolution."
    )
    args = parser.parse_args()

    if args.mode == "cli":
        run_cli()
    elif args.mode == "web":
        run_web()
    elif args.mode == "evolve":
        if not args.source or not args.output:
            print("Evolve mode requires --source and --output.")
            sys.exit(1)
        evolve_code(args.source, args.output, instructions=args.instructions)
    elif args.mode == "evolve-self":
        if not args.source or not args.output:
            print("Self-evolve mode requires --source and --output.")
            sys.exit(1)
        evolve_self(args.source, args.output)
    elif args.mode == "debug":
        run_dashboard()  # Start the Debugging Dashboard
    else:
        print("Unknown mode. Use --help for usage.")


if __name__ == "__main__":
    main()

#
# #!/usr/bin/env python3
# """
# Main entry point for Grüblergeist.
# Run in CLI mode, Web mode, or Evolve mode.
# """
#
# import argparse
# import logging
# import sys
# from typing import NoReturn
#
# from rich.logging import RichHandler
#
# from assistant.cli import run_cli
# from assistant.config import load_config
# from assistant.db import init_db
# from assistant.evolve import evolve_code, evolve_self
# from assistant.web import run_web
#
#
# def setup_logging() -> None:
#     """
#     Configure logging with Rich handler for color-coded output.
#     """
#     logging.basicConfig(
#         level=logging.INFO,
#         format="%(message)s",
#         datefmt="[%X]",
#         handlers=[RichHandler()],
#     )
#
#
# def main() -> None:
#     """
#     Parse CLI arguments, initialize database, and run Grüblergeist in the requested mode.
#     """
#     setup_logging()
#     load_config()
#     init_db()
#
#     parser = argparse.ArgumentParser(description="Grüblergeist Chat Assistant")
#     parser.add_argument(
#         "--mode",
#         choices=["cli", "web", "evolve", "evolve-self"],
#         default="cli",
#         help="Run in CLI mode, Web mode, code Evolve mode, or self Evolve mode.",
#     )
#     parser.add_argument("--source", help="Source file path for evolve.")
#     parser.add_argument("--output", help="Output file path for evolve.")
#     parser.add_argument(
#         "--instructions", help="Custom instructions for code evolution."
#     )
#     args = parser.parse_args()
#
#     if args.mode == "cli":
#         run_cli()
#     elif args.mode == "web":
#         run_web()
#     elif args.mode == "evolve":
#         if not args.source or not args.output:
#             print("Evolve mode requires --source and --output.")
#             sys.exit(1)
#         evolve_code(args.source, args.output, instructions=args.instructions)
#     elif args.mode == "evolve-self":
#         if not args.source or not args.output:
#             print("Self-evolve mode requires --source and --output.")
#             sys.exit(1)
#         evolve_self(args.source, args.output)
#     else:
#         print("Unknown mode. Use --help for usage.")
#
#
# if __name__ == "__main__":
#     main()
