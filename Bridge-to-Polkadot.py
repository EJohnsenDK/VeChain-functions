#This program simulates first part of a token bridge from VeChain to Polkadot, by sending VET from one wallet to another. 
#Sending wallet is a token holder's wallet
#Receiving wallet is VeChain part of a 'smart contract' that together with other functions bridges the tokens to a Polkadot version, 
#with information about which wallet on Polkadot that has to receive the bridged tokens.

#Creates a couple of VeChain wallets and send tokens from one to the other: 

#First we need to install the VeChain Thor request library: https://pypi.org/project/thor-requests/0.1.2/
pip3 install -U thor-requests

#Some imports:
from thor_requests.wallet import Wallet
from thor_requests.connect import Connect
from thor_requests.contract import Contract
from thor_devkit import cry
from thor_devkit.cry import mnemonic
from thor_devkit.cry import hdnode
import requests
import binascii

#---------------------------------------------------------------------------------------------------------
#Creating token holder's wallet from which tokens will be sent towards the 'token bridge'
#---------------------------------------------------------------------------------------------------------

# Generate random mnemonic words or reuse some already generated - DO NOT USE ON MAINNET!
words_th = ['trick', 'follow', 'resource', 'bind', 'fabric', 'ancient', 'tragic', 'weird', 'limit', 'soft', 'cousin', 'husband']
#words_th = mnemonic.generate()

# Construct HD node from words. 
hd_node_th = cry.HDNode.from_mnemonic(words_th)
# Get address and privatekey from words_th
for i in range(0, 1):
   address_th='0x'+hd_node_th.derive(i).address().hex()
   privkey_th=hd_node_th.derive(i).private_key().hex()
# Print out everything
print('')
print('Your mnemonic words are:    ' + str(words_th))
print('Your wallet private key is: ' + str(privkey_th))
print('Your wallet address is:     ' + str(address_th))
print('')

#Output:
#Your mnemonic words are:    ['trick', 'follow', 'resource', 'bind', 'fabric', 'ancient', 'tragic', 'weird', 'limit', 'soft', 'cousin', 'husband']
#Your wallet private key is: 422aa579196a6ab9fec7a0cb4049b8a322d82e52f19e944af7896f2ddf6b6210
#Your wallet address is:     0x4271530dac4cc2f34c240e1dbed6c81885c290a0

#---------------------------------------------------------------------------------------------------------
#Creating 'token bridge' wallet which will simulate the VeChain part of the token bridge
#---------------------------------------------------------------------------------------------------------

# Generate random mnemonic words or reuse some already generated - DO NOT USE ON MAINNET!
words_sc = ['pig', 'fame', 'comic', 'equal', 'debris', 'this', 'island', 'deer', 'what', 'bag', 'assist', 'conduct']
#words_sc = mnemonic.generate()

# Construct HD node from words. 
hd_node_sc = cry.HDNode.from_mnemonic(words_sc)
# Get address and privatekey from words_sc
for i in range(0, 1):
   address_sc='0x'+hd_node_sc.derive(i).address().hex()
   privkey_sc=hd_node_sc.derive(i).private_key().hex()
# Print out everything
print('')
print('Your mnemonic words are:    ' + str(words_sc))
print('Your wallet private key is: ' + str(privkey_sc))
print('Your wallet address is:     ' + str(address_sc))
print('')

#Output:
#Your mnemonic words for SC are:    ['pig', 'fame', 'comic', 'equal', 'debris', 'this', 'island', 'deer', 'what', 'bag', 'assist', 'conduct']
#Your wallet private key for SC is: 3833960b90e550e30f1efbb33505417c4fd67f9c4ac1fe0386fb6667384c1755
#Your wallet address for SC is:     0xd042a9d3f6648f0a803e230c8b998ca02c94cea1

#---------------------------------------------------------------------------------------------------------
#Loading the interface:
#---------------------------------------------------------------------------------------------------------
ERC20_CONTRACT = Contract.fromFile("./VTHO.json")
print(ERC20_CONTRACT)

#---------------------------------------------------------------------------------------------------------
#NB: This is only to be used for simulating in test environment. Absolutely NOT production material this!
#---------------------------------------------------------------------------------------------------------

#Connecting to testnet and getting the associated token list:
NODE_URL     = "https://sync-testnet.vechain.org" # node connection
TOKEN_LIST   = 'https://vechain.github.io/token-registry/test.json' # main net is main.json

CONNECTOR      = Connect(NODE_URL)

# Gather tokens list
r = requests.get(TOKEN_LIST)
assert r.status_code == 200
tokens = r.json()

#---------------------------------------------------------------------------------------------------------
Checking balances of token holder's wallet:
#---------------------------------------------------------------------------------------------------------
#VET being native coin has own function
CONNECTOR.get_vet_balance(WALLET_ADD)

balance_clauses = [ CONNECTOR.clause(ERC20_CONTRACT, 'balanceOf', [address_th], token['address']) for token in tokens]
results = CONNECTOR.call_multi(address_th, balance_clauses)
assert len(results) == len(tokens)
balances = [int(x['decoded']['0']) for x in results]
for token, balance in zip(tokens, balances):
  if (token["symbol"] == "VTHO"):
    print(f'{token["symbol"]}: {balance}')
    
#---------------------------------------------------------------------------------------------------------
Setting up receiving wallet address on the Polkadot blockchain
#---------------------------------------------------------------------------------------------------------    
Wallet_polkadot_receiver = '5GTAHGPnMLpz3cuWe9omkW5eGBk2uUMhHEm8tkJpKamaBBuj'
WPR_HEX = Wallet_polkadot_receiver.encode('utf-8').hex()
print(WPR_HEX)

#Sanity check:
Wallet_polkadot_receiver_decoded = bytes.fromhex(WPR_HEX).decode('utf-8')
print(Wallet_polkadot_receiver_decoded)
assert Wallet_polkadot_receiver == Wallet_polkadot_receiver_decoded

#Output:
#'5GTAHGPnMLpz3cuWe9omkW5eGBk2uUMhHEm8tkJpKamaBBuj'

#---------------------------------------------------------------------------------------------------------
Building VeChain transaction
#---------------------------------------------------------------------------------------------------------    
body = {
    "chainTag": 39, # chainTag 39 = testnet,  see: https://docs.vechain.org/others/#network-identifier for more details
    "blockRef": '0x00c86110816551d2', # to get latest blockRef: https://docs.vechain.org/thor/learn/transaction-model.html#model
    "expiration": 720, # blockref + expiration = blocknumber where TX expires
    "clauses": [  # here the clause section starts
        {
            "to": address_sc, # destination of vet
            "value": 42000000000000000000, # how much vet will be send. Vet has 18 decimals, so this equals to 42 vet.
            "data": '0x' + WPR_HEX # Address of receiving wallet on the Polkadot blockchain after bridging
        }
    ],
    "gasPriceCoef": 0, # gasPriceCoef can be between 0 and 255 to increase the urgency of your transactions
    "gas": 210000, # maximum gas a tx can consume
    "dependsOn": None, # you can stage transactions, irrelevant for now
    "nonce": 12345679 # nonce for proof-of-work and uniquesness of the transaction
}

print(body)
#Output:
#{'chainTag': 39, 'blockRef': '0x00c86169b6ec016a', 'expiration': 720, 'clauses': [{'to': '0xd042a9d3f6648f0a803e230c8b998ca02c94cea1', 'value': 42000000000000000000, 'data': '0x354754414847506e4d4c707a3363755765396f6d6b57356547426b3275554d6848456d38746b4a704b616d614242756a'}], 'gasPriceCoef': 0, 'gas': 210000, 'dependsOn': None, 'nonce': 12345679}

#---------------------------------------------------------------------------------------------------------
# Sign the transaction with the private key.
#---------------------------------------------------------------------------------------------------------
priv_key = bytes.fromhex(privkey_th)
message_hash = tx.get_signing_hash()
signature = cry.secp256k1.sign(message_hash, priv_key)

# Set the signature on the transaction.
tx.set_signature(signature)

print('Created a transaction from ' + tx.get_origin() + ' to 0x0000000000000000000000000000000000000000 with TXID: ' + tx.get_id() + '.')
print('')
#Output:
#Created a transaction from 0x4271530dac4cc2f34c240e1dbed6c81885c290a0 to 0x0000000000000000000000000000000000000000 with TXID: 0xe30bfcd1c3b69e5ab10611f125bfa543300f825338c1011ba25404729dd6024f.

encoded_bytes = tx.encode()

# pretty print the encoded bytes.
print('The transaction "0x' + encoded_bytes.hex() + '" will be send to the testnet node now.')

#Output:
#The transaction "0xf8ae2787c86169b6ec016a8202d0f852f85094d042a9d3f6648f0a803e230c8b998ca02c94cea1890246ddf97976680000b0354754414847506e4d4c707a3363755765396f6d6b57356547426b3275554d6848456d38746b4a704b616d614242756a80830334508083bc614fc0b841abf818757f4e0309222e7d44638755798fd04153866c95c9323da79f77d2f52952c87170e268fa67434c2ee575983c5a455cb4920892cc9ab4a7f5c92107bc5901" will be send to the testnet node now.

#---------------------------------------------------------------------------------------------------------
# Send the transaction
#---------------------------------------------------------------------------------------------------------
tx_headers = {'Content-Type': 'application/json', 'accept': 'application/json'}
tx_data = {'raw': '0x' + encoded_bytes.hex()}
	
send_transaction = requests.post('https://testnet.veblocks.net/transactions', json=tx_data, headers=tx_headers)

print('Response from Server: ' + str(send_transaction.content))
#Output:
#Response from Server: b'{"id":"0xe30bfcd1c3b69e5ab10611f125bfa543300f825338c1011ba25404729dd6024f"}\n'

response = CONNECTOR.replay_tx("0x8632d95b5eb26d709377a49e687f532da766108ef918243927bdd2593c0bb25a")
print(response)
#Output.
#[{'data': '0x', 'events': [], 'transfers': [{'sender': '0x4271530dac4cc2f34c240e1dbed6c81885c290a0', 'recipient': '0xd042a9d3f6648f0a803e230c8b998ca02c94cea1', 'amount': '0x3860e639d80640000'}], 'gasUsed': 0, 'reverted': False, 'vmError': ''}]

Response from Server: b'{"id":"0x8632d95b5eb26d709377a49e687f532da766108ef918243927bdd2593c0bb25a"}\n'

#---------------------------------------------------------------------------------------------------------
# Transaction result
#---------------------------------------------------------------------------------------------------------
https://explore-testnet.vechain.org/transactions/0xe30bfcd1c3b69e5ab10611f125bfa543300f825338c1011ba25404729dd6024f#info

#Voila!
Footer
© 2022 GitHub, Inc.
Footer navigation
Terms
Privacy
Security
Status
Docs
Contact GitHub
Pricing
API
Training
Blog
About
