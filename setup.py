#!/usr/bin/env python
# -*- coding: utf-8 -*-

import setuptools


with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="p2pclient",
    version="0.0.1",
    author="Kevin Mai-Hsuan Chia",
    author_email="kevin.mh.chia@gmail.com",
    description="The libp2p daemon bindings for Python",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/mhchia/py-libp2p-daemon-bindings",
    packages=setuptools.find_packages(),
    install_requires=[
        "base58",
        "py-multiaddr",  # use the forked one temporarily
        "protobuf",
    ],
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        'Programming Language :: Python :: 3.6',
    ],
)
