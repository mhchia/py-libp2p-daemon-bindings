#!/bin/bash
# Installs nodejs and jsp2pd on the system.

set -e

NODE_VERSION=v16.13.2
NODE_ARCHIVE=node-${NODE_VERSION}-linux-x64.tar.xz
JSP2PD_VERSION=0.10.1

# Check the currently installed version, if any
INSTALLED_VERSION=""
if command -v jsp2pd &> /dev/null
then
  INSTALLED_VERSION=$(jsp2pd --version)
fi

if [ -z "${INSTALLED_VERSION}" ] || [ "${INSTALLED_VERSION}" != "${JSP2PD_VERSION}" ]; then
  if ! command -v node &> /dev/null
  then
    # Install node
    echo "installing nodejs ${NODE_VERSION}..."
    wget https://nodejs.org/dist/${NODE_VERSION}/${NODE_ARCHIVE}
    sudo mkdir -p /usr/local/lib/nodejs
    sudo tar -xJvf node-${NODE_VERSION}-linux_x64.tar.xz -C /usr/local/lib/nodejs
    export PATH="${PATH}:/usr/local/lib/nodejs/node-${NODE_VERSION}-linux-x64/bin"

    echo "nodejs installed."
  else
    echo "nodejs is already installed."
  fi

  echo "installing jsp2pd ${JSP2PD_VERSION}..."
  npm install --global libp2p-daemon@"${JSP2PD_VERSION}"
  echo "jsp2pd installed."
fi
