## Set the prompt
# Full major.minor (e.g. 9.4)
RELEASE=$(grep ^VERSION_ID= /etc/os-release | cut -d= -f2 | tr -d '"')

export PS1="[(Builder $RELEASE)\\u@\\h \\W]\\$ "

