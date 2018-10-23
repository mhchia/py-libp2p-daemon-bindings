p2pd_path = ${GOPATH}/src/github.com/libp2p/go-libp2p-daemon
p2pd_pb_path = $(p2pd_path)/pb
p2pd_pbs = $(shell find $(p2pd_pb_path) -name *.proto)

all: p2pd_pb_pys

p2pd_pb_pys: $(p2pd_pbs)
	protoc -I$(p2pd_pb_path) $(p2pd_pbs) --python_out=.

