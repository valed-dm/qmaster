#!/bin/bash
# Poetry auto-activation script for zsh
# This script can be sourced in your .zshrc or run manually

_qmaster_poetry_activate() {
    local project_dir="$HOME/TT/qmaster"
    
    # Only activate if we're in the project directory or a subdirectory
    if [[ "$PWD" == "$project_dir"* ]] && [ -f "$project_dir/pyproject.toml" ]; then
        # Check if already activated
        if [[ "$VIRTUAL_ENV" == "$project_dir/.venv" ]]; then
            return 0
        fi
        
        # Ensure Poetry is configured for in-project venv
        if command -v poetry >/dev/null 2>&1; then
            poetry config virtualenvs.in-project true --local 2>/dev/null || true
            
            # Activate if venv exists
            if [ -d "$project_dir/.venv" ]; then
                source "$project_dir/.venv/bin/activate"
            fi
        fi
    fi
}

# For zsh: use precmd hook to auto-activate
if [ -n "$ZSH_VERSION" ]; then
    autoload -Uz add-zsh-hook
    add-zsh-hook chpwd _qmaster_poetry_activate
    # Also run it when the shell starts
    _qmaster_poetry_activate
fi

# For bash: use PROMPT_COMMAND
if [ -n "$BASH_VERSION" ]; then
    PROMPT_COMMAND="_qmaster_poetry_activate; $PROMPT_COMMAND"
fi

