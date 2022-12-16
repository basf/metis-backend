#!/usr/bin/env bash

set -em

if [[ ! -d "${HOME}/.ssh/" ]]; then
  # Create .ssh folder with an check that known_hosts file is present there
  mkdir --mode=0700 "${HOME}/.ssh/"
  touch "${HOME}/.ssh/known_hosts"

  # Generate ssh key that works with `paramiko`
  # See: https://aiida.readthedocs.io/projects/aiida-core/en/latest/get_started/computers.html#remote-computer-requirements
  ssh-keygen -f "${HOME}/.ssh/id_rsa" -t rsa -b 4096 -m PEM -N ''
fi

cp -f "${HOME}/.ssh/id_rsa.pub" /yanode-put-pubkey-here
