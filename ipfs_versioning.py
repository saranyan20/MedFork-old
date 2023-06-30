import json
import ipfshttpclient
from json_check import json_file_check
import ipfs_integration as ipfs
import os
from config import *
import encryp
from umbral.curve import Curve, SECP256K1
from umbral import pre
from umbral.params import UmbralParameters
import base64
import chalk 

def gen_ipnskey(uid):
	with ipfshttpclient.connect() as client:
		try:
			hash=client.key.gen(f"{uid}_ipnskey",type="rsa")['Id']
		except:
			for i in client.key.list()['Keys']:
				if i["Name"]==f"{uid}_ipnskey":
					hash=i["Id"]
			return hash
		json_file_check("ipns_hash_indices.json")
		with open("ipns_hash_indices.json",'r+') as file:
			data=json.load(file)
			print("Updating.... ipns hash indices",end='\n')
			data[uid]=hash
			file.seek(0)
			json.dump(data,file,indent=4)
			file.truncate()
	return hash

def get_ipns_hash_from_index(uid):
	with open("ipns_hash_indices.json",'r') as file:
		data=json.load(file)
	return data[uid]


def ipfs_version_holder(uid):
	if(not json_file_check(f"./static/block_explorer/{uid}_version_holder.json")):
		with open(f"./static/block_explorer/{uid}_version_holder.json","r+") as file:
			data={"versions":[]}
			json.dump(data,file,indent=4)
	# if(not json_file_check(f"{uid}_version_holder1.json")):
	# 	with open(f"./static/block_explorer/{uid}_version_holder1.json","r+") as file:
	# 		dt = []
	# 		json.dump(dt,file,indent=4)



def update_medical_record(uid,initial_hash,capsule): #for 1st transaction only
	ipns_hash=gen_ipnskey(uid)
	ipfs_version_holder(uid)
	print("ipns hash=",ipns_hash)
	with open(f"./static/block_explorer/{uid}_version_holder.json",'w') as file:
		data={"versions":[{"version":1,"ipfs_hash":initial_hash,"KEM":capsule}]}
		json.dump(data,file)
	# Local ....

	with open(f"./static/block_explorer/{uid}_version_holder1.json",'w') as file:
		dt = [{"version":1,"ipfs_hash":initial_hash,"KEM":capsule}]
		print(dt)
		json.dump(dt,file,indent = 4)
		
	with open("ipns_hash_indices.json",'r') as f:
		with ipfshttpclient.connect() as client:
			data=json.load(f)[uid]
			#place the version json
			index_holder_hash=ipfs_version_holder(uid)
			hash=ipfs.upload_ipfs(uid,f"./static/block_explorer/{uid}_version_holder.json")
			ret=client.name.publish(hash,key=f"{uid}_ipnskey")["Name"]
			print("The static ipns hash :",ipns_hash)
			print("ipns key(version holder) and newly upload hash comparsion, result=",ret==ipns_hash)
	return ipns_hash

def ipfs_version_holder_updater(uid):  #this gets new medical data and updates into ipns
	ipns_hash=get_ipns_hash_from_index(uid)
	print("ipns_hash:",end=" ")
	print(ipns_hash)
	with ipfshttpclient.connect() as client:
		holder_file_hash=client.name.resolve(ipns_hash)['Path'].lstrip("/ipfs/")
		try:
			os.remove(f"./static/block_explorer/{uid}_version_holder.json")
		except:
			pass
		client.get(holder_file_hash)
		os.rename(holder_file_hash,f"./static/block_explorer/{uid}_version_holder.json")
		with open(f"./static/block_explorer/{uid}_version_holder.json",'r+') as file:
			data=json.load(file)
			version_data=data["versions"]
			# During first new transaction ... version_data = [] 
			if(not version_data):
				new_ver=1
			else:
				#print("ver vals :",[int(i["version"]) for i in version_data ])
				new_ver=max([int(i["version"]) for i in version_data ])+1
			# As single page transaction for both new and update transaction (Data already got.)
			#ipfs.get_details(uid)
			capsule=encryp.encrypt_file(uid,f"{uid}_medical_report.json")
			new_file_hash=ipfs.upload_ipfs(uid,f"{uid}_medical_report.json_encrypted")
			new_field={"version":new_ver,"ipfs_hash":new_file_hash,"KEM":capsule}
			data["versions"].append(new_field)
			file.seek(0)
			json.dump(data,file,indent=4)
			file.truncate()
		# Changed now .... (28-1-2020)
		with open(f"./static/block_explorer/{uid}_version_holder1.json",'r+') as file:
			data=json.load(file)
			new_field={"version":new_ver,"ipfs_hash":new_file_hash,"KEM":capsule}
			data.append(new_field)
			file.seek(0)
			json.dump(data,file,indent=4)
			print(data)
			file.truncate()
	with ipfshttpclient.connect() as client:
		hash=client.add(f"./static/block_explorer/{uid}_version_holder.json")['Hash'] #second connection because we can't upload file without closing it
		res=client.name.publish(hash,key=f"{uid}_ipnskey")
	return new_file_hash,ipns_hash

	print(f"new medical record of {uid} has been updated to version holder")
	print(f"the static ipns address of {uid}--> {res['Name']}")

def retrive_lastest(uid):
	encryp.gen_keypair(uid)
	with open("ipns_hash_indices.json",'r') as file:
		data=json.load(file)
		hash=data[uid]
		print("client connectin....")
		with ipfshttpclient.connect() as client:
			hash=client.name.resolve(hash)['Path'].lstrip("/ipfs/")
			client.get(hash)
			print("Retriving version holder......")
			print(hash, type(hash))
			with open(str(hash),'r') as file:
				print("processing version holder......")
				data=json.load(file)
				version_data=data["versions"]
				capsule=version_data[-1]["KEM"]
				latest=version_data[-1]["ipfs_hash"]
				print("The current version of your medical record is Version.",version_data[-1]["version"])

				try:
					os.remove(f"{uid}_medical_report.json_encrypted")
				except:
					pass
				finally:
					client.get(latest)
					os.rename(latest,f"{uid}_medical_report.json_encrypted")
					print("retriving and decrypting latest version")
					encryp.decrypt_file(uid,f"{uid}_medical_report.json",
										pre.Capsule.from_bytes(base64.b64decode(capsule.encode()),
															   UmbralParameters(SECP256K1)))









'''update_medical_record("nithya1005")
ipfs_version_holder_updater("nithya1005")
retrive_lastest("nithya1005")'''
