# py-libp2p-daemon-bindings

[![Unit tests](https://github.com/mhchia/py-libp2p-daemon-bindings/actions/workflows/unit-tests.yml/badge.svg)](https://github.com/mhchia/py-libp2p-daemon-bindings/actions/workflows/unit-tests.yml)

> The [libp2p daemon](https://github.com/libp2p/go-libp2p-daemon) bindings for Python

Provides a client library to interact with the official libp2p daemons.
Supports the [Go](https://github.com/libp2p/go-libp2p-daemon) and [JavaScript](https://github.com/libp2p/js-libp2p-daemon) daemons.

Features:
- The `Client` class enables communication with a P2P daemon using its protobuf control protocol.
- The `Daemon` class allows to spawn a P2P daemon from Python code. This is especially useful for testing.

Tested with the Go daemon v0.2.0 and the JS daemon v0.10.2.

## Supported features (Go daemon)

- [x] `Identify`
- [x] `Connect`
- [x] `StreamOpen`
- [x] `StreamHandler` - Register
- [x] `StreamHandler` - Inbound stream
- [x] DHT ops
- [x] Conn manager ops
- [x] PubSub ops

## Supported features (JS daemon)
- [x] `Identify`
- [x] `Connect`
- [x] `StreamOpen`
- [x] `StreamHandler` - Register
- [x] `StreamHandler` - Inbound stream
- [ ] DHT ops / most functionalities are bugged and some are not implemented
- [ ] Conn manager ops
- [x] PubSub ops
- [ ] PeerStore
