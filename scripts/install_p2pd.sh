#!/bin/bash

set -euo pipefail

LIBP2P_DAEMON_VERSION=v0.2.0
PROJECT_NAME=go-libp2p-daemon
LIBP2P_DAEMON_REPO=github.com/libp2p/$PROJECT_NAME

go version
go env
git clone https://$LIBP2P_DAEMON_REPO
cd $PROJECT_NAME
git checkout $LIBP2P_DAEMON_VERSION
go get ./...
go install ./...
