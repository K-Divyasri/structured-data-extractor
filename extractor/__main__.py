"""Makes `python -m extractor ...` work by delegating to the CLI."""

from .cli import main

if __name__ == "__main__":
    raise SystemExit(main())
