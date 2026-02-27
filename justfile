# Just commands for Minesploit development

_default:
    @just --list

# Run ruff linter
lint:
    uv run ruff check .

# Run mypy type checker
check:
    uv run mypy minesploit/

# Run tests via REPL script
test:
    uv run python -m minesploit.repl -s tests.ms

# Start the REPL
run:
    uv run python -m minesploit.repl

# Build binary release
dist:
    uv pip install -e ".[build]"
    uv run pyinstaller minesploit.spec
    @echo "Binary available at: dist/minesploit"