import json
import ipfshttpclient
uid = "2"
with open("ipns_hash_indices.json",'r') as file:
	ipns_hash=json.load(file)[uid]
	print(ipns_hash)
	with ipfshttpclient.connect() as client:
		holder_file_hash=client.name.resolve(ipns_hash)['Path'].lstrip("/ipfs/")
		client.get(holder_file_hash)
		with open(holder_file_hash,'r') as file:
			res=json.load(file)
print(res)