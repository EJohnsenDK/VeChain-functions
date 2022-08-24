#This python script lets you connect to a VeChain node, either on mainnet or testnet, choose a wallet address, and get it's holdings of different coins listed

#First we need to install the VeChain Thor request library: https://pypi.org/project/thor-requests/0.1.2/
pip3 install -U thor-requests

#Some imports:
from thor_requests.wallet import Wallet
from thor_requests.connect import Connect
from thor_requests.contract import Contract
import requests

#Loading the interface:
ERC20_CONTRACT = Contract.fromFile("./VTHO.json")
print(ERC20_CONTRACT)

#Selecting the environment - "M" for MAIN, "T" for TEST - connecting to it, and getting the associated token list:
ENV = "T"

# Config
if ENV == "T":
  NODE_URL     = "https://sync-testnet.vechain.org" # node connection
  TOKEN_LIST   = 'https://vechain.github.io/token-registry/test.json' # main net is main.json

if ENV == "M":
  NODE_URL     = "https://sync-mainnet.veblocks.net/" # node connection
  TOKEN_LIST   = 'https://vechain.github.io/token-registry/main.json' # main net is main.json

CONNECTOR      = Connect(NODE_URL)

# Gather tokens list
r = requests.get(TOKEN_LIST)
assert r.status_code == 200
tokens = r.json()

WALLET_ADD = "0x2e6a0c62629A7f86606A0F68252E52791696Fae7"

#VET being native coin has its' own function
VET_hold = CONNECTOR.get_vet_balance(WALLET_ADD)
print('VET: ', int(VET_hold)/10**18)

# Choose wallet address and print token balances:
#balance_clauses = [ CONNECTOR.clause(ERC20_CONTRACT, 'balanceOf', [SRC_WALLET.getAddress()], token['address']) for token in tokens]
#results = CONNECTOR.call_multi(SRC_WALLET.getAddress(), balance_clauses)
balance_clauses = [ CONNECTOR.clause(ERC20_CONTRACT, 'balanceOf', [WALLET_ADD], token['address']) for token in tokens]
results = CONNECTOR.call_multi(WALLET_ADD, balance_clauses)
assert len(results) == len(tokens)
balances = [int(x['decoded']['0']) for x in results]
for token, balance in zip(tokens, balances):
  #if (token["symbol"] == "JUR") or (token["symbol"] == "VTHO"):
    print(f'{token["symbol"]}: {int(balance)/10**18}')
