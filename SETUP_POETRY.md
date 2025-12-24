# Automatic Poetry Activation Setup

This project is configured to automatically activate Poetry's virtual environment when you work in the project directory.

## Option 1: Using direnv (Recommended)

If you have `direnv` installed, the `.envrc` file will automatically activate Poetry when you `cd` into this directory.

### Install direnv (if not already installed):

**macOS (using Homebrew):**
```bash
brew install direnv
```

**Add to your `~/.zshrc`:**
```bash
eval "$(direnv hook zsh)"
```

Then reload your shell:
```bash
source ~/.zshrc
```

**Trust the `.envrc` file:**
```bash
cd ~/TT/qmaster
direnv allow
```

From now on, whenever you `cd` into the project directory, Poetry will be activated automatically.

## Option 2: Manual zsh Hook

If you don't want to use direnv, you can add this to your `~/.zshrc`:

```bash
# Auto-activate Poetry for qmaster project
_qmaster_poetry_activate() {
    local project_dir="$HOME/TT/qmaster"
    if [[ "$PWD" == "$project_dir"* ]] && [ -f "$project_dir/pyproject.toml" ]; then
        if [[ "$VIRTUAL_ENV" != "$project_dir/.venv" ]]; then
            if command -v poetry >/dev/null 2>&1; then
                poetry config virtualenvs.in-project true --local 2>/dev/null || true
                if [ -d "$project_dir/.venv" ]; then
                    source "$project_dir/.venv/bin/activate"
                fi
            fi
        fi
    fi
}

autoload -Uz add-zsh-hook
add-zsh-hook chpwd _qmaster_poetry_activate
_qmaster_poetry_activate  # Run on shell start
```

Then reload your shell:
```bash
source ~/.zshrc
```

## Option 3: VS Code/Cursor Integration

The `.vscode/settings.json` file is already configured to:
- Use the Poetry virtual environment (`${workspaceFolder}/.venv/bin/python`)
- Automatically activate the environment in integrated terminals

Simply open the project in VS Code/Cursor and open a new terminal - Poetry will be activated automatically.

## Verify Installation

After setup, verify Poetry is activated:

```bash
cd ~/TT/qmaster
which python  # Should point to .venv/bin/python
poetry env info  # Should show the virtual environment path
```

## Troubleshooting

### If Poetry environment is not activated:

1. **Ensure Poetry is installed:**
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```

2. **Configure Poetry to create venv in project:**
   ```bash
   poetry config virtualenvs.in-project true --local
   ```

3. **Install dependencies (if venv doesn't exist):**
   ```bash
   poetry install
   ```

4. **Manually activate (if needed):**
   ```bash
   source .venv/bin/activate
   ```
