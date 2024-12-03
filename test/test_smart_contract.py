from web3 import Web3
import sys
import numpy as np
w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:7545'))
from solcx import compile_standard, install_solc
install_solc("0.8.0")
import json  # to save the output in a JSON file
import gmpy2

with open("Contracts/Test_Smart_Contract.sol", "r") as file:
    contact_list_file = file.read()

compiled_sol = compile_standard(
    {
        "language": "Solidity",
        "sources": {"Test_Smart_Contract.sol": {"content": contact_list_file}},
        "settings": {
            "outputSelection": {
                "*": {
                    "*": ["abi", "metadata", "evm.bytecode", "evm.bytecode.sourceMap"]
                    # output needed to interact with and deploy contract
                }
            }
        },
    },
    solc_version="0.8.0",
)

# print(compiled_sol)
with open("compiled_code.json", "w") as file:
    json.dump(compiled_sol, file)
# get bytecode
bytecode = compiled_sol["contracts"]["Test_Smart_Contract.sol"]["Test_Smart_Contract"]["evm"]["bytecode"]["object"]
# get abi
abi = json.loads(compiled_sol["contracts"]["Test_Smart_Contract.sol"]["Test_Smart_Contract"]["metadata"])["output"]["abi"]
# Create the contract in Python
contract = w3.eth.contract(abi=abi, bytecode=bytecode)

chain_id = 5777
accounts0 = w3.eth.accounts[0]
transaction_hash = contract.constructor().transact({'from': accounts0})
# Wait for the contract to be deployed
transaction_receipt = w3.eth.wait_for_transaction_receipt(transaction_hash)
# Get the deployed contract address
contract_address = transaction_receipt['contractAddress']

Contract = w3.eth.contract(address=contract_address, abi=abi)

def gen_grad(size):
    gradients = np.round(np.random.random(size), 4)
    scale_factor = 1e4
    scaled_gradients = gradients * scale_factor
    grad = scaled_gradients.astype(np.int32)

    return grad


# Test multiple candidates
# python test_smart_contract.py <num of clients> <size of grad>
if __name__ == '__main__':

    n = int(sys.argv[1])
    vector_size = int(sys.argv[2])
    batch_size = int(vector_size/2)

    P = 1208925819614629174706189
    g1 = 71268528852831316311076975079190540529007687924137045429198239221085821340320
    g2 = 107444586961954676114358403768738618907097969765753511016337400927285324288018
    g = [g1, g2]
    grads = []
    grads_sum = []

    for i in range(n):
        grads.append(gen_grad(vector_size))
        grads_sum.append([np.sum(grads[i][:batch_size]), np.sum(grads[i][batch_size:])])
    print(f"generate grad complete")
    sum_grad = np.sum(grads, axis=0)
    client_commit = []
    for s in grads_sum:
        c_s1 = gmpy2.powmod(gmpy2.mpz(g1), gmpy2.mpz(s[0]), P)
        c_s2 = gmpy2.powmod(gmpy2.mpz(g2), gmpy2.mpz(s[1]), P)
        client_commit.append([c_s1, c_s2])
    print("commit compute complete")
    sum1 = int(np.sum(sum_grad[:batch_size]))
    sum2 = int(np.sum(sum_grad[batch_size:]))
    sumtosc_cost = Contract.functions.SumtoSC(sum1, sum2).estimate_gas({'from': w3.eth.accounts[0]})
    print(f"the sum of aggregated grad had been uploaded to smart contract, gas cost: {sumtosc_cost}")
    # gradtosc_cost = Contract.functions.GradtoSC(sum_grad.tolist()).estimate_gas({'from': w3.eth.accounts[0]})
    # print(f"the aggregated grad had been uploaded to smart contract, gas cost:{gradtosc_cost}")
    committosc_cost = []
    for c in client_commit:
        c_list = [int(c[0]), int(c[1])]
        committosc_cost.append(Contract.functions.CommittoSC(c_list).estimate_gas({'from': w3.eth.accounts[0]}))
    print(f"the commitment had been uploaded to smart contract, gas cost:{committosc_cost}")
    verify_cost = Contract.functions.verifyCommitment().estimate_gas({'from': w3.eth.accounts[0]})
    print(f"the gas cost of verification：{verify_cost}")
