#!/usr/bin/env python
# -*- coding: utf-8 -*-

from distutils.core import setup


setup(
    name="p2pclient",
    version="0.0.1",
    packages=["p2pclient"],
    install_requires=[
        "base58",
        "multiaddr",
        "protobuf",
    ],
)
