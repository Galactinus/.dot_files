#!/usr/bin/env bash
# Shared interpreter selection for dotfiles Python commands.
_dotfiles_python_run() {
    local script="$1" candidate
    shift
    if [[ -n "${DOTFILES_PYTHON:-}" ]]; then
        if ! "$DOTFILES_PYTHON" -c 'import sys; sys.exit(sys.version_info < (3, 12))' >/dev/null 2>&1; then
            printf '%s: DOTFILES_PYTHON is not an executable Python 3.12 or newer: %s\n' "${script##*/}" "$DOTFILES_PYTHON" >&2
            return 1
        fi
        "$DOTFILES_PYTHON" "$script" "$@"
        return $?
    fi
    for candidate in python3.12 python3 python3.14 python3.13; do
        if command -v "$candidate" >/dev/null 2>&1 && \
           "$candidate" -c 'import sys; sys.exit(sys.version_info < (3, 12))' >/dev/null 2>&1; then
            "$candidate" "$script" "$@"
            return $?
        fi
    done
    printf '%s: Python 3.12 or newer is required; set DOTFILES_PYTHON to its executable\n' "${script##*/}" >&2
    return 1
}
