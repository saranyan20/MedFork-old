# Note we imported all request!
from flask import Flask, render_template, request
from blockchain import Blockchain
from flask import Flask, jsonify, request
from uuid import uuid4
from key_pair_helpers import Key
import hashlib,json
import json,pickle,random
import ipfs_integration as ipfs
import encryp
import ipfs_versioning as ipfsver
import ipfshttpclient
import datetime
import io
import json
import os
from config import *
import base64
import data_sharing_helpers as share
from umbral import keys
import chalk

app = Flask(__name__)
node_identifier = str(uuid4()).replace('-', '')

# Retain state of Blockchain...
#try:
	#with open("blockchain_state",'rb') as file:
#		blockchain=pickle.load(file)
#except:
blockchain = Blockchain()

# Main page
@app.route('/index.html')
def index():
	return render_template('index.html')

# key generation
@app.route('/key_generation.html')
def key_generation():
	return render_template('key_generation.html')

# Redirection to home page
@app.route('/index.html', methods=['POST','GET'])
def index2():
	if request.method=='POST':
		uid = 23
		uid=request.form['id']
		encryp.gen_keypair(uid)
		verify={
		"status":"success",
		}
		print(verify)
		return render_template('index.html')

# USERS PART
@app.route("/applicant_details.html")
def applicant_details():
	return render_template('applicant_details.html')
 
@app.route("/processing.html", methods=['POST','GET'])
def processing():
	if request.method=='POST':
		# Please generate keys before filling this .... 
		uid=request.form['uuid']
		name=request.form['name']
		dob=request.form['dob']
		pnum=request.form['pnum']
		address=request.form['address']
		encryp.gen_keypair(uid)
		# Change in encryp file
		ruid = request.form['ruid']
		encryp.gen_keypair(ruid)
		personal_details = {
		"uid":uid,
		"name":name,
		"dob":dob,
		"pnum":pnum,
		"Acceptor_uid":ruid
		}
		print("Personal Details is retrived ....")
		print(personal_details)
		with open(f'{uid}PersonalData.json', 'w') as file:
			json.dump(personal_details,file,indent=4)
		return render_template('processing.html',uuid = uid, ruid = ruid ,name = name, dob = dob, pnum = pnum, address = address)
	else:
		return render_template('applicant_details.html')

# DOCTORs PART
@app.route('/medical_details.html')
def medical_details():
	return render_template('medical_details.html')


def json_file_check(filename):
	if os.path.isfile(f"./{filename}") and os.access(f"./{filename}", os.R_OK):
		print (f"{filename} exists and is readable")
		return True
	else:
		print (f"Either {filename} is missing or is not readable, creating {filename}...")
		with io.open(os.path.join('.', f"{filename}"), 'w') as file:
			file.write(json.dumps([[1,0]]))
		return False


# This page will be the page after the form
@app.route("/processsing.html", methods=['POST','GET'])
def processsing():
	# add selection bar for type of transaction
	if request.method=='POST':	
		uid=request.form['uuid']
		duid=request.form['duid']
		diabetes_level=request.form['diabetes_level']
		bp_level=request.form['bp_level']
		Type=request.form['exist'] # exists 1 --> update # 2 --> new
		details=request.form['details']
		encryp.gen_keypair(uid)
		encryp.gen_keypair(duid)
		print(bp_level,diabetes_level)
		print(Type)
		json_file_check(f"./static/graph_ploter/{uid}_diabetes.json")
		with open(f"./static/graph_ploter/{uid}_diabetes.json",'r+') as file:
			data=json.load(file)
			print(data[-1])
			last=data[-1][0]
			data.append([last+1,int(diabetes_level)])
			file.seek(0)
			json.dump(data,file,indent=4)
			file.truncate()
		
		json_file_check(f"./static/graph_ploter/{uid}_bp.json")
		with open(f"./static/graph_ploter/{uid}_bp.json",'r+') as file:
			data=json.load(file)
			print(data[-1])
			last=data[-1][0]
			data.append([last+1,int(bp_level)])
			file.seek(0)
			json.dump(data,file,indent=4)
			file.truncate()			
		medical_details = {
		"typeOfTransaction":Type,
		"uid":uid,
		"doctorUid":duid,
		"data":details
		}
		print("Medical Details is retrived ...")
		print(medical_details)
		with open(f'{uid}_medical_report.json', 'w') as file:
			json.dump(medical_details,file,indent=4)

		if Type == "exist2": # if first transaction 
			print("New Transaction initiated....")
			capsule=encryp.encrypt_file(uid,f"{uid}_medical_report.json")
			ipfs_file_hash=ipfs.upload_ipfs(uid,f"{uid}_medical_report.json_encrypted")
			version_holder=ipfsver.update_medical_record(uid,ipfs_file_hash,capsule)
			
			with open(f'{uid}_public_key.pem','rb') as f:
				public_key_patient=keys.UmbralPublicKey.from_bytes(f.read())
			with open(f'{duid}_public_key.pem','rb') as f:
				public_key_doctor=keys.UmbralPublicKey.from_bytes(f.read())

			digital_sign_doctor=encryp.digital_sign(duid,text_data=ipfs_file_hash)
			digital_sign_patient=encryp.digital_sign(uid,text_data=ipfs_file_hash)

			#even if one can able to fake this Verification, during mining other nodes will verify and rule out the transaction
			if(encryp.sign_verification(duid,base64.b64decode(digital_sign_doctor.encode()),text_data=ipfs_file_hash) and
			(encryp.sign_verification(uid,base64.b64decode(digital_sign_patient.encode()),text_data=ipfs_file_hash))):
				index = blockchain.new_transaction( ipfs_file_hash=ipfs_file_hash,
											version_holder=version_holder,
											digital_sign_doctor=digital_sign_doctor,
											digital_sign_patient=digital_sign_patient,
											public_key_doctor=encryp.base64encode(public_key_doctor.to_bytes()),
											public_key_patient=encryp.base64encode(public_key_patient.to_bytes()),
											time=str(datetime.datetime.now()),
											modification="false",
											UUID=uid )
				response = {'message': f'Transaction will be added to Block {index}'}
				print("N-True")
				return render_template('processsing.html',uuid = uid, details = details)
			else:
				print({'message': f'This is not a vaild transaction'})
				print("N-False")
				return render_template('medical_details.html')
		else: # if updprint(chalk.yellow("Update(medical report) request"))ate transaction # if type is not new then update is considered
			#uid=request.get_json()["uid"]
			print("Update(medical report) request")
			new_file_hash,ipns_hash=ipfsver.ipfs_version_holder_updater(uid)
			with open(f'{uid}_public_key.pem','rb') as f:
				public_key_patient=keys.UmbralPublicKey.from_bytes(f.read())
			with open(f'{duid}_public_key.pem','rb') as f:
				public_key_doctor=keys.UmbralPublicKey.from_bytes(f.read())
			digital_sign_doctor=encryp.digital_sign(duid,text_data=new_file_hash)
			digital_sign_patient=encryp.digital_sign(uid,text_data=new_file_hash)
			if(encryp.sign_verification(duid,base64.b64decode(digital_sign_doctor.encode()),text_data=new_file_hash) and
			   (encryp.sign_verification(uid,base64.b64decode(digital_sign_patient.encode()),text_data=new_file_hash))):
				index = blockchain.new_transaction( ipfs_file_hash=new_file_hash,
								version_holder=ipns_hash,
								digital_sign_doctor=digital_sign_doctor,
								digital_sign_patient=digital_sign_patient,
								public_key_doctor=encryp.base64encode(public_key_doctor.to_bytes()),
								public_key_patient=encryp.base64encode(public_key_patient.to_bytes()),
								time=str(datetime.datetime.now()),
								modification="true",
								UUID=uid )
				response = {'message': f'Medical Record has been updated successfully!.'}
				print("U-True")
				return render_template('processsing.html',uuid = uid, details = details)
			else:
				response = {'message': f'This is not a vaild transaction'}
				print("U-False")
				return render_template('medical_details.html') 
	else:
		return render_template('medical_details.html')

# MINE after transaction is created ...
@app.route('/mine_page')
def mine_page():
	return render_template('mine.html')

@app.route('/index2.html', methods=['GET'])
def mine():
	# if Mine button is clicked .....
	last_block = blockchain.last_block
	proof = blockchain.proof_of_work(last_block)
	previous_hash = blockchain.hash(last_block)
	block = blockchain.new_block(proof, previous_hash)
	
	response = {
		'message': "New Block Added",
		'index': block['index'],
		'transactions': block['transactions'],
		'proof': block['proof'],
		'previous_hash': block['previous_hash'],
	}
	print(response)
	return render_template('index.html')


@app.route('/latest_transaction')
def latest_transaction():
	# get patient_id
	'''if request.method=='POST':	
		patient_id=request.form['uuid']
		try:
			ipfsver.retrive_lastest(patient_id)
			with open(f"{uid}_medical_report.json","r") as file:
				data=json.load(file)
			print(jsonify(data))
		except:
			print("Invalid UID")'''
	return render_template('latest_transaction.html')

@app.route('/version_holder')
def version_holder():
	return render_template('version_holder.html')

@app.route('/version_holder',methods=['POST','GET'])
def version_holder_processing():
	# get uid ..
	# if request.method=='POST':
	# 	uid=request.form['uuid']
	# 	print(uid)
	# 	print(chalk.yellow("checking version holder data"))
	# 	with open("ipns_hash_indices.json",'r') as file:
	# 		ipns_hash=json.load(file)[uid]
	# 		with ipfshttpclient.connect() as client:
	# 			holder_file_hash=client.name.resolve(ipns_hash)['Path'].lstrip("/ipfs/")
	# 			client.get(holder_file_hash)
	# 			with open(holder_file_hash,'r') as file:
	# 				res=json.load(file)
	# 	print(res)
	return render_template('version_holder.html')

# Hospital registration ...

# Render plate (nodes)

@app.route('/node_registration.html')
def node_registration():
	return render_template('node_registration.html')

@app.route('/index2.html', methods=['POST','GET'])
def node_register():
	# get details ...
	if request.method == 'POST':
		h_id = request.form['h_id']
		h_url = request.form['h_url']
		h_name = request.form['h_name']
		ima_num = request.form['ima_num']
		h_add = request.form['h_add']
		nodes = h_url

		hospital_details = {
			"h_id":h_id,
			"url":h_url,
			"name":h_name,
			"ima_num":ima_num,
			"address":h_add,
			}
		print("Hospital Details is retrived ....")
		print(hospital_details)
		with open(f'{nodes}HospitalData.json', 'w') as file:
			json.dump(hospital_details,file,indent=4)

		if nodes is None:
			print("Error: Please supply a valid list of nodes")
			return render_template('index.html')

		blockchain.register_node(nodes)

		response = {
			'message': 'New nodes have been added',
			'total_nodes': list(blockchain.nodes),
		}
		print(response)
		return render_template('index.html')


# share data ....

@app.route('/share/new_policy', methods=['GET','POST'])
def share_data():
	# Saran ...
	if request.method=='POST':	
		s_uid=request.form['s_uid']
		r_uid=request.form['r_uid']
		data_hash=request.form['data_hash'] # version holder refer ....
		public_key_digitalsign=request.form['public_key_digitalsign']
		capsule=request.form['capsule']
		remove=request.form['remove']
		share.new_policy(s_uid,r_uid,data_hash,public_key_digitalsign,capsule,remove)
		print("status : success")
		print("message : New policy has been added !")


@app.route('/view_policy', methods=['GET'])
def share_datas():
	with open("data_sharing_policies.json",'r+') as file:
		response=json.load(file)
		print(response)


# reencrypt ....
@app.route('/re_encrypt', methods=['GET','POST'])
def re_encrypt():
	# Saran ....
	if request.method=='POST':	
		s_uid=request.form['s_uid']
		r_uid=request.form['r_uid']
		public_key_digitalsign=request.form['public_key_digitalsign']
		response=share.re_encrypt(s_uid,r_uid,public_key_digitalsign)
		print(response)
	return render_template('re_encrypt.html')

# check patient details ...
@app.route('/check_data', methods=['POST','GET'])
def check_patient_data():
	# Saran ....
	if request.method=='POST':	
		request_patient = request.form['uid']
		data_blocks=[]
		for blocks in blockchain.chain[::-1]:
			idx=blocks["index"]
			trans=blocks["transactions"]
			for i in trans:
				if i["UUID"]==request_patient:
					data_blocks.append(idx)
					continue
		if data_blocks:
			result = "the requested patient details found in the following blocks","Block_indices : {}".format(data_blocks)
		else:
			result = "the requested patient details cannot be found"
		print(result)
	return render_template('check_data.html')

@app.route('/nodes_resolve', methods=['GET'])
def consensus():
	replaced = blockchain.resolve_conflicts()
	if replaced:
		response = {
			'message': 'Our chain was replaced',
			'new_chain': blockchain.chain
		}
	else:
		response = {
			'message': 'Our chain is authoritative',
			'chain': blockchain.chain
		}
	print(response)


# EXPLORING
@app.route('/full_chain.html')
def full_chain():	
	response = {
		'chain': blockchain.chain,
		'length': len(blockchain.chain),
	}
	print(response)	
	return render_template('full_chain.html')

@app.route('/fullchain_transac_details')
def fullchain_transac_details():
	return render_template('fullchain_transac_details.html')


@app.route('/block_explorer.html')
def block_explorer():
	print("Transaction at given block")
	return render_template('block_explorer.html')

@app.route('/blockexplorer_transac_details')
def blockexplorer_transac_details():
	# # get block number
	# for blocks in blockchain.chain:
	# 	if blocks["index"]==int(index):
	# 		response=blocks
	# 		break
	# else:
	# 	response={"status":"failed","message":"Invalid block index"}
	return render_template('blockexplorer_transac_details.html')

@app.route('/full_transaction.html')
def full_transaction():
	print("Transaction at given block")
	return render_template('full_transaction.html')

@app.route('/save', methods=['GET'])
def save_state():
	with open("blockchain_state","wb") as file:
		pickle.dump(blockchain,file)
	print(chalk.red(("State saved...!!!")))
	print("Blockchain is svaed")

@app.route('/sugar_report.html')
def sugar_report():
	print("Diabetes report plotted in graph")
	return render_template('sugar_report.html')

@app.route('/bp_report.html')
def bp_report():
	print("BP report plotted in graph")
	return render_template('bp_report.html')

@app.route('/graph.html')
def graph():
	print("BP report plotted in graph")
	return render_template('graph.html')



@app.errorhandler(404)
def page_not_found(e):
	return render_template('404.html'), 404

if __name__ == '__main__':
	app.run(debug = True)
