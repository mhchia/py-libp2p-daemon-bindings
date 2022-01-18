#!/usr/bin/env python
# -*- coding: utf-8 -*-

import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()


extras_require = {
    "test": ["pytest>=4.6.3,<5.0.0", "pytest-cov>=2.7.1,<3.0.0"],
    "lint": [
        "mypy>=0.761,<1.0",
        "mypy-protobuf>=1.16",
        "black>=19.3b0",
        "isort>=4.3.21",
        "flake8>=3.7.7,<4.0.0",
    ],
    "dev": ["tox>=3.13.2,<4.0.0", "wheel"],
}

extras_require["dev"] = (
    extras_require["test"] + extras_require["lint"] + extras_require["dev"]
)


setuptools.setup(
    name="p2p_daemon_client",
    version="0.1.4",
    author="Kevin Mai-Hsuan Chia",
    author_email="kevin.mh.chia@gmail.com",
    description="The libp2p daemon bindings for Python",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/mhchia/py-libp2p-daemon-bindings",
    packages=setuptools.find_packages(exclude=["tests", "tests.*"]),
    install_requires=[
        "base58>=1.0.3",
        "multiaddr>=0.0.8,<0.1.0",
        "protobuf>=3.9.0",
        "pymultihash>=0.8.2",
        "anyio>=1.2.2,<2.0.0",
        "async-generator>=1.10,<2.0",
        "async-exit-stack>=1.0.1,<2.0.0",
    ],
    extras_require=extras_require,
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3 :: Only",
    ],
)
