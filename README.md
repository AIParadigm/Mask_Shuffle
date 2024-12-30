# MASH: Large-Scale Privacy-Preserving Federated Learning based on Mask Shuffling

A Python implementation of the proposed federated learning framework.

## Introduction

1. First, we introduce a mask-shuffling scheme for mask seeds, leveraging ECIES and Paillier cryptosystems, to ensure that the sum of all masks equals $\textbf{0}$.
1. Second, we employ a group-based mask-shuffling scheme to improve client parallelism, thereby enhancing execution efficiency. Additionally, the group-based scheme enables the framework to tolerate client dropouts. 
1. Third, we utilize exponential operations to obfuscate clients' gradients while avoiding the need to solve the discrete logarithm problem when computing the aggregated gradient.
1. Fourth, we present a sampling-based verification method that ensures the correctness of the aggregation with high probability and incurs minimal computational overhead. The verification is accomplished on smart contract.


## Run the project

## Setup
### Usage
```asp
python setup_node.py <client_num>
```
- `<client_num>`: The number of clients (must be an integer).

### Example
Start a setup node for 10 clients:
```commandline
python setup_node.py 10
```

## Aggregator
### Usage
```asp
python aggregator.py <port> <ip address>
```
- `<port>`: The port on which the aggregator listens.
- `<ip address>`: The IP address of the setup node to fetch client information.

### Example
To start an aggregator instance listening on port `9475` and connecting to the setup node at `127.0.0.1`:
```commandline
python aggregator.py 9475 127.0.0.1
```
### Client
Once both the setup node and aggregator are running, you need to run the following script to start all the clients.
You can modify the values of `client_count` and `vectorsize` in the script to meet your experimental needs. However, please ensure that the `client_count` matches the number of clients set in the `setup_node` process that you have already started.

For windows:

You need to replace the virtual environment path in `start_clients.bat` with the path to your own virtual environment.

```shell
./start_clients.bat
```

For linux:

```bash
./start_clients.sh
```

