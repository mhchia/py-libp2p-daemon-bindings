#!/usr/bin/env python
# -*- coding: utf-8 -*-

import setuptools


with open("README.md", "r") as fh:
    long_description = fh.read()


deps = {
    "libp2p": [
        "base58>=1.0.3",
        "multiaddr>=0.0.8,<0.1.0",
        "protobuf>=3.6.1",
        "pymultihash>=0.8.2",
    ],
    "test": ["pytest", "pytest-asyncio", "pytest-cov"],
    "lint": ["flake8", "mypy", "black", "mypy-protobuf"],
    "dev": ["tox"],
}

deps["dev"] = deps["libp2p"] + deps["test"] + deps["lint"] + deps["dev"]

install_requires = deps["libp2p"]


setuptools.setup(
    name="p2pclient",
    version="0.0.1",
    author="Kevin Mai-Hsuan Chia",
    author_email="kevin.mh.chia@gmail.com",
    description="The libp2p daemon bindings for Python",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/mhchia/py-libp2p-daemon-bindings",
    packages=setuptools.find_packages(exclude=["tests", "tests.*"]),
    install_requires=install_requires,
    extras_require=deps,
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ],
)
