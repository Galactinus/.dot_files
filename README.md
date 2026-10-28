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

   On the first run, choose which enabled plugin supplies the Bash prompt. Use
   `./install --select-prompt` later to change that choice.

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

#### Command discovery and bulk renaming

The interactive Bash runners for the Python-based dotfiles commands require
Python 3.12 or newer. They try `python3.12`, then `python3`, `python3.14`, and
`python3.13`, accepting the first executable that meets the requirement. To select a specific
interpreter, set `DOTFILES_PYTHON` to its executable name or absolute path,
for example `export DOTFILES_PYTHON=/usr/bin/python3.12`. Put that export in
your shell configuration to keep it across sessions. An invalid or too-old
explicit selection reports an error instead of silently using another Python.
This setting only affects dotfiles commands that call the runner; it does not
change `PATH`, redefine `python3`, or select Python for other programs.
Reload Bash configuration after installation or changes. Directly executing a
script by its path bypasses the runner and uses its own `python3` shebang.

`dotcommands` lists callable commands, scripts, and functions from enabled plugins.
Add `-a` to include aliases; `-f` excludes functions and `-s` excludes scripts.
`-A` includes all categories, and `-t TYPE` also includes a plugin-defined type
and can be
repeated. `dotcommands --json` produces machine-readable output with the same
category filters. `-u` / `--include-unavailable` also shows unavailable entries
and disabled plugins, with reasons; combine it with `-A` to include all types.
Descriptions appear in an aligned column and may include newline characters.
Usage details appear beneath descriptions when available; use `--no-usage` to
hide them.
Interactive text output opens in `less` when available; JSON and redirected
output are not paged.
In an installed interactive Bash shell, a wrapper supplies the current aliases
and functions. A standalone invocation cannot inspect its parent shell, so it
reports shell entries as unavailable unless a plugin hook supplies their status.
Base aliases, public
shell functions and executable scripts are discovered automatically. Plugins
can publish a `commands.json` array, for example:

```json
[{"name": "my-tool", "type": "script", "description": "Describe the tool", "usage": "my-tool [option]"}]
```

Only `name` is required; the other fields are optional strings. Base manifest
entries add descriptions or override inferred details. Re-run `./install` after
changing plugin status to regenerate shell configuration.

For custom availability rules, a plugin may provide an executable
`commands-status` at its root. `dotcommands` calls it once per listed entry,
with the command name and manifest type as arguments, from the plugin directory.
Exit 0 means available, exit 1 means unavailable, and exit 3 delegates to the
standard shell/PATH check. The first stdout line may explain the status. Other
exit codes, execution errors, and timeouts (3 seconds) report an error and mark
the entry unavailable. A plugin disabled through `./install` is always marked
unavailable, and its hook is not run. This hook is executable plugin code and
inherits the current environment; it should only perform a quick, read-only
status check.

`renamer [path ...]` opens an interactive recursive file-renaming preview,
defaulting to the current directory. Paths may be files, directories or globs
(quote globs to have the command expand them). The filter is a Python regular
expression matched against relative paths, and the rename regex matches file
names. The replacement supports `$1`, `$2`, etc. for capture groups and `$$`
for a literal dollar sign. An empty replacement leaves filenames unchanged.
For example, filter `\.(cpp|h)$`, regex
`_(\w+)(\.[^.]+)$`, and replacement `_translator$2` change the text after
the final underscore while keeping the extension.

The preview shows filtered files even when their names are unchanged; the
change count includes only files that would actually be renamed.
In the regex fields, control characters are blue, escapes are purple, and
invalid or incomplete constructs are red. The error message gives details.
The rename regex's matching filename text is highlighted in the file list, and
capture groups share colors with their corresponding parts of that expression.
Nested groups take precedence, and group colors repeat after four groups.
Extension protection also excludes the extension from highlighting.
Group references in the replacement and their expanded text in the resulting
filename use the same colors as the corresponding capture groups.
In the resulting filename, unchanged text is green and changed text is blue;
capture-group colors take precedence. Literal text in the replacement field
is blue. The comparison aligns matching text between the old and new names.
When there is room beside the filenames, the right-hand panel shows capture
values for the match with the most populated groups. Repeated
parentheses remain one capture group, holding its last captured value.
Use Tab or Shift-Tab to select fields, Options, and Apply; press Space or Enter
to open Options or activate Apply. In Options, use Up/Down to select a setting,
Space to toggle it, and `q` to return. Arrow or Page Up/Down keys scroll the
preview; Ctrl-C or Escape quits. The options control hidden entries, symlinks,
traversal through directory symlinks, and protection of the final extension.
Hidden entries and symlinks are included by default;
directory symlinks are not followed unless enabled. Conflicts appear first in
red; applying offers the choice to go back or skip conflicting entries. If a
directory symlink and a file reached through it would both be renamed, the
symlink is treated as a conflict so its descendants remain accessible.
Toggle choices are saved immediately in `${XDG_STATE_HOME:-~/.local/state}/renamer/options.json`
and restored next time; the filter, regex, and replacement start empty.

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
- `bash/prompt.bash` to provide a selectable Bash prompt
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
