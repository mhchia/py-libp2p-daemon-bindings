# py-libp2p-daemon-bindings

This is a fork of https://github.com/mhchia/py-libp2p-daemon-bindings targeting
with the new JavaScript libp2p daemon.
The Go daemon for which the original lib was created is now deprecated.
This is a work in progress, the first step is to make the lib compatible with the new
daemon and remove the dependency on py-libp2p as it is not maintained anymore either.

[![Build Status](https://circleci.com/gh/mhchia/py-libp2p-daemon-bindings/tree/master.svg?style=shield)](https://circleci.com/gh/mhchia/py-libp2p-daemon-bindings/tree/master)

> The [libp2p daemon](https://github.com/libp2p/js-libp2p-daemon) bindings for Python

Methods:
- [x] `Identify`
- [x] `Connect`
- [x] `StreamOpen`
- [x] `StreamHandler` - Register
- [x] `StreamHandler` - Inbound stream
- [x] DHT ops
- [x] Conn manager ops
- [x] PubSub ops
- [ ] Peer Storage
