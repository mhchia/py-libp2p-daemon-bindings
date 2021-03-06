# @generated by generate_proto_mypy_stubs.py.  Do not edit!
import sys
from google.protobuf.descriptor import (
    Descriptor as google___protobuf___descriptor___Descriptor,
    EnumDescriptor as google___protobuf___descriptor___EnumDescriptor,
)

from google.protobuf.internal.containers import (
    RepeatedCompositeFieldContainer as google___protobuf___internal___containers___RepeatedCompositeFieldContainer,
    RepeatedScalarFieldContainer as google___protobuf___internal___containers___RepeatedScalarFieldContainer,
)

from google.protobuf.message import (
    Message as google___protobuf___message___Message,
)

from typing import (
    Iterable as typing___Iterable,
    List as typing___List,
    Optional as typing___Optional,
    Text as typing___Text,
    Tuple as typing___Tuple,
    cast as typing___cast,
)

from typing_extensions import (
    Literal as typing_extensions___Literal,
)


class Request(google___protobuf___message___Message):
    DESCRIPTOR: google___protobuf___descriptor___Descriptor = ...
    class Type(int):
        DESCRIPTOR: google___protobuf___descriptor___EnumDescriptor = ...
        @classmethod
        def Name(cls, number: int) -> str: ...
        @classmethod
        def Value(cls, name: str) -> Request.Type: ...
        @classmethod
        def keys(cls) -> typing___List[str]: ...
        @classmethod
        def values(cls) -> typing___List[Request.Type]: ...
        @classmethod
        def items(cls) -> typing___List[typing___Tuple[str, Request.Type]]: ...
        IDENTIFY = typing___cast(Request.Type, 0)
        CONNECT = typing___cast(Request.Type, 1)
        STREAM_OPEN = typing___cast(Request.Type, 2)
        STREAM_HANDLER = typing___cast(Request.Type, 3)
        DHT = typing___cast(Request.Type, 4)
        LIST_PEERS = typing___cast(Request.Type, 5)
        CONNMANAGER = typing___cast(Request.Type, 6)
        DISCONNECT = typing___cast(Request.Type, 7)
        PUBSUB = typing___cast(Request.Type, 8)
    IDENTIFY = typing___cast(Request.Type, 0)
    CONNECT = typing___cast(Request.Type, 1)
    STREAM_OPEN = typing___cast(Request.Type, 2)
    STREAM_HANDLER = typing___cast(Request.Type, 3)
    DHT = typing___cast(Request.Type, 4)
    LIST_PEERS = typing___cast(Request.Type, 5)
    CONNMANAGER = typing___cast(Request.Type, 6)
    DISCONNECT = typing___cast(Request.Type, 7)
    PUBSUB = typing___cast(Request.Type, 8)

    type = ... # type: Request.Type

    @property
    def connect(self) -> ConnectRequest: ...

    @property
    def streamOpen(self) -> StreamOpenRequest: ...

    @property
    def streamHandler(self) -> StreamHandlerRequest: ...

    @property
    def dht(self) -> DHTRequest: ...

    @property
    def connManager(self) -> ConnManagerRequest: ...

    @property
    def disconnect(self) -> DisconnectRequest: ...

    @property
    def pubsub(self) -> PSRequest: ...

    def __init__(self,
        *,
        type : Request.Type,
        connect : typing___Optional[ConnectRequest] = None,
        streamOpen : typing___Optional[StreamOpenRequest] = None,
        streamHandler : typing___Optional[StreamHandlerRequest] = None,
        dht : typing___Optional[DHTRequest] = None,
        connManager : typing___Optional[ConnManagerRequest] = None,
        disconnect : typing___Optional[DisconnectRequest] = None,
        pubsub : typing___Optional[PSRequest] = None,
        ) -> None: ...
    @classmethod
    def FromString(cls, s: bytes) -> Request: ...
    def MergeFrom(self, other_msg: google___protobuf___message___Message) -> None: ...
    def CopyFrom(self, other_msg: google___protobuf___message___Message) -> None: ...
    if sys.version_info >= (3,):
        def HasField(self, field_name: typing_extensions___Literal[u"connManager",u"connect",u"dht",u"disconnect",u"pubsub",u"streamHandler",u"streamOpen",u"type"]) -> bool: ...
        def ClearField(self, field_name: typing_extensions___Literal[u"connManager",u"connect",u"dht",u"disconnect",u"pubsub",u"streamHandler",u"streamOpen",u"type"]) -> None: ...
    else:
        def HasField(self, field_name: typing_extensions___Literal[u"connManager",b"connManager",u"connect",b"connect",u"dht",b"dht",u"disconnect",b"disconnect",u"pubsub",b"pubsub",u"streamHandler",b"streamHandler",u"streamOpen",b"streamOpen",u"type",b"type"]) -> bool: ...
        def ClearField(self, field_name: typing_extensions___Literal[u"connManager",b"connManager",u"connect",b"connect",u"dht",b"dht",u"disconnect",b"disconnect",u"pubsub",b"pubsub",u"streamHandler",b"streamHandler",u"streamOpen",b"streamOpen",u"type",b"type"]) -> None: ...

class Response(google___protobuf___message___Message):
    DESCRIPTOR: google___protobuf___descriptor___Descriptor = ...
    class Type(int):
        DESCRIPTOR: google___protobuf___descriptor___EnumDescriptor = ...
        @classmethod
        def Name(cls, number: int) -> str: ...
        @classmethod
        def Value(cls, name: str) -> Response.Type: ...
        @classmethod
        def keys(cls) -> typing___List[str]: ...
        @classmethod
        def values(cls) -> typing___List[Response.Type]: ...
        @classmethod
        def items(cls) -> typing___List[typing___Tuple[str, Response.Type]]: ...
        OK = typing___cast(Response.Type, 0)
        ERROR = typing___cast(Response.Type, 1)
    OK = typing___cast(Response.Type, 0)
    ERROR = typing___cast(Response.Type, 1)

    type = ... # type: Response.Type

    @property
    def error(self) -> ErrorResponse: ...

    @property
    def streamInfo(self) -> StreamInfo: ...

    @property
    def identify(self) -> IdentifyResponse: ...

    @property
    def dht(self) -> DHTResponse: ...

    @property
    def peers(self) -> google___protobuf___internal___containers___RepeatedCompositeFieldContainer[PeerInfo]: ...

    @property
    def pubsub(self) -> PSResponse: ...

    def __init__(self,
        *,
        type : Response.Type,
        error : typing___Optional[ErrorResponse] = None,
        streamInfo : typing___Optional[StreamInfo] = None,
        identify : typing___Optional[IdentifyResponse] = None,
        dht : typing___Optional[DHTResponse] = None,
        peers : typing___Optional[typing___Iterable[PeerInfo]] = None,
        pubsub : typing___Optional[PSResponse] = None,
        ) -> None: ...
    @classmethod
    def FromString(cls, s: bytes) -> Response: ...
    def MergeFrom(self, other_msg: google___protobuf___message___Message) -> None: ...
    def CopyFrom(self, other_msg: google___protobuf___message___Message) -> None: ...
    if sys.version_info >= (3,):
        def HasField(self, field_name: typing_extensions___Literal[u"dht",u"error",u"identify",u"pubsub",u"streamInfo",u"type"]) -> bool: ...
        def ClearField(self, field_name: typing_extensions___Literal[u"dht",u"error",u"identify",u"peers",u"pubsub",u"streamInfo",u"type"]) -> None: ...
    else:
        def HasField(self, field_name: typing_extensions___Literal[u"dht",b"dht",u"error",b"error",u"identify",b"identify",u"pubsub",b"pubsub",u"streamInfo",b"streamInfo",u"type",b"type"]) -> bool: ...
        def ClearField(self, field_name: typing_extensions___Literal[u"dht",b"dht",u"error",b"error",u"identify",b"identify",u"peers",b"peers",u"pubsub",b"pubsub",u"streamInfo",b"streamInfo",u"type",b"type"]) -> None: ...

class IdentifyResponse(google___protobuf___message___Message):
    DESCRIPTOR: google___protobuf___descriptor___Descriptor = ...
    id = ... # type: bytes
    addrs = ... # type: google___protobuf___internal___containers___RepeatedScalarFieldContainer[bytes]

    def __init__(self,
        *,
        id : bytes,
        addrs : typing___Optional[typing___Iterable[bytes]] = None,
        ) -> None: ...
    @classmethod
    def FromString(cls, s: bytes) -> IdentifyResponse: ...
    def MergeFrom(self, other_msg: google___protobuf___message___Message) -> None: ...
    def CopyFrom(self, other_msg: google___protobuf___message___Message) -> None: ...
    if sys.version_info >= (3,):
        def HasField(self, field_name: typing_extensions___Literal[u"id"]) -> bool: ...
        def ClearField(self, field_name: typing_extensions___Literal[u"addrs",u"id"]) -> None: ...
    else:
        def HasField(self, field_name: typing_extensions___Literal[u"id",b"id"]) -> bool: ...
        def ClearField(self, field_name: typing_extensions___Literal[u"addrs",b"addrs",u"id",b"id"]) -> None: ...

class ConnectRequest(google___protobuf___message___Message):
    DESCRIPTOR: google___protobuf___descriptor___Descriptor = ...
    peer = ... # type: bytes
    addrs = ... # type: google___protobuf___internal___containers___RepeatedScalarFieldContainer[bytes]
    timeout = ... # type: int

    def __init__(self,
        *,
        peer : bytes,
        addrs : typing___Optional[typing___Iterable[bytes]] = None,
        timeout : typing___Optional[int] = None,
        ) -> None: ...
    @classmethod
    def FromString(cls, s: bytes) -> ConnectRequest: ...
    def MergeFrom(self, other_msg: google___protobuf___message___Message) -> None: ...
    def CopyFrom(self, other_msg: google___protobuf___message___Message) -> None: ...
    if sys.version_info >= (3,):
        def HasField(self, field_name: typing_extensions___Literal[u"peer",u"timeout"]) -> bool: ...
        def ClearField(self, field_name: typing_extensions___Literal[u"addrs",u"peer",u"timeout"]) -> None: ...
    else:
        def HasField(self, field_name: typing_extensions___Literal[u"peer",b"peer",u"timeout",b"timeout"]) -> bool: ...
        def ClearField(self, field_name: typing_extensions___Literal[u"addrs",b"addrs",u"peer",b"peer",u"timeout",b"timeout"]) -> None: ...

class StreamOpenRequest(google___protobuf___message___Message):
    DESCRIPTOR: google___protobuf___descriptor___Descriptor = ...
    peer = ... # type: bytes
    proto = ... # type: google___protobuf___internal___containers___RepeatedScalarFieldContainer[typing___Text]
    timeout = ... # type: int

    def __init__(self,
        *,
        peer : bytes,
        proto : typing___Optional[typing___Iterable[typing___Text]] = None,
        timeout : typing___Optional[int] = None,
        ) -> None: ...
    @classmethod
    def FromString(cls, s: bytes) -> StreamOpenRequest: ...
    def MergeFrom(self, other_msg: google___protobuf___message___Message) -> None: ...
    def CopyFrom(self, other_msg: google___protobuf___message___Message) -> None: ...
    if sys.version_info >= (3,):
        def HasField(self, field_name: typing_extensions___Literal[u"peer",u"timeout"]) -> bool: ...
        def ClearField(self, field_name: typing_extensions___Literal[u"peer",u"proto",u"timeout"]) -> None: ...
    else:
        def HasField(self, field_name: typing_extensions___Literal[u"peer",b"peer",u"timeout",b"timeout"]) -> bool: ...
        def ClearField(self, field_name: typing_extensions___Literal[u"peer",b"peer",u"proto",b"proto",u"timeout",b"timeout"]) -> None: ...

class StreamHandlerRequest(google___protobuf___message___Message):
    DESCRIPTOR: google___protobuf___descriptor___Descriptor = ...
    addr = ... # type: bytes
    proto = ... # type: google___protobuf___internal___containers___RepeatedScalarFieldContainer[typing___Text]

    def __init__(self,
        *,
        addr : bytes,
        proto : typing___Optional[typing___Iterable[typing___Text]] = None,
        ) -> None: ...
    @classmethod
    def FromString(cls, s: bytes) -> StreamHandlerRequest: ...
    def MergeFrom(self, other_msg: google___protobuf___message___Message) -> None: ...
    def CopyFrom(self, other_msg: google___protobuf___message___Message) -> None: ...
    if sys.version_info >= (3,):
        def HasField(self, field_name: typing_extensions___Literal[u"addr"]) -> bool: ...
        def ClearField(self, field_name: typing_extensions___Literal[u"addr",u"proto"]) -> None: ...
    else:
        def HasField(self, field_name: typing_extensions___Literal[u"addr",b"addr"]) -> bool: ...
        def ClearField(self, field_name: typing_extensions___Literal[u"addr",b"addr",u"proto",b"proto"]) -> None: ...

class ErrorResponse(google___protobuf___message___Message):
    DESCRIPTOR: google___protobuf___descriptor___Descriptor = ...
    msg = ... # type: typing___Text

    def __init__(self,
        *,
        msg : typing___Text,
        ) -> None: ...
    @classmethod
    def FromString(cls, s: bytes) -> ErrorResponse: ...
    def MergeFrom(self, other_msg: google___protobuf___message___Message) -> None: ...
    def CopyFrom(self, other_msg: google___protobuf___message___Message) -> None: ...
    if sys.version_info >= (3,):
        def HasField(self, field_name: typing_extensions___Literal[u"msg"]) -> bool: ...
        def ClearField(self, field_name: typing_extensions___Literal[u"msg"]) -> None: ...
    else:
        def HasField(self, field_name: typing_extensions___Literal[u"msg",b"msg"]) -> bool: ...
        def ClearField(self, field_name: typing_extensions___Literal[u"msg",b"msg"]) -> None: ...

class StreamInfo(google___protobuf___message___Message):
    DESCRIPTOR: google___protobuf___descriptor___Descriptor = ...
    peer = ... # type: bytes
    addr = ... # type: bytes
    proto = ... # type: typing___Text

    def __init__(self,
        *,
        peer : bytes,
        addr : bytes,
        proto : typing___Text,
        ) -> None: ...
    @classmethod
    def FromString(cls, s: bytes) -> StreamInfo: ...
    def MergeFrom(self, other_msg: google___protobuf___message___Message) -> None: ...
    def CopyFrom(self, other_msg: google___protobuf___message___Message) -> None: ...
    if sys.version_info >= (3,):
        def HasField(self, field_name: typing_extensions___Literal[u"addr",u"peer",u"proto"]) -> bool: ...
        def ClearField(self, field_name: typing_extensions___Literal[u"addr",u"peer",u"proto"]) -> None: ...
    else:
        def HasField(self, field_name: typing_extensions___Literal[u"addr",b"addr",u"peer",b"peer",u"proto",b"proto"]) -> bool: ...
        def ClearField(self, field_name: typing_extensions___Literal[u"addr",b"addr",u"peer",b"peer",u"proto",b"proto"]) -> None: ...

class DHTRequest(google___protobuf___message___Message):
    DESCRIPTOR: google___protobuf___descriptor___Descriptor = ...
    class Type(int):
        DESCRIPTOR: google___protobuf___descriptor___EnumDescriptor = ...
        @classmethod
        def Name(cls, number: int) -> str: ...
        @classmethod
        def Value(cls, name: str) -> DHTRequest.Type: ...
        @classmethod
        def keys(cls) -> typing___List[str]: ...
        @classmethod
        def values(cls) -> typing___List[DHTRequest.Type]: ...
        @classmethod
        def items(cls) -> typing___List[typing___Tuple[str, DHTRequest.Type]]: ...
        FIND_PEER = typing___cast(DHTRequest.Type, 0)
        FIND_PEERS_CONNECTED_TO_PEER = typing___cast(DHTRequest.Type, 1)
        FIND_PROVIDERS = typing___cast(DHTRequest.Type, 2)
        GET_CLOSEST_PEERS = typing___cast(DHTRequest.Type, 3)
        GET_PUBLIC_KEY = typing___cast(DHTRequest.Type, 4)
        GET_VALUE = typing___cast(DHTRequest.Type, 5)
        SEARCH_VALUE = typing___cast(DHTRequest.Type, 6)
        PUT_VALUE = typing___cast(DHTRequest.Type, 7)
        PROVIDE = typing___cast(DHTRequest.Type, 8)
    FIND_PEER = typing___cast(DHTRequest.Type, 0)
    FIND_PEERS_CONNECTED_TO_PEER = typing___cast(DHTRequest.Type, 1)
    FIND_PROVIDERS = typing___cast(DHTRequest.Type, 2)
    GET_CLOSEST_PEERS = typing___cast(DHTRequest.Type, 3)
    GET_PUBLIC_KEY = typing___cast(DHTRequest.Type, 4)
    GET_VALUE = typing___cast(DHTRequest.Type, 5)
    SEARCH_VALUE = typing___cast(DHTRequest.Type, 6)
    PUT_VALUE = typing___cast(DHTRequest.Type, 7)
    PROVIDE = typing___cast(DHTRequest.Type, 8)

    type = ... # type: DHTRequest.Type
    peer = ... # type: bytes
    cid = ... # type: bytes
    key = ... # type: bytes
    value = ... # type: bytes
    count = ... # type: int
    timeout = ... # type: int

    def __init__(self,
        *,
        type : DHTRequest.Type,
        peer : typing___Optional[bytes] = None,
        cid : typing___Optional[bytes] = None,
        key : typing___Optional[bytes] = None,
        value : typing___Optional[bytes] = None,
        count : typing___Optional[int] = None,
        timeout : typing___Optional[int] = None,
        ) -> None: ...
    @classmethod
    def FromString(cls, s: bytes) -> DHTRequest: ...
    def MergeFrom(self, other_msg: google___protobuf___message___Message) -> None: ...
    def CopyFrom(self, other_msg: google___protobuf___message___Message) -> None: ...
    if sys.version_info >= (3,):
        def HasField(self, field_name: typing_extensions___Literal[u"cid",u"count",u"key",u"peer",u"timeout",u"type",u"value"]) -> bool: ...
        def ClearField(self, field_name: typing_extensions___Literal[u"cid",u"count",u"key",u"peer",u"timeout",u"type",u"value"]) -> None: ...
    else:
        def HasField(self, field_name: typing_extensions___Literal[u"cid",b"cid",u"count",b"count",u"key",b"key",u"peer",b"peer",u"timeout",b"timeout",u"type",b"type",u"value",b"value"]) -> bool: ...
        def ClearField(self, field_name: typing_extensions___Literal[u"cid",b"cid",u"count",b"count",u"key",b"key",u"peer",b"peer",u"timeout",b"timeout",u"type",b"type",u"value",b"value"]) -> None: ...

class DHTResponse(google___protobuf___message___Message):
    DESCRIPTOR: google___protobuf___descriptor___Descriptor = ...
    class Type(int):
        DESCRIPTOR: google___protobuf___descriptor___EnumDescriptor = ...
        @classmethod
        def Name(cls, number: int) -> str: ...
        @classmethod
        def Value(cls, name: str) -> DHTResponse.Type: ...
        @classmethod
        def keys(cls) -> typing___List[str]: ...
        @classmethod
        def values(cls) -> typing___List[DHTResponse.Type]: ...
        @classmethod
        def items(cls) -> typing___List[typing___Tuple[str, DHTResponse.Type]]: ...
        BEGIN = typing___cast(DHTResponse.Type, 0)
        VALUE = typing___cast(DHTResponse.Type, 1)
        END = typing___cast(DHTResponse.Type, 2)
    BEGIN = typing___cast(DHTResponse.Type, 0)
    VALUE = typing___cast(DHTResponse.Type, 1)
    END = typing___cast(DHTResponse.Type, 2)

    type = ... # type: DHTResponse.Type
    value = ... # type: bytes

    @property
    def peer(self) -> PeerInfo: ...

    def __init__(self,
        *,
        type : DHTResponse.Type,
        peer : typing___Optional[PeerInfo] = None,
        value : typing___Optional[bytes] = None,
        ) -> None: ...
    @classmethod
    def FromString(cls, s: bytes) -> DHTResponse: ...
    def MergeFrom(self, other_msg: google___protobuf___message___Message) -> None: ...
    def CopyFrom(self, other_msg: google___protobuf___message___Message) -> None: ...
    if sys.version_info >= (3,):
        def HasField(self, field_name: typing_extensions___Literal[u"peer",u"type",u"value"]) -> bool: ...
        def ClearField(self, field_name: typing_extensions___Literal[u"peer",u"type",u"value"]) -> None: ...
    else:
        def HasField(self, field_name: typing_extensions___Literal[u"peer",b"peer",u"type",b"type",u"value",b"value"]) -> bool: ...
        def ClearField(self, field_name: typing_extensions___Literal[u"peer",b"peer",u"type",b"type",u"value",b"value"]) -> None: ...

class PeerInfo(google___protobuf___message___Message):
    DESCRIPTOR: google___protobuf___descriptor___Descriptor = ...
    id = ... # type: bytes
    addrs = ... # type: google___protobuf___internal___containers___RepeatedScalarFieldContainer[bytes]

    def __init__(self,
        *,
        id : bytes,
        addrs : typing___Optional[typing___Iterable[bytes]] = None,
        ) -> None: ...
    @classmethod
    def FromString(cls, s: bytes) -> PeerInfo: ...
    def MergeFrom(self, other_msg: google___protobuf___message___Message) -> None: ...
    def CopyFrom(self, other_msg: google___protobuf___message___Message) -> None: ...
    if sys.version_info >= (3,):
        def HasField(self, field_name: typing_extensions___Literal[u"id"]) -> bool: ...
        def ClearField(self, field_name: typing_extensions___Literal[u"addrs",u"id"]) -> None: ...
    else:
        def HasField(self, field_name: typing_extensions___Literal[u"id",b"id"]) -> bool: ...
        def ClearField(self, field_name: typing_extensions___Literal[u"addrs",b"addrs",u"id",b"id"]) -> None: ...

class ConnManagerRequest(google___protobuf___message___Message):
    DESCRIPTOR: google___protobuf___descriptor___Descriptor = ...
    class Type(int):
        DESCRIPTOR: google___protobuf___descriptor___EnumDescriptor = ...
        @classmethod
        def Name(cls, number: int) -> str: ...
        @classmethod
        def Value(cls, name: str) -> ConnManagerRequest.Type: ...
        @classmethod
        def keys(cls) -> typing___List[str]: ...
        @classmethod
        def values(cls) -> typing___List[ConnManagerRequest.Type]: ...
        @classmethod
        def items(cls) -> typing___List[typing___Tuple[str, ConnManagerRequest.Type]]: ...
        TAG_PEER = typing___cast(ConnManagerRequest.Type, 0)
        UNTAG_PEER = typing___cast(ConnManagerRequest.Type, 1)
        TRIM = typing___cast(ConnManagerRequest.Type, 2)
    TAG_PEER = typing___cast(ConnManagerRequest.Type, 0)
    UNTAG_PEER = typing___cast(ConnManagerRequest.Type, 1)
    TRIM = typing___cast(ConnManagerRequest.Type, 2)

    type = ... # type: ConnManagerRequest.Type
    peer = ... # type: bytes
    tag = ... # type: typing___Text
    weight = ... # type: int

    def __init__(self,
        *,
        type : ConnManagerRequest.Type,
        peer : typing___Optional[bytes] = None,
        tag : typing___Optional[typing___Text] = None,
        weight : typing___Optional[int] = None,
        ) -> None: ...
    @classmethod
    def FromString(cls, s: bytes) -> ConnManagerRequest: ...
    def MergeFrom(self, other_msg: google___protobuf___message___Message) -> None: ...
    def CopyFrom(self, other_msg: google___protobuf___message___Message) -> None: ...
    if sys.version_info >= (3,):
        def HasField(self, field_name: typing_extensions___Literal[u"peer",u"tag",u"type",u"weight"]) -> bool: ...
        def ClearField(self, field_name: typing_extensions___Literal[u"peer",u"tag",u"type",u"weight"]) -> None: ...
    else:
        def HasField(self, field_name: typing_extensions___Literal[u"peer",b"peer",u"tag",b"tag",u"type",b"type",u"weight",b"weight"]) -> bool: ...
        def ClearField(self, field_name: typing_extensions___Literal[u"peer",b"peer",u"tag",b"tag",u"type",b"type",u"weight",b"weight"]) -> None: ...

class DisconnectRequest(google___protobuf___message___Message):
    DESCRIPTOR: google___protobuf___descriptor___Descriptor = ...
    peer = ... # type: bytes

    def __init__(self,
        *,
        peer : bytes,
        ) -> None: ...
    @classmethod
    def FromString(cls, s: bytes) -> DisconnectRequest: ...
    def MergeFrom(self, other_msg: google___protobuf___message___Message) -> None: ...
    def CopyFrom(self, other_msg: google___protobuf___message___Message) -> None: ...
    if sys.version_info >= (3,):
        def HasField(self, field_name: typing_extensions___Literal[u"peer"]) -> bool: ...
        def ClearField(self, field_name: typing_extensions___Literal[u"peer"]) -> None: ...
    else:
        def HasField(self, field_name: typing_extensions___Literal[u"peer",b"peer"]) -> bool: ...
        def ClearField(self, field_name: typing_extensions___Literal[u"peer",b"peer"]) -> None: ...

class PSRequest(google___protobuf___message___Message):
    DESCRIPTOR: google___protobuf___descriptor___Descriptor = ...
    class Type(int):
        DESCRIPTOR: google___protobuf___descriptor___EnumDescriptor = ...
        @classmethod
        def Name(cls, number: int) -> str: ...
        @classmethod
        def Value(cls, name: str) -> PSRequest.Type: ...
        @classmethod
        def keys(cls) -> typing___List[str]: ...
        @classmethod
        def values(cls) -> typing___List[PSRequest.Type]: ...
        @classmethod
        def items(cls) -> typing___List[typing___Tuple[str, PSRequest.Type]]: ...
        GET_TOPICS = typing___cast(PSRequest.Type, 0)
        LIST_PEERS = typing___cast(PSRequest.Type, 1)
        PUBLISH = typing___cast(PSRequest.Type, 2)
        SUBSCRIBE = typing___cast(PSRequest.Type, 3)
    GET_TOPICS = typing___cast(PSRequest.Type, 0)
    LIST_PEERS = typing___cast(PSRequest.Type, 1)
    PUBLISH = typing___cast(PSRequest.Type, 2)
    SUBSCRIBE = typing___cast(PSRequest.Type, 3)

    type = ... # type: PSRequest.Type
    topic = ... # type: typing___Text
    data = ... # type: bytes

    def __init__(self,
        *,
        type : PSRequest.Type,
        topic : typing___Optional[typing___Text] = None,
        data : typing___Optional[bytes] = None,
        ) -> None: ...
    @classmethod
    def FromString(cls, s: bytes) -> PSRequest: ...
    def MergeFrom(self, other_msg: google___protobuf___message___Message) -> None: ...
    def CopyFrom(self, other_msg: google___protobuf___message___Message) -> None: ...
    if sys.version_info >= (3,):
        def HasField(self, field_name: typing_extensions___Literal[u"data",u"topic",u"type"]) -> bool: ...
        def ClearField(self, field_name: typing_extensions___Literal[u"data",u"topic",u"type"]) -> None: ...
    else:
        def HasField(self, field_name: typing_extensions___Literal[u"data",b"data",u"topic",b"topic",u"type",b"type"]) -> bool: ...
        def ClearField(self, field_name: typing_extensions___Literal[u"data",b"data",u"topic",b"topic",u"type",b"type"]) -> None: ...

class PSMessage(google___protobuf___message___Message):
    DESCRIPTOR: google___protobuf___descriptor___Descriptor = ...
    from_id = ... # type: bytes
    data = ... # type: bytes
    seqno = ... # type: bytes
    topicIDs = ... # type: google___protobuf___internal___containers___RepeatedScalarFieldContainer[typing___Text]
    signature = ... # type: bytes
    key = ... # type: bytes

    def __init__(self,
        *,
        from_id : typing___Optional[bytes] = None,
        data : typing___Optional[bytes] = None,
        seqno : typing___Optional[bytes] = None,
        topicIDs : typing___Optional[typing___Iterable[typing___Text]] = None,
        signature : typing___Optional[bytes] = None,
        key : typing___Optional[bytes] = None,
        ) -> None: ...
    @classmethod
    def FromString(cls, s: bytes) -> PSMessage: ...
    def MergeFrom(self, other_msg: google___protobuf___message___Message) -> None: ...
    def CopyFrom(self, other_msg: google___protobuf___message___Message) -> None: ...
    if sys.version_info >= (3,):
        def HasField(self, field_name: typing_extensions___Literal[u"data",u"from_id",u"key",u"seqno",u"signature"]) -> bool: ...
        def ClearField(self, field_name: typing_extensions___Literal[u"data",u"from_id",u"key",u"seqno",u"signature",u"topicIDs"]) -> None: ...
    else:
        def HasField(self, field_name: typing_extensions___Literal[u"data",b"data",u"from_id",b"from_id",u"key",b"key",u"seqno",b"seqno",u"signature",b"signature"]) -> bool: ...
        def ClearField(self, field_name: typing_extensions___Literal[u"data",b"data",u"from_id",b"from_id",u"key",b"key",u"seqno",b"seqno",u"signature",b"signature",u"topicIDs",b"topicIDs"]) -> None: ...

class PSResponse(google___protobuf___message___Message):
    DESCRIPTOR: google___protobuf___descriptor___Descriptor = ...
    topics = ... # type: google___protobuf___internal___containers___RepeatedScalarFieldContainer[typing___Text]
    peerIDs = ... # type: google___protobuf___internal___containers___RepeatedScalarFieldContainer[bytes]

    def __init__(self,
        *,
        topics : typing___Optional[typing___Iterable[typing___Text]] = None,
        peerIDs : typing___Optional[typing___Iterable[bytes]] = None,
        ) -> None: ...
    @classmethod
    def FromString(cls, s: bytes) -> PSResponse: ...
    def MergeFrom(self, other_msg: google___protobuf___message___Message) -> None: ...
    def CopyFrom(self, other_msg: google___protobuf___message___Message) -> None: ...
    if sys.version_info >= (3,):
        def ClearField(self, field_name: typing_extensions___Literal[u"peerIDs",u"topics"]) -> None: ...
    else:
        def ClearField(self, field_name: typing_extensions___Literal[u"peerIDs",b"peerIDs",u"topics",b"topics"]) -> None: ...
