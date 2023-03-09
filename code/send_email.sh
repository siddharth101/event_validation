#!/bin/bash
if [[ $# -lt 3 ]]
then
    echo "Wrapper script to send mail from unattended scripts"
    echo "Usage: $(basename $0) <email address> <subject> <message>"
    echo "NB: quote subject if it has spaces, message can have multiple lines"
else
    who=$1
    subj=$2
    msg=$3
    from=${USER}@ligo.org
    Mail -v  -s "${subj}" -r ${from} ${who} <<EOMSG
    ${msg}
EOMSG
fi
