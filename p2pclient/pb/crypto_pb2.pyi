# @generated by generate_proto_mypy_stubs.py.  Do not edit!
import sys
from google.protobuf.descriptor import (
    EnumDescriptor as google___protobuf___descriptor___EnumDescriptor,
)

from google.protobuf.message import Message as google___protobuf___message___Message

from typing import List as typing___List, Tuple as typing___Tuple, cast as typing___cast

from typing.typing_extensions import Literal as typing_extensions___Literal

class KeyType(int):
    DESCRIPTOR: google___protobuf___descriptor___EnumDescriptor = ...
    @classmethod
    def Name(cls, number: int) -> str: ...
    @classmethod
    def Value(cls, name: str) -> KeyType: ...
    @classmethod
    def keys(cls) -> typing___List[str]: ...
    @classmethod
    def values(cls) -> typing___List[KeyType]: ...
    @classmethod
    def items(cls) -> typing___List[typing___Tuple[str, KeyType]]: ...

RSA = typing___cast(KeyType, 0)
Ed25519 = typing___cast(KeyType, 1)
Secp256k1 = typing___cast(KeyType, 2)
ECDSA = typing___cast(KeyType, 3)

class PublicKey(google___protobuf___message___Message):
    Type = ...  # type: KeyType
    Data = ...  # type: bytes
    def __init__(self, Type: KeyType = None, Data: bytes = None) -> None: ...
    @classmethod
    def FromString(cls, s: bytes) -> PublicKey: ...
    def MergeFrom(self, other_msg: google___protobuf___message___Message) -> None: ...
    def CopyFrom(self, other_msg: google___protobuf___message___Message) -> None: ...
    def HasField(
        self, field_name: typing_extensions___Literal[u"Data", u"Type"]
    ) -> bool: ...
    def ClearField(
        self, field_name: typing_extensions___Literal[u"Data", u"Type"]
    ) -> None: ...

class PrivateKey(google___protobuf___message___Message):
    Type = ...  # type: KeyType
    Data = ...  # type: bytes
    def __init__(self, Type: KeyType, Data: bytes) -> None: ...
    @classmethod
    def FromString(cls, s: bytes) -> PrivateKey: ...
    def MergeFrom(self, other_msg: google___protobuf___message___Message) -> None: ...
    def CopyFrom(self, other_msg: google___protobuf___message___Message) -> None: ...
    def HasField(
        self, field_name: typing_extensions___Literal[u"Data", u"Type"]
    ) -> bool: ...
    def ClearField(
        self, field_name: typing_extensions___Literal[u"Data", u"Type"]
    ) -> None: ...
