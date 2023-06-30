from json_check import json_file_check
import json
import encryp
import ipfshttpclient
import umbral
from umbral import pre, keys, config, signing
from umbral.curve import Curve, SECP256K1
import encryp
import base64
from umbral.params import UmbralParameters

def verification(uid,public_key,public_key_digitalsign):#signs on hash of the public key and sends itself for verification
    #return encryp.sign_verification(uid,public_key_digitalsign,text_data=public_key)
    return True


def new_policy(s_uid,r_uid,data_hash,public_key_digitalsign,capsule,remove):
    with open(f"{s_uid}_public_key.pem", "rb") as key_file:
        data_owner = key_file.read()
        data_owner = keys.UmbralPublicKey.from_bytes(data_owner)
    with open(f"{r_uid}_public_key.pem", "rb") as key_file:
        reciever = key_file.read()
        reciever = keys.UmbralPublicKey.from_bytes(reciever)
    status=verification(s_uid,public_key_digitalsign,data_owner)
    if status:
        if not json_file_check("data_sharing_policies.json"):
            with open("data_sharing_policies.json",'w') as file:
                dummy={
                       'policies':[]
                }
                json.dump(dummy,file)
        with open("data_sharing_policies.json",'r+') as file:
            data=json.load(file)
            print("Modifying ploicies",end='\n')
            if not int(remove):
                new_data={
                          'Sender_UID':s_uid,
                          'Reciever_UID':r_uid,
                          'data_owner':encryp.base64encode(data_owner.to_bytes()),
                          'reciever':encryp.base64encode(reciever.to_bytes()),
                          'shared_data':data_hash,
                          'capsule':capsule
                }
                data['policies'].append(new_data)
            else:
                values=data['policies']
                for i in values:
                    if i['Sender_UID']==s_uid and i['Reciever_UID']==r_uid and i['shared_data']==data_hash:
                        values.remove(i)
                        break
                else:
                    print("The requested policy cannot be found..!")
                data['policies']=values
            file.seek(0)
            json.dump(data,file,indent=4)
            file.truncate()
    else:
        print("Sorry! Verification failed...Retry")

def re_encrypt(s_uid,r_uid,public_key_digitalsign):
    try:
        with open(f"{s_uid}_public_key.pem", "rb") as key_file:
            data_owner = key_file.read()
            data_owner = keys.UmbralPublicKey.from_bytes(data_owner)
        with open(f"{r_uid}_public_key.pem", "rb") as key_file:
            reciever = key_file.read()
            reciever = keys.UmbralPublicKey.from_bytes(reciever)
    except:
        print("No policy has been written for your UID")
        return
    status=verification(r_uid,public_key_digitalsign,reciever)
    if status:
        with open("data_sharing_policies.json",'r') as file:
            print("in share")
            data=json.load(file)
            values=data['policies']
            for i in values:
                if i['Sender_UID']==s_uid and i['Reciever_UID']==r_uid:
                    file_hash=i['shared_data']
                    capsule=i['capsule']
                    break
            else:
                print("Policy not found !")
                return
    with ipfshttpclient.connect() as client:
        client.get(file_hash)
    with open(f"{s_uid}_private_key.pem", "rb") as key_file:
        sender_private_key = key_file.read()
        sender_private_key = keys.UmbralPrivateKey.from_bytes(sender_private_key)
        signer = signing.Signer(private_key=sender_private_key)
    with open(f"{r_uid}_private_key.pem", "rb") as key_file:
        reciever_private_key = key_file.read()
        reciever_private_key = keys.UmbralPrivateKey.from_bytes(reciever_private_key)
    kfrags = pre.generate_kfrags(delegating_privkey=sender_private_key,
                                 signer=signer,
                                 receiving_pubkey=reciever,
                                 threshold=10,
                                 N=20)
    '''with open(file_hash,'wb') as file:
        file.write(kfrags.to_bytes())
    with open(filename,'rb') as file:
        kfrags=umbral.kfrags.Kfrag.from_bytes(file.read())'''
    cfrags = list()
    new_capsule=pre.Capsule.from_bytes(base64.b64decode(capsule.encode()),UmbralParameters(SECP256K1))
    new_capsule.set_correctness_keys(delegating=data_owner,
                                     receiving=reciever,
                                     verifying=data_owner)
    for kfrag in kfrags:
        cfrag = pre.reencrypt(kfrag=kfrag, capsule=new_capsule)
        cfrags.append(cfrag)
    for cfrag in cfrags:
        new_capsule.attach_cfrag(cfrag)
    with open(file_hash,'rb') as file:
        ciphertext=file.read()
    return pre.decrypt(ciphertext=ciphertext, capsule=new_capsule, decrypting_key=reciever_private_key)#.decode()


'''encryp.gen_keypair("nanda5")
encryp.gen_keypair("nanda10")
cap=encryp.encrypt_file("nanda5","test.txt")
with ipfshttpclient.connect() as client:
    print("uploading.... to ipfs",end='\n')
    hash = client.add("test.txt_encrypted")['Hash']
new_policy("nanda5","nanda10",hash,"pubsign",cap,'0')
re_encrypt("nanda5","nanda10","pubsign")'''
