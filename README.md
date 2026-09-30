# Dotfiles with Plugin System

This repository contains my personal dotfiles with a plugin-based configuration system that allows for easy separation of shared and environment-specific settings.

## Structure

```
.
├── install              # Main installation script
├── plugins/            # Plugin directory
│   ├── base/          # Base configurations (included in repo)
│   │   ├── bash/     # Bash configurations
│   │   ├── scripts/  # Utility scripts
│   │   └── ...
│   └── ...           # Other plugins (added as git submodules)
```

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/dotfiles.git ~/.dot_files
   cd ~/.dot_files
   ```

2. Run the install script:
   ```bash
   ./install
   ```

## Plugin System

### Base Plugin
The `base` plugin contains core configurations that are shared across all environments. This includes:
- Bash configurations
- Common aliases
- Utility scripts
- Prompt customization

#### Directory helpers

`cdr set_root [directory]` sets `PROJ_ROOT` (the current directory when it is
omitted); `cdr` returns to that root.

`paths` keeps a persistent active file of directories. Choose or create the
file with `paths set_file ~/my-paths`, then add or remove directories with
`paths add [directory ...]` and `paths del [directory ...]`. Paths are stored as
absolute paths, one per line. Run a command in each listed directory with, for
example, `paths run git status` or `paths run 'git status && git diff --stat'`.
Each directory is announced in purple before its command runs. In an installed
interactive shell, `paths` sources its standalone script so `run` uses the
current bash environment; it restores the original directory afterwards.

### Adding Custom Plugins
To add environment-specific configurations (e.g., work-specific settings):

1. Add the plugin as a git submodule:
   ```bash
   git submodule add <repository-url> plugins/my-custom-plugin
   ```

2. Run the install script again:
   ```bash
   ./install
   ```

### Plugin Structure
Each plugin can contain:
- Files ending in `.symlink` that will be automatically linked to your home directory
- An optional `install.sh` script for additional setup steps

### Creating a New Plugin
A plugin can be as simple as:
```
my-custom-plugin/
├── install.sh                  # Optional installation script
├── bashrc.symlink             # Will be linked as ~/.bashrc
└── custom-config.symlink      # Will be linked as ~/.custom-config
```

## License

MIT
