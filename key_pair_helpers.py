import hashlib,json
#from Crypto.Hash import SHA256
#from Crypto.PublicKey import RSA
import pickle
class MerkTree:
	def __init__(self,listofdata=None):
		self.listofdata = listofdata
		self.past_transaction = {}

	def create_tree(self):
		listofdata = self.listofdata
		past_transaction = self.past_transaction
		temp_transaction = []
		for index in range(0,len(listofdata),2):
			current = listofdata[index]
			if index+1 != len(listofdata):
				current_right = listofdata[index+1]
			else:
				current_right = ''
			current_hash = hashlib.sha256(str(current).encode('utf-8'))
			if current_right != '':
				current_right_hash = hashlib.sha256(str(current_right).encode('utf-8'))
			past_transaction[listofdata[index]] = current_hash.hexdigest()
			if current_right != '':
				past_transaction[listofdata[index+1]] = current_right_hash.hexdigest()
			if current_right != '':
				temp_transaction.append(current_hash.hexdigest() + current_right_hash.hexdigest())
			else:
				temp_transaction.append(current_hash.hexdigest())
		if len(listofdata) != 1:
			self.listofdata = temp_transaction
			self.past_transaction = past_transaction
			self.create_tree()

	def Get_past_transacion(self):
		return self.past_transaction

	def Get_Root_leaf(self):
		last_key = list(self.past_transaction.keys())[-1]
		return dict(root_hash=self.past_transaction[last_key])

#if __name__ == "__main__":
name=""
class Key:
	def main_function(self):
		global name
		print ("merkle tree")
		kyc = MerkTree()
		user_details = []
		name=input("Name : ")
		age=int(input("Age : "))
		uuid=int(input("UUID : "))
		city=input("City : ")
		nation=input("Nation : ")
		user_details.append(name)
		user_details.append(age)
		user_details.append(uuid)
		user_details.append(city)
		user_details.append(nation)
		kyc.listofdata = user_details
		kyc.create_tree()
		all_details_hash = kyc.Get_past_transacion()
		root_hash = kyc.Get_Root_leaf()
		'''print(all_details_hash)
		for k, v in all_details_hash.items():
			print(f"{k} : {v}")
		print(f"root hash : {root_hash}")
		print(json.dumps(all_details_hash, indent=4))
		print(f"root hash -- > {json.dumps(root_hash)}")'''
		with open("all_details_hash.json",'w') as file:
			json.dump(all_details_hash, file,indent=4)
		with open("root_hash.json",'w') as file:
			json.dump(root_hash, file,indent=4)
		return root_hash, json.dumps(all_details_hash,indent=1)

	def govt_key_pair(self):
	    key = RSA.generate(2048)
	    public = key.publickey()
	    private = key.exportKey()
	    with open("govt_key_pair.txt",'w') as file:
	        file.write(f"public_key : {public.exportKey()}")
	        file.write(f"private_key : {private.decode()}")
	    with open(f"govt_public_key.obj","wb") as file:
	        pickle.dump(public,file)
	    with open(f"govt_key.obj","wb") as file:
	        pickle.dump(key,file)


	def public_key_pair(self):
	    key = RSA.generate(2048)
	    public = key.publickey()
	    private = key.exportKey()
	    with open("user_public_key_pair.txt",'w') as file:
	        file.write(f"public_key : {public.exportKey()}")
	        file.write(f"private_key : {private.decode()}")
	    with open("user_public_key.obj","wb") as file:
	        pickle.dump(public,file)
	    with open("user_key.obj","wb") as file:
	        pickle.dump(key,file)

	def sign(self, data):
	    text = data.encode()
	    hash = SHA256.new(text).digest()
	    with open("govt_key.obj","rb") as obj:
	        key=pickle.load(obj)
	    signature = key.sign(hash, '')
	    return signature

	def verify(self, signature, data):
	    with open("govt_public_key.obj","rb") as file:
	        public_key=pickle.load(file)
	    text = data.encode()
	    hash = SHA256.new(text).digest()
	    return public_key.verify(hash, signature)
