from Crypto.PublicKey import RSA
from Crypto import Random
from Crypto.Hash import SHA256
import os,json,ast

def check_key_presence(uid):
    if os.path.isfile(f"./{uid}_pubkey"):
        print (f"{uid} key pair exists and is readable")
        return True
    else: return False

def gen_keypair(uid):
    if not check_key_presence(uid):
        random_generator = Random.new().read
        key = RSA.generate(1024, random_generator)
        with open(f"{uid}_pubkey","wb") as f:
            f.write(key.publickey().exportKey())
        with open(f"{uid}_privkey","wb") as f:
            f.write(key.exportKey())

def encrypt_file(uid, filename):
    with open(f"{uid}_pubkey","rb") as f:
        publickey=RSA.importKey(f.read())
    with open(filename,'r') as f:
        data=f.read()
    encrypdata=publickey.encrypt(data.encode(),32)
    with open(filename+'_encrypted','w') as f:
        f.write(encrypdata[0].encode())

def decrypt_file(uid, filename):
    with open(f"{uid}_privkey","rb") as f:
        privatekey=RSA.importKey(f.read())
    with open(filename+'_encrypted','r') as f:
        data=privatekey.decrypt(f.read())
        data = data.decode('unicode_escape').encode('utf-8')
    with open(filename,'wb') as f:
        f.write(data)

def digital_sign(uid,filename):
    with open(f"{uid}_privkey",'rb') as f:
        privatekey=RSA.importKey(f.read())
    with open(filename,'rb') as f:
        data=f.read()
    hash = SHA256.new(data).digest()
    signature = privatekey.sign(hash, '')
    return signature[0]

def sign_verification(uid,filename):
    with open(f"{uid}_pubkey") as f:
        publickey=RSA.importKey(f.read())
    with open(f"{uid}_privkey") as f:
        privatekey=RSA.importKey(f.read())
    with open(filename,'rb') as f:
        data=f.read()
    hash = SHA256.new(data).digest()
    signature = privatekey.sign(hash, '')
    return publickey.verify(hash, signature)



'''gen_keypair(7479)
encrypt_file(7479,"nandu")
decrypt_file(7479,"nandu")
print("sign",digital_sign(7479,"nandu"))
print(sign_verification(7479,"nandu"))'''

encrypt_file("nithya1005","323_medical_report.json")
decrypt_file("nithya1005","323_medical_report.json")
