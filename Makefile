p2pd_pb_path = p2pclient/pb
p2pd_pbs = $(shell find $(p2pd_pb_path) -name *.proto)
pys = $(p2pd_pbs:.proto=_pb2.py)
pyis = $(p2pd_pbs:.proto=_pb2.pyi)

# Set default to `protobufs`, otherwise `format` is called when typing only `make`
all: protobufs

format:
	black p2pclient/ tests/ setup.py
	isort --recursive p2pclient tests setup.py

lint:
	black --check p2pclient/ tests/ setup.py
	isort --recursive --check-only p2pclient tests setup.py
	flake8 p2pclient/ tests/ setup.py
	mypy -p p2pclient --config-file mypy.ini

protobufs: $(pys)

%_pb2.py: %.proto
	protoc --python_out=. --mypy_out=. $<

.PHONY: clean

clean:
	rm $(pys) $(pyis)

