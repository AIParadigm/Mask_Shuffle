# MASH: Large-Scale Privacy-Preserving Federated Learning based on Mask Shuffling

A simple Python implementation of a privacy-preserving aggregation protocol for federated learning.

## Introduction

This project is an implementation of Mask shuffling FL for Large-Scale Privacy-Preserving Federated Learning based on Mask Shuffling


## Run the project

### Setup 

To initialize initial system parameters, use the following command:
```commandline
python setup_node.py 100
```
You can change the number of clients according to your needs.


### Aggregator

The client is a simple python script to interact with the server.
```commandline
python aggregator.py 1234 127.0.0.1
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

