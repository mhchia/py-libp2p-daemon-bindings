#!/bin/bash

LIBP2P_DAEMON_VERSION=v0.2.0
GOPACKAGE=go1.12.6.linux-amd64.tar.gz
PROJECT_NAME=go-libp2p-daemon
LIBP2P_DAEMON_REPO=github.com/libp2p/$PROJECT_NAME

P2PD_DIR=$HOME/.p2pd/$LIBP2P_DAEMON_VERSION
P2PD_BINARY=$P2PD_DIR/p2pd
if [ ! -e "$P2PD_BINARY" ]; then
    wget https://dl.google.com/go/$GOPACKAGE
    sudo tar -C /usr/local -xzf $GOPACKAGE
    export GOPATH=$HOME/go
    export GOROOT=/usr/local/go
    export PATH=$GOROOT/bin:$GOPATH/bin:$PATH
    go version
    git clone https://$LIBP2P_DAEMON_REPO
    cd $PROJECT_NAME
    git checkout $LIBP2P_DAEMON_VERSION
    go get ./...
    go install ./...
    mkdir -p $P2PD_DIR
    cp `which p2pd` $P2PD_BINARY
fi
sudo ln -s $P2PD_BINARY /usr/local/bin/p2pd
