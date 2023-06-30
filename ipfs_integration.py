import json
#import encryp
import ipfshttpclient
import os
from json_check import json_file_check
from config import *
import chalk

# Not used here ...
def get_details(uuid):
	uid=uuid
	n=int(input("Enter the no.of fields : "))
	medical_details=dict(input().split('=') for i in range(n))
	with open(f"{uuid}_medical_report.json","w") as file:
		json.dump(medical_details,file,indent=4)
	return uid

def upload_ipfs(uid,filename):
	print("IPFS conn:")
	with ipfshttpclient.connect() as client:
		print("uploading.... to ipfs",end='\n')
		hash = client.add(filename)['Hash']
		print("hash of the file : "+hash,end='\n')
		#os.remove(filename)
	json_file_check("hash_indices.json")
	with open("hash_indices.json",'r+') as file:
		print("updating.... hash indices",end='\n')
		data=json.load(file)
		data[uid]=hash
		file.seek(0)
		json.dump(data,file,indent=4)
		file.truncate()
	return hash

def download_and_decrypt(uid,file_hash):
	print("downloading.... from ipfs",end='\n')
	with ipfshttpclient.connect() as client:
		client.get(file_hash)
		os.rename(file_hash,f"{uid}_medical_report.json_encrypted")
	print("Copied to local storage")
	print("Verifying signature of the file")
	print("Verification status : ",encryp.sign_verification(uid,f"{uid}_medical_report.json_encrypted"))



'''id=576776585
get_details(id)
encryp.gen_keypair(id)
encryp.encrypt_file(id,f"{id}_medical_report.json")
encryp.decrypt_file(id,f"{id}_medical_report.json")
sign=encryp.digital_sign(id,f"{id}_medical_report.json_encrypted")
hash=upload_ipfs(id,f"{id}_medical_report.json_encrypted")
download_and_decrypt(id,hash)'''
