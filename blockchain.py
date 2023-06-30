from time import time
import hashlib,json
import pickle
import hashlib
import json
from urllib.parse import urlparse
import requests
from config import *
import chalk
import io,os

class Blockchain:
	def __init__(self):
		self.current_transactions = []
		self.chain = []
		self.transaction_count = 0
		self.nodes = set()
		self.new_block(previous_hash='1', proof=100)
		self.approved_hospital = []

	def register_node(self, address):
		parsed_url = urlparse(address)
		if parsed_url.netloc:
			self.nodes.add(parsed_url.netloc)
		elif parsed_url.path:
			self.nodes.add(parsed_url.path)
		else:
			raise ValueError('Invalid URL')


	def valid_chain(self, chain):

		last_block = chain[0]
		current_index = 1

		while current_index < len(chain):
			block = chain[current_index]
			print(f'{last_block}')
			print(f'{block}')
			print("\n-----------\n")
			last_block_hash = self.hash(last_block)
			if block['previous_hash'] != last_block_hash:
				return False

			if not self.valid_proof(last_block['proof'], block['proof'], last_block_hash):
				return False

			last_block = block
			current_index += 1

		return True

	def resolve_conflicts(self):

		neighbours = self.nodes
		new_chain = None

		max_length = len(self.chain)

		for node in neighbours:
			response = requests.get(f'http://{node}/chain')

			if response.status_code == 200:
				length = response.json()['length']
				chain = response.json()['chain']

				if length > max_length and self.valid_chain(chain):
					max_length = length
					new_chain = chain

		if new_chain:
			self.chain = new_chain
			return True

		return False

	def new_block(self, proof, previous_hash):


		block = {
			'index': 6,
			'timestamp': time(),
			'transactions': self.current_transactions,
			'proof': proof,
			'previous_hash': previous_hash or self.hash(self.chain[-1]),
		}
		# for my purpose
		block1 = {
			'index': len(self.chain) + 1,
			'timestamp': time(),
			'proof': proof,
			'previous_hash': previous_hash or self.hash(self.chain[-1]),
		}

		self.current_transactions = []
		# for processing ...
		with open(f'5block.json', 'w') as file:
			json.dump(block,file,indent=4)
		# for retriving ...
		with open(f'static/block_explorer/6block.json', 'w') as file:
			json.dump(block,file,indent=4)
		# To save the class blockchain
		'''with open("blockchain_state","wb+") as file:
			pickle.dump(Blockchain,file)
			print(chalk.red(("State saved...!!!")))
			print("Blockchain is saved")'''
		self.chain.append(block)
		return block

	@staticmethod
	def json_file_check(filename):
		if os.path.isfile(f"./{filename}") and os.access(f"./{filename}", os.R_OK):
			print (f"{filename} exists and is readable")
			return True
		else:
			print (f"Either {filename} is missing or is not readable, creating {filename}...")
			with io.open(os.path.join('.', f"{filename}"), 'w') as file:
				file.write(json.dumps([]))
			return False

	def new_transaction(self, ipfs_file_hash, version_holder, digital_sign_doctor, digital_sign_patient,					public_key_doctor, public_key_patient, time, modification, UUID ):
		self.current_transactions.append({
			'ipfs_file_hash': ipfs_file_hash,
			'version_holder': version_holder,
			'digital_sign_doctor': digital_sign_doctor,
			'digital_sign_patient': digital_sign_patient,
			'public_key_doctor': public_key_doctor,
			'public_key_patient': public_key_patient,
			'time': time,
			'modification': modification,
			'UUID': UUID,
		})
		Current_transactions={
			'ipfs_file_hash': ipfs_file_hash,
			'version_holder': version_holder,
			'digital_sign_doctor': digital_sign_doctor,
			'digital_sign_patient': digital_sign_patient,
			'public_key_doctor': public_key_doctor,
			'public_key_patient': public_key_patient,
			'time': time,
			'modification': modification,
			'UUID': UUID,
		}
		'''with open(f'static/block_explorer/{(self.transaction_count) + 1}transactions.json', 'w') as file:
			json.dump(Current_transactions,file,indent=4)
			'''
		# Local ..
		self.json_file_check(f'./static/block_explorer/{UUID}_full_transactions.json')
		with open(f'./static/block_explorer/{UUID}_full_transactions.json','r+') as file:
			data=json.load(file)
			data.append(Current_transactions)
			file.seek(0)
			json.dump(data,file,indent=4)
			file.truncate()

		self.transaction_count += 1
		with open(f'./static/block_explorer/{UUID}_transactions.json','w') as file:
			json.dump(Current_transactions,file,indent=4)
		with open(f'./static/block_explorer/6transactions.json', 'w') as file:
			json.dump(self.current_transactions,file,indent=4)
		return self.last_block['index'] + 1


	@property
	def last_block(self):
		return self.chain[-1]

	@staticmethod
	def hash(block):
		#block_string = str(block).encode()#c1
		block_string = json.dumps(block, sort_keys=True).encode()
		return hashlib.sha256(block_string).hexdigest()

	def proof_of_work(self, last_block):


		last_proof = last_block['proof']
		last_hash = self.hash(last_block)

		proof = 0
		while self.valid_proof(last_proof, proof, last_hash) is False:
			proof += 1

		return proof

	@staticmethod
	def valid_proof(last_proof, proof, last_hash):
		guess = f'{last_proof}{proof}{last_hash}'.encode()
		guess_hash = hashlib.sha256(guess).hexdigest()
		return guess_hash[:4] == "0000"
