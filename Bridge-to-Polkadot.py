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
VET_bal = CONNECTOR.get_vet_balance(address_th)
print('VET : ', int(VET_bal)/10**18)

balance_clauses = [ CONNECTOR.clause(ERC20_CONTRACT, 'balanceOf', [address_th], token['address']) for token in tokens]
results = CONNECTOR.call_multi(address_th, balance_clauses)
assert len(results) == len(tokens)
balances = [int(x['decoded']['0']) for x in results]
for token, balance in zip(tokens, balances):
  if (token["symbol"] == "VTHO"):
    print(f'{token["symbol"]}: {int(balance)/10**18}')
    
#Amount of tokens to be bridged
VET_sending = 55.5
assert VET_sending <= VET_bal

VET_tx = int(VET_sending * 10**18)
print(VET_tx)

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
#Building VeChain transaction
#---------------------------------------------------------------------------------------------------------    
body = {
    "chainTag": 39, # chainTag 39 = testnet,  see: https://docs.vechain.org/others/#network-identifier for more details
    "blockRef": '0x00c7c9a82cf31351', # to get latest blockRef: https://docs.vechain.org/thor/learn/transaction-model.html#model
    "expiration": 720, # blockref + expiration = blocknumber where TX expires
    "clauses": [  # here the clause section starts
        {
            "to": address_sc, # destination of vet
            "value": VET_tx, # how much vet will be send. Vet has 18 decimals
            "data": '0x' + WPR_HEX # Address of receiving wallet on the Polkadot blockchain after bridging
        }
    ],
    "gasPriceCoef": 0, # gasPriceCoef can be between 0 and 255 to increase the urgency of your transactions
    "gas": 210000, # maximum gas a tx can consume
    "dependsOn": None, # you can stage transactions, irrelevant for now
    "nonce": 12345679 # nonce for proof-of-work and uniquesness of the transaction
}

print(body)
#---------------------------------------------------------------------------------------------------------
# Create the transaction
#---------------------------------------------------------------------------------------------------------

from thor_devkit import cry, transaction
# Construct an unsigned transaction.
tx = transaction.Transaction(body)

#Output:
#{'chainTag': 39, 'blockRef': '0x00c88a23fb1229bc', 'expiration': 720, 'clauses': [{'to': '0xd042a9d3f6648f0a803e230c8b998ca02c94cea1', 'value': 55500000000000000000, 'data': '0x354754414847506e4d4c707a3363755765396f6d6b57356547426b3275554d6848456d38746b4a704b616d614242756a'}], 'gasPriceCoef': 0, 'gas': 210000, 'dependsOn': None, 'nonce': 12345679}

#---------------------------------------------------------------------------------------------------------
# Sign the transaction with the private key.
#---------------------------------------------------------------------------------------------------------
priv_key = bytes.fromhex(privkey_th)
message_hash = tx.get_signing_hash()
signature = cry.secp256k1.sign(message_hash, priv_key)

# Set the signature on the transaction.
tx.set_signature(signature)
tx_ID = tx.get_id()

print('Created a transaction from ' + tx.get_origin() + ' to ', address_sc, ' with TXID: ' + tx_ID + '.')
print('')
#Output:
#Created a transaction from 0x4271530dac4cc2f34c240e1dbed6c81885c290a0 to  0xd042a9d3f6648f0a803e230c8b998ca02c94cea1  with TXID: 0x9c5e4bdb227ab68293cc9d1ca98e206602623836ac54c2146f4e669d91aa54f2.

encoded_bytes = tx.encode()

# pretty print the encoded bytes.
print('The transaction "0x' + encoded_bytes.hex() + '" will be send to the testnet node now.')

#Output:
#The transaction "0xf8ae2787c88a23fb1229bc8202d0f852f85094d042a9d3f6648f0a803e230c8b998ca02c94cea1890302379bf2ca2e0000b0354754414847506e4d4c707a3363755765396f6d6b57356547426b3275554d6848456d38746b4a704b616d614242756a80830334508083bc614fc0b84129a916dccea79c8fb777322eb9908d833b263c7deaf4474b14660b58830acd8249b6da7bd042678a070678df448c68fe988892c68ba34384db5f5dab6c5684b400" will be send to the testnet node now.

#---------------------------------------------------------------------------------------------------------
# Send the transaction
#---------------------------------------------------------------------------------------------------------
tx_headers = {'Content-Type': 'application/json', 'accept': 'application/json'}
tx_data = {'raw': '0x' + encoded_bytes.hex()}
	
send_transaction = requests.post('https://testnet.veblocks.net/transactions', json=tx_data, headers=tx_headers)

print('Response from Server: ' + str(send_transaction.content))
#Output:
#Response from Server: b'{"id":"0x9c5e4bdb227ab68293cc9d1ca98e206602623836ac54c2146f4e669d91aa54f2"}\n'

response = CONNECTOR.replay_tx(tx_ID)
print(response)
#Output.
#[{'data': '0x', 'events': [], 'transfers': [{'sender': '0x4271530dac4cc2f34c240e1dbed6c81885c290a0', 'recipient': '0xd042a9d3f6648f0a803e230c8b998ca02c94cea1', 'amount': '0x302379bf2ca2e0000'}], 'gasUsed': 0, 'reverted': False, 'vmError': ''}]

print(tx_ID)
#Output: 0x9c5e4bdb227ab68293cc9d1ca98e206602623836ac54c2146f4e669d91aa54f2
#---------------------------------------------------------------------------------------------------------
# Transaction result
#---------------------------------------------------------------------------------------------------------
#https://explore-testnet.vechain.org/transactions/0xe30bfcd1c3b69e5ab10611f125bfa543300f825338c1011ba25404729dd6024f#info
#"Voila!

#---------------------------------------------------------------------------------------------------------
#Fetch transaction result from blockchain:
#---------------------------------------------------------------------------------------------------------
tx = requests.get(NODE_URL + '/transactions/' + tx_ID)
print(tx)
tx_data = tx.json()
print(tx_data)

#Output:
#{'id': '0x9c5e4bdb227ab68293cc9d1ca98e206602623836ac54c2146f4e669d91aa54f2', 'chainTag': 39, 'blockRef': '0x00c88a23fb1229bc', 'expiration': 720, 'clauses': [{'to': '0xd042a9d3f6648f0a803e230c8b998ca02c94cea1', 'value': '0x302379bf2ca2e0000', 'data': '0x354754414847506e4d4c707a3363755765396f6d6b57356547426b3275554d6848456d38746b4a704b616d614242756a'}], 'gasPriceCoef': 0, 'gas': 210000, 'origin': '0x4271530dac4cc2f34c240e1dbed6c81885c290a0', 'delegator': None, 'nonce': '0xbc614f', 'dependsOn': None, 'size': 176, 'meta': {'blockID': '0x00c88a2e0968555584883189cf684da83d4814319364ade90d0824fc89462508', 'blockNumber': 13142574, 'blockTimestamp': 1661457090}}

#Fetch block result from blockchain to ensure finality:
blocknum = tx_data['meta']['blockNumber']
block = requests.get(NODE_URL + '/blocks/' + str(blocknum))
print(block)
block_content = block.json()
print(block_content)
#Output:
#{'number': 13142574, 'id': '0x00c88a2e0968555584883189cf684da83d4814319364ade90d0824fc89462508', 'size': 858, 'parentID': '0x00c88a2d4793ed8269bda0db578a766a3314071fd1832ad62d74fcc16aa918bb', 'timestamp': 1661457090, 'gasLimit': 30000000, 'beneficiary': '0xb4094c25f86d628fdd571afc4077f0d0196afb48', 'gasUsed': 747494, 'totalScore': 78547532, 'txsRoot': '0x96e6f701cc85d67981c2e4a9441c967b438145103c2e1ffc3d853e897660569f', 'txsFeatures': 1, 'stateRoot': '0x4eb69e580db3f82b5d7747b5f1235dd6b46a39618404f2b8895f8d6b8773f2af', 'receiptsRoot': '0xc874050d95a17809bffb4dc9ad22664dbdf29b6de35adddd709bcee4e2d5c0e7', 'com': True, 'signer': '0x39218d415dc252a50823a3f5600226823ba4716e', 'isTrunk': True, 'isFinalized': False, 'transactions': ['0xcc2b6d593a756f2fb1948e00b39e6761309691fd6680d7c1f5a648bdeb0abf45', '0x9c5e4bdb227ab68293cc9d1ca98e206602623836ac54c2146f4e669d91aa54f2', '0x29daabb409f4a6ce99505153fd194fd9d60ec77470bf6ec61263d3bbd54467fa']}

#---------------------------------------------------------------------------------------------------------
#Wait until block is finalized 
#---------------------------------------------------------------------------------------------------------
import time

finalized = False
while (finalized == False):  
  if block_content['isFinalized'] == True:
    finalized = True
  else:  
    print("Waiting 5 more secs")
    time.sleep(5) #waits 5s for preformance
	
#---------------------------------------------------------------------------------------------------------
#Secure data structure for database
#---------------------------------------------------------------------------------------------------------
if (block_content['isFinalized'] == True):
  chainTag = tx_data['chainTag']
  blockNum = tx_data['meta']['blockNumber']
  blockID  = tx_data['meta']['blockID']
  TxID     = tx_data['id']
  sender   = tx_data['origin']  
  clauses  = tx_data['clauses']
  value    = clauses[0]['value']
  amount   = int(value, base=16)/10**18        

  receiver = clauses[0]['data']        
  if receiver[:2] == '0x':
     receiver = receiver[2:]
     receiver_decoded = bytes.fromhex(receiver).decode('utf-8')
     print(receiver)           
     print(len(receiver_decoded), ' ', receiver_decoded)

  print('chainTag: ', chainTag)
  print('blockNum: ', blockNum)
  print('blockID : ', blockID) 
  print('TxID    : ', TxID)    
  print('sender  : ', sender)  
  print('amount  : ', amount)  
  print('receiver: ', receiver)

#---------------------------------------------------------------------------------------------------------	
#Using a Google sheet as database mockup
#---------------------------------------------------------------------------------------------------------
from pyasn1_modules.rfc5208 import Attributes
from google.colab import auth
auth.authenticate_user()

import gspread
from google.auth import default
creds, _ = default()

gc = gspread.authorize(creds)

#-------------------------------------------------------------------------------------------------------------	
# Open our new sheet and add some data - create one yourself and get key from URL, then name a worksheet #Txs"
#-------------------------------------------------------------------------------------------------------------	
JUR_gs = gc.open_by_key('1hkQnl4cyrk5ARC2onffz9UTBbfl-Nsu_Ul1O9tC1JWI')
JUR_ws = JUR_gs.worksheet("Txs")

print(JUR_ws.spreadsheet.id)
print(JUR_ws.spreadsheet.title)

JUR_ws = JUR_gs.worksheet("Txs")

#-------------------------------------------------------------------------------------------------------------	
#Fill in data in Google sheet
#-------------------------------------------------------------------------------------------------------------	          
cells = 'B' + str(row_start) + ':H' + str(row_start)
print(cells)
JUR_ws.update(cells,[[chainTag,
		      blockNum,
		      blockID,
		      "TRUE",
		      Tx_ID,
		      sender,
		      amount,
		      receiver]])          
	
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
