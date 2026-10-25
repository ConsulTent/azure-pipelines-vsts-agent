#!/bin/bash
set -e

export AGENT_ALLOW_RUNASROOT=1
export DEBIAN_FRONTEND=noninteractive

cleanup() {
  print_header "Caught $1..."
  exit 0
}

print_header() {
  # lightcyan='\033[1;36m'
  # nocolor='\033[0m'
  # echo -e "${lightcyan}$1${nocolor}"
  echo -e "$1"
}

trap_with_arg() {
    func="$1" ; shift
    for sig ; do
        trap "$func $sig" "$sig"
    done
}

GVER=`< /etc/git_version`

print_header "Using $GVER container."

trap_with_arg cleanup INT TERM EXIT


sleep 36000