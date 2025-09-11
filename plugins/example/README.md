# Example Plugin

This is an example plugin demonstrating the standard structure and common customizations.

## Structure

```
plugins/example/
├── README.md               # This file
├── install.sh             # Plugin-specific installation script
├── bash/
│   ├── alias.bash         # Plugin-specific aliases
│   └── bashrc.symlink     # Main bash configurations
├── scripts/
│   └── example-tool       # Utility scripts
└── config/                # Additional configuration files
```

## Features

- Bash environment customizations
- Custom aliases
- Utility scripts
- Configuration management

## Installation

The plugin will be automatically installed when you run the main dotfiles install script.
The installation will:

1. Create necessary directories
2. Set up environment variables
3. Install utility scripts
4. Create default configurations

## Configuration

Edit `~/.config/example/settings` to customize the plugin settings.

## Usage

After installation, you'll have access to:

- New environment variables (EXAMPLE_PATH, EXAMPLE_CONFIG)
- New aliases (ex, exc, cdex, cdexc)
- New commands (example-tool)

## Adding Custom Configuration

To add your own configurations:

1. Edit the appropriate files in the bash directory
2. Add new scripts to the scripts directory
3. Add new configuration files to the config directory 