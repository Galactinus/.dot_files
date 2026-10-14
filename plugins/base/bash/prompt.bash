# Set the Bash prompt (to be sourced by bashrc).

##############################################################################
# Color definitions
##############################################################################

# Regular colors
BLACK='\[\033[0;30m\]'
RED='\[\033[0;31m\]'
GREEN='\[\033[0;32m\]'
YELLOW='\[\033[0;33m\]'
BLUE='\[\033[0;34m\]'
MAGENTA='\[\033[0;35m\]'
CYAN='\[\033[0;36m\]'
WHITE='\[\033[0;37m\]'

# Bold colors
BOLD_BLACK='\[\033[01;30m\]'
BOLD_RED='\[\033[01;31m\]'
BOLD_GREEN='\[\033[01;32m\]'
BOLD_YELLOW='\[\033[01;33m\]'
BOLD_BLUE='\[\033[01;34m\]'
BOLD_MAGENTA='\[\033[01;35m\]'
BOLD_CYAN='\[\033[01;36m\]'
BOLD_WHITE='\[\033[01;37m\]'

# Reset color
RESET='\[\033[00m\]'

# Prompt colors (customize these to change prompt appearance)
TIME_COLOR="$BOLD_BLACK"
CHROOT_COLOR="$BOLD_MAGENTA"
HOST_COLOR="$GREEN"
DIR_COLOR="$BOLD_CYAN"
GIT_COLOR="$BOLD_MAGENTA"

# Source Git's bash completion and prompt support from our plugin
if [ -f "$DOTFILES_ROOT/plugins/base/git/git-completion.bash" ]; then
    source "$DOTFILES_ROOT/plugins/base/git/git-completion.bash"
fi

if [ -f "$DOTFILES_ROOT/plugins/base/git/git-prompt.bash" ]; then
    source "$DOTFILES_ROOT/plugins/base/git/git-prompt.bash"
fi

# set variable identifying the chroot you work in (used in the prompt below)
if [ -z "$debian_chroot" ] && [ -r /etc/debian_chroot ]; then
  debian_chroot=$(cat /etc/debian_chroot)
fi

##############################################################################
# Prompt component functions
##############################################################################

# Time component: [HH:MM:SS]
__prompt_time() {
    printf "[%s]" "$(date +%H:%M:%S)"
}

# Chroot component: (chroot-name) if in chroot
__prompt_chroot() {
    printf "%s" "${debian_chroot:+($debian_chroot)}"
}

# Host component: username@hostname
__prompt_host() {
    printf '%s@%s' "$USER" "${HOSTNAME%%.*}"
}

# Directory component: current directory name
__prompt_dir() {
    local dir="${PWD##*/}"
    printf '%s' "${dir:-/}"
}

# Git component: (branch-name hash)
__prompt_git() {
    printf "%s" "$(__git_ps1 "(%s $(git rev-parse --is-inside-work-tree >/dev/null 2>&1 && git log -1 --pretty=oneline | cut -c -7))")"
}

# Return the display width of plain prompt text. `wc -L` uses the active
# locale, so wide characters take the space they occupy in the terminal.
__prompt_visible_width() {
    printf '%s\n' "$1" | wc -L
}

# Cache the dynamic prompt data once before Bash displays each prompt. The same
# values are used for both rendering and deciding where to put its marker.
__prompt_update() {
    __prompt_time_value="$(__prompt_time)"
    __prompt_chroot_value="$(__prompt_chroot)"
    __prompt_host_value="$(__prompt_host)"
    __prompt_dir_value="$(__prompt_dir)"
    __prompt_git_value="$(__prompt_git)"

    __prompt_prefix_value="${__prompt_time_value} ${__prompt_chroot_value}${__prompt_host_value} ${__prompt_dir_value} ${__prompt_git_value}"
    __prompt_prefix_width="$(__prompt_visible_width "$__prompt_prefix_value")"
}

# Put the marker on its own line unless enough input space remains after the
# visible prompt prefix. COLUMNS is maintained by bash's `checkwinsize` option
# (enabled in bash_sym). DOTFILES_PROMPT_NARROW_COLUMNS controls the minimum
# remaining input width and defaults to 80 columns.
__prompt_marker() {
    local threshold="${DOTFILES_PROMPT_NARROW_COLUMNS:-80}"

    if [[ "$threshold" =~ ^[0-9]+$ && "${COLUMNS:-0}" =~ ^[0-9]+$ ]] \
        && (( COLUMNS - __prompt_prefix_width < threshold )); then
        printf '\n'
    fi

    if (( EUID == 0 )); then
        printf '# '
    else
        printf '$ '
    fi
}

##############################################################################
# Determine if color prompt will be used
##############################################################################

# set a fancy prompt (non-color, unless we know we "want" color)
case "$TERM" in
  xterm-color | xterm-256color) color_prompt=yes;;
esac

# uncomment for a colored prompt, if the terminal has the capability; turned
# off by default to not distract the user: the focus in a terminal window
# should be on the output of commands, not on the prompt
force_color_prompt=yes

if [ -n "$force_color_prompt" ]; then
  if [ -x /usr/bin/tput ] && tput setaf 1 >&/dev/null; then
    # We have color support; assume it's compliant with Ecma-48
    # (ISO/IEC-6429). (Lack of such support is extremely rare, and such
    # a case would tend to support setf rather than setaf.)
    color_prompt=yes
  else
    color_prompt=
  fi
fi

##############################################################################
# Set git prompt varibales
##############################################################################

#Shows staged changes (+), unstaged changes (*)
GIT_PS1_SHOWDIRTYSTATE=true

#Shows stashed changes ($)
GIT_PS1_SHOWSTASHSTATE=true

#Shows untracked files (%)
GIT_PS1_SHOWUNTRACKEDFILES=true

#Shows difference between HEAD and its upstream
#GIT_PS1_SHOWUPSTREAM=auto    # Shows behind (<), ahead (>), diverged (<>), (=)
GIT_PS1_SHOWUPSTREAM=verbose  # Also shows how many commit +/-

#Shows more info about identity of commit checked out in detached HEAD
#GIT_PS1_DESCRIBE_STYLE=contains    #relative to newer annotated tag
#GIT_PS1_DESCRIBE_STYLE=branch      #relative to newer tag or branch
#GIT_PS1_DESCRIBE_STYLE=describe    #relative to older annotated tag
GIT_PS1_DESCRIBE_STYLE=default     #exactly matching tag

#Shows a colored hint about the current dirty state
GIT_PS1_SHOWCOLORHINTS=true

##############################################################################
# Set the prompt
##############################################################################

# Show current branch in prompt if in git repo.
if [ "$color_prompt" = yes ]; then
  PS1='\[\033[01;30m\]${__prompt_time_value} \[\033[01;35m\]${__prompt_chroot_value}\[\033[32m\]${__prompt_host_value}\[\033[00m\] \[\033[0;34m\]${__prompt_dir_value} \[\033[01;35m\]${__prompt_git_value}\[\033[00m\]$(__prompt_marker)'
else
  PS1='${__prompt_time_value} ${__prompt_chroot_value}${__prompt_host_value} ${__prompt_dir_value} ${__prompt_git_value}$(__prompt_marker)'
fi

# Preserve an existing hook while ensuring our cached values are refreshed last.
PROMPT_COMMAND="${PROMPT_COMMAND:+${PROMPT_COMMAND}; }__prompt_update"

unset color_prompt force_color_prompt

##############################################################################
# Set the xterm title
##############################################################################

# If this is an xterm set the title to 'bash user@host: dir'
case "$TERM" in
  xterm*|rxvt*)
    PS1="\[\e]0;${debian_chroot:+($debian_chroot)}bash \u@\h: \w\a\]$PS1"
    ;;
esac

