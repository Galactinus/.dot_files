# general
alias md='mkdir'
alias mdc='mkdirc'
alias rd='rmdir'

alias search='find -type f | xargs grep '
alias cd..='cd ..'
alias ..='cd ..'
alias ...='cd ../..'
alias ....='cd ../../..'
alias .....='cd ../../../..'
alias ......='cd ../../../../..'
alias .......='cd ../../../../../..'
alias ........='cd ../../../../../../..'
alias .........='cd ../../../../../../../..'
alias ..........='cd ../../../../../../../../..'
alias ...........='cd ../../../../../../../../../..'

alias ..2='cd ../..'
alias ..3='cd ../../..'
alias ..4='cd ../../../..'
alias ..5='cd ../../../../..'
alias ..6='cd ../../../../../..'
alias ..7='cd ../../../../../../..'
alias ..8='cd ../../../../../../../..'
alias ..9='cd ../../../../../../../../..'
alias ..10='cd ../../../../../../../../../..'

LS_OPTIONS="--color=auto -F" #remove
alias ll='ls --lA'

##grep
alias grep='grep --color=auto'
alias fgrep='fgrep --color=auto'
alias egrep='egrep --color=auto'

#ssh 
alias ssh='ssh -o StrictHostKeyChecking=no'

##git
alias gs='git status'
alias gb='git branch'
alias gl='git log --graph --decorate=auto --all'
alias gls='git log --graph --oneline'
alias make='time make'
