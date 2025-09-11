#!/usr/bin/env bash
#
# Example plugin installation script

# Exit on error
set -e

# Get the plugin directory
PLUGIN_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "Installing example plugin..."

# Example: Create necessary directories
# mkdir -p "$HOME/.config/example"

# Example: Make scripts executable
chmod +x "$PLUGIN_DIR/scripts/"*

# Example: Add scripts to PATH by creating symlinks in ~/.local/bin
# mkdir -p "$HOME/.local/bin"
# for script in "$PLUGIN_DIR/scripts"/*; do
#     if [ -f "$script" ]; then
#         ln -sf "$script" "$HOME/.local/bin/$(basename "$script")"
#     fi
# done

# Example: Copy default configurations
# if [ ! -f "$HOME/.config/example/settings" ]; then
#     echo "# Example plugin settings" > "$HOME/.config/example/settings"
#     echo "# Customize these settings as needed" >> "$HOME/.config/example/settings"
# fi

echo "Example plugin installation complete!" 