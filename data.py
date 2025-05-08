from web3 import Web3

# Connect to Ganache
ganache_url = "http://127.0.0.1:7545"  # Update with your Ganache URL
web3 = Web3(Web3.HTTPProvider(ganache_url))

# Check connection
if web3.is_connected():
    print("Connected to Ganache")
else:
    print("Failed to connect to Ganache")

# Retrieve latest block number
# latest_block_number = web3.eth.block_number
# print("Latest block number:", latest_block_number)

# Retrieve block details
# latest_block = web3.eth.get_block(latest_block_number)
# print("Latest block details:", latest_block)

# Retrieve transaction details
# transactions = latest_block["transactions"]
# print("Transactions in the latest block:", transactions)

# Retrieve transaction receipt details
"""for tx_hash in transactions:
    tx_receipt = web3.eth.get_transaction_receipt(tx_hash)
    print("Transaction receipt for transaction", tx_hash, ":", tx_receipt)
"""
acc = {}
# Retrieve account balances
accounts = web3.eth.accounts
for account in accounts:
    balance = web3.eth.get_balance(account)
    acc[account] = float(web3.from_wei(balance, "ether"))
    # print("Balance of account", account, ":",
    #      web3.from_wei(balance, "ether"), "ETH")

balances = acc
# Sort the dictionary by balance in descending order
sorted_balances = sorted(balances.items(), key=lambda x: x[1], reverse=True)

# Get the top 3 balances
top_3_balances = sorted_balances[:3]

print("Top 3 balances:")
for address, balance in top_3_balances:
    print(f"Address: {address}, Balance: {balance}")
