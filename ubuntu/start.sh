#!/bin/bash
set -e

export AGENT_ALLOW_RUNASROOT=1
export DEBIAN_FRONTEND=noninteractive

export VSO_AGENT_IGNORE=_,MAIL,OLDPWD,PATH,PWD,VSTS_AGENT,VSTS_ACCOUNT,VSTS_TOKEN_FILE,VSTS_TOKEN,VSTS_POOL,VSTS_WORK,VSO_AGENT_IGNORE
if [ -n "$VSTS_AGENT_IGNORE" ]; then
  export VSO_AGENT_IGNORE=$VSO_AGENT_IGNORE,VSTS_AGENT_IGNORE,$VSTS_AGENT_IGNORE
fi

if [ -z "$VSTS_ACCOUNT" ]; then
  echo 1>&2 error: missing VSTS_ACCOUNT environment variable
  exit 1
fi

if [ -z "$VSTS_TOKEN_FILE" ]; then
  if [ -z "$VSTS_TOKEN" ]; then
    echo 1>&2 error: missing VSTS_TOKEN environment variable
    exit 1
  fi
  VSTS_TOKEN_FILE=/vsts/.token
  echo -n $VSTS_TOKEN > "$VSTS_TOKEN_FILE"
fi
unset VSTS_TOKEN

if [ -n "$VSTS_AGENT" ]; then
  export VSTS_AGENT="$(eval echo $VSTS_AGENT)"
fi

if [ -n "$VSTS_WORK" ]; then
  export VSTS_WORK="$(eval echo $VSTS_WORK)"
  mkdir -p "$VSTS_WORK"
fi

print_header() {
  lightcyan='\033[1;36m'
  nocolor='\033[0m'
  echo -e "${lightcyan}$1${nocolor}"
}

trap_with_arg() {
    func="$1" ; shift
    for sig ; do
        trap "$func $sig" "$sig"
    done
}


web-server() {
  while true; do
    printf 'HTTP/1.1 302 Found\r\nLocation: https://'$VSTS_ACCOUNT'.visualstudio.com/_admin/_AgentPool\r\n\r\n' | nc -l -p 80 -q 0 > /dev/null
  done
}

cleanup() {
  print_header "Caught $1..."
  if [ -e /vsts/.configure ]; then
    print_header "Cleaning up."
    ./config.sh remove --unattended --auth pat --token $(cat "$VSTS_TOKEN_FILE")
    rm -f /vsts/.configure
  fi
}

configure() {
 print_header "Configuring VSTS agent..."
 touch /vsts/.configure
./config.sh --unattended \
  --url "https://$VSTS_ACCOUNT.visualstudio.com" \
  --auth pat --token $(cat "$VSTS_TOKEN_FILE") \
  --pool "${VSTS_POOL:-Default}" \
  --agent "${VSTS_AGENT:-$(hostname)}" \
  --work "${VSTS_WORK:-_work}" \
  --acceptTeeEula & wait $!
  print_header "Done configuring VSTS agent..."
}


if [ -e /vsts/agent -a ! -e /vsts/.configure ]; then
  print_header "Existing configuration detected.. continuing agent run."
  cd /vsts/agent
  ./run.sh & wait $!
  print_header "Exiting pre-existing agent run."
  exit $?
fi

rm -rf /vsts/agent
mkdir /vsts/agent
cd /vsts/agent

GVER=`< /etc/git_version`

print_header "Spinning up $GVER container."
print_header "Determining matching VSTS agent..."

VSTS_AGENT_RESPONSE=$(curl -LsS \
-u user:$(cat "$VSTS_TOKEN_FILE") \
  -H 'Accept:application/json;api-version=3.0' \
  "https://$VSTS_ACCOUNT.visualstudio.com/_apis/distributedtask/packages/agent?platform=linux-x64")

if echo "$VSTS_AGENT_RESPONSE" | jq . >/dev/null 2>&1; then
  VSTS_AGENT_URL=$(echo "$VSTS_AGENT_RESPONSE" \
    | jq -r '.value | map([.version.major,.version.minor,.version.patch,.downloadUrl]) | sort | .[length-1] | .[3]')
fi


if [ -z "$VSTS_AGENT_URL" -o "$VSTS_AGENT_URL" == "null" ]; then
  echo 1>&2 error: could not determine a matching VSTS agent - check that account \'$VSTS_ACCOUNT\' is correct and the token is valid for that account
  exit 1
fi


check_and_delete(){

print_header "Checking to make sure $VSTS_AGENT doesn't already exist in the pool in a bad state."

VSTS_AGENT_POOL_ID=$(curl -LsS \
-u user:$(cat "$VSTS_TOKEN_FILE") \
  -H 'Accept:application/json;api-version=3.0' \
"https://dev.azure.com/$VSTS_ACCOUNT/_apis/distributedtask/pools?api-version=5.1" \
 | jq -r ".value | .[] | select(.name==\"$VSTS_POOL\") | .id")


VSTS_AGENT_ID=$(curl -LsS \
-u user:$(cat "$VSTS_TOKEN_FILE") \
  -H 'Accept:application/json;api-version=3.0' \
"https://dev.azure.com/$VSTS_ACCOUNT/_apis/distributedtask/pools/$VSTS_AGENT_POOL_ID/agents?agentName=$VSTS_AGENT" \
| jq -r '.value | .[] | select(.status=="offline") | .id')

if [ -z "$VSTS_AGENT_ID" ]; then
print_header "Agent wasn't detected in a bad state."
else
print_header "Attempting to delete ${VSTS_AGENT}(${VSTS_AGENT_ID}) from ${VSTS_POOL}(${VSTS_AGENT_POOL_ID})"
DSTATUS=$(curl -LsS \
-u user:$(cat "$VSTS_TOKEN_FILE") \
 -X "DELETE" \
 "https://dev.azure.com/$VSTS_ACCOUNT/_apis/distributedtask/pools/$VSTS_AGENT_POOL_ID/agents/$VSTS_AGENT_ID?api-version=5.1")
print_header "Deleted (${DSTATUS})"
fi
}

print_header "Downloading and installing VSTS agent..."

curl -LsS $VSTS_AGENT_URL | tar -xz --no-same-owner & wait $!

print_header "Sourcing environment..."
source ./env.sh

print_header "Setting traps..."
trap_with_arg cleanup INT TERM

azout=`az version -o table`
print_header "Using internal AZ cli:"
print_header "$azout"

check_and_delete
configure

print_header "Running \"webserver\".."
web-server &
./run.sh & wait $!