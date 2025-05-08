from solcx import compile_standard, install_solc
from web3 import Web3
from azure.storage.blob import *
config = {"azure_storage_connectionstring": "DefaultEndpointsProtocol=https;AccountName=mypdf;AccountKey=go/Q2RmG8nB8zFVKPDisxsTE7WWX6NqZEt43FhrsSngnc3olLGeFHJxLYFJD/SksJIOE20kQUZfK+AStLpjjPw==;EndpointSuffix=core.windows.net",
          "videos_container_name": "check", "source_folder": "static/upload"}
# Connect to Hardhat JSON-RPC
web3 = Web3(Web3.HTTPProvider('http://localhost:8545'))
print(web3.is_connected())


def soliditycontract():
    import json
    install_solc("0.6.0")
    with open("./SimpleStorage.sol", "r") as file:
        simple_storage_file = file.read()

    compiled_sol = compile_standard(
        {
            "language": "Solidity",
            "sources": {"SimpleStorage.sol": {"content": simple_storage_file}},
            "settings": {
                "outputSelection": {
                    "*": {
                        "*": ["abi", "metadata", "evm.bytecode", "evm.bytecode.sourceMap"]
                    }
                }
            },
        },
        solc_version="0.6.0",
    )

    with open("compiled_code.json", "w") as file:
        json.dump(compiled_sol, file)

    bytecode = compiled_sol["contracts"]["SimpleStorage.sol"]["SimpleStorage"]["evm"][
        "bytecode"
    ]["object"]
    # get abi
    abi = json.loads(
        compiled_sol["contracts"]["SimpleStorage.sol"]["SimpleStorage"]["metadata"]
    )["output"]["abi"]

    w3 = Web3(Web3.HTTPProvider('http://localhost:8545'))
    chain_id = 31337
    print(w3.is_connected())
    my_address = "0x8626f6940E2eb28930eFb4CeF49B2d1F2C9C1199"
    private_key = "0xdf57089febbacf7ba0bc227dafbffa9fc08a93fdc68e1e42411a14efcf23656e"
    # initialize contract
    SimpleStorage = w3.eth.contract(abi=abi, bytecode=bytecode)
    nonce = w3.eth.get_transaction_count(my_address)
    # set up transaction from constructor which executes when firstly
    transaction = SimpleStorage.constructor().build_transaction(
        {"chainId": chain_id, "from": my_address, "nonce": nonce}
    )
    signed_tx = w3.eth.account.sign_transaction(
        transaction, private_key=private_key)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    tx_receipt = "".join(["{:02X}".format(b)
                         for b in tx_receipt["transactionHash"]])
    return tx_receipt


print(soliditycontract())
