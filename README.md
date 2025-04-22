# Mochi API Integration

A Python script to count Mochi flashcards and optionally post review data to Beeminder.

## Features

- Fetch all cards or cards from a specific deck
- Count cards by review status (due today, due tomorrow, etc.)
- Post review success metrics to Beeminder

## Setup

1. Install [uv](https://github.com/astral-sh/uv) if you haven't already:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. Create virtual environment and install dependencies:
   ```bash
   uv venv
   source .venv/bin/activate  # or `.venv/Scripts/activate` on Windows
   uv pip install -e .
   ```

3. Create your own version of the upload script:
   ```bash
   cp upload_mochi_data_to_beeminder.sh.example upload_mochi_data_to_beeminder.sh
   ```

4. Edit the script with your credentials:
   - Set environment variables for your API keys: `MOCHI_API_KEY` and `BEEMINDER_API_KEY`
   - Update username, goal, and other parameters

## Usage

```bash
python mochi_api.py --mochi-key YOUR_KEY [options]
```

Options:
- `--deck-id`: Specific deck ID to count (optional)
- `--beeminder`: Post to Beeminder
- `--beeminder-key`: Beeminder API key
- `--beeminder-user`: Beeminder username
- `--beeminder-goal`: Beeminder goal name
- `--minimum-cards`: Minimum cards for a successful review day (default: 10)

## Development

This project uses `uv` for dependency management and `ruff` for linting.

To run linting:
```bash
uv pip install ruff
ruff check .
```
