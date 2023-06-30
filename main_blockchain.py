from blockchain import Blockchain
from flask import Flask, jsonify, request
from uuid import uuid4
import hashlib,json
import json,pickle,random
import ipfs_integration as ipfs
import encryp
import ipfs_versioning as ipfsver
import ipfshttpclient
import datetime
import base64
import data_sharing_helpers as share
from umbral import keys
from config import *
# Add new terms from stage 0.2
app = Flask(__name__)
node_identifier = str(uuid4()).replace('-', '')
blockchain = Blockchain()
uid="230"
duid="223"+"_doc"

@app.route('/init', methods=['GET'])
def key_gen():
    global uid,duid
    uid=input("Enter you Uinque Identifier (UUID) :")
    ipfs.get_details(uid)
    encryp.gen_keypair(uid)
    verify={
        "status":"success",
        "message":"Key pair has been generated successfully"
    }
    duid=input("Enter Doctor's Uinque Identifier (UUID)")+"_doc"
    encryp.gen_keypair(duid)
    return jsonify(verify)

@app.route('/transactions/new', methods=['GET','POST'])
def new_transaction():
    global uid,duid
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
    if(encryp.sign_verification(duid,base64.b64decode(digital_sign_doctor.encode()),text_data=ipfs_file_hash) and
       (encryp.sign_verification(uid,base64.b64decode(digital_sign_patient.encode()),text_data=ipfs_file_hash))): #even if one can able to fake this Verification, during mining other nodes will verify and rule out the transaction
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
        return jsonify(response), 201
    else:
        return jsonify({'message': f'This is not a vaild transaction'})

@app.route('/version/holder', methods=['GET','POST'])
def view_version_holder():
    print("checking version holder data")
    values=request.get_json()
    uid=values["uid"]
    with open("ipns_hash_indices.json",'r') as file:
        ipns_hash=json.load(file)[uid]
        with ipfshttpclient.connect() as client:
            holder_file_hash=client.name.resolve(ipns_hash)['Path'].lstrip("/ipfs/")
            client.get(holder_file_hash)
            with open(holder_file_hash,'r') as file:
                res=json.load(file)
    return jsonify(res)

@app.route('/update/data', methods=['GET','POST'])
def update_data():
    global uid,duid
    uid=request.get_json()["uid"]
    print("Update(medical report) request")
    new_file_hash,ipns_hash=ipfsver.ipfs_version_holder_updater(uid)
    with open(f'{uid}_public_key.pem','rb') as f:
        public_key_patient=keys.UmbralPublicKey.from_bytes(f.read())
    with open(f'{duid}_public_key.pem','rb') as f:
        public_key_doctor=keys.UmbralPublicKey.from_bytes(f.read())
    digital_sign_doctor=encryp.digital_sign(duid,text_data=new_file_hash)
    digital_sign_patient=encryp.digital_sign(uid,text_data=new_file_hash)
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
    return jsonify(response), 201


@app.route('/mine', methods=['GET'])
def mine():
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
    return jsonify(response), 200


@app.route('/share/new_policy', methods=['GET','POST'])
def share_data():
    values=request.get_json()
    s_uid=values['s_uid']
    r_uid=values['r_uid']
    data_hash=values['data_hash']
    public_key_digitalsign=values['public_key_digitalsign']
    capsule=values['capsule']
    remove=values['remove']
    share.new_policy(s_uid,r_uid,data_hash,public_key_digitalsign,capsule,remove)
    response={'status':"success","message":"New policy has been added !"}
    return jsonify(response), 200

@app.route('/view_policy', methods=['GET'])
def share_datas():
    with open("data_sharing_policies.json",'r+') as file:
        response=json.load(file)
    return jsonify(response), 200


@app.route('/re_encrypt', methods=['GET','POST'])
def re_encrypt():
    values=request.get_json()
    s_uid=values['s_uid']
    r_uid=values['r_uid']
    public_key_digitalsign=values['public_key_digitalsign']
    response=share.re_encrypt(s_uid,r_uid,public_key_digitalsign)
    return jsonify(response), 200


@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200


@app.route('/check/data', methods=['POST','GET'])
def check_patient_data():
    values = request.get_json()
    request_patient = values.get('uid')
    data_blocks=[]
    for blocks in blockchain.chain[::-1]:
        idx=blocks["index"]
        trans=blocks["transactions"]
        for i in trans:
            if i["UUID"]==request_patient:
                data_blocks.append(idx)
                continue
    if data_blocks:
        result={"message":"the requested patient details found in the following blocks","Block_indices":data_blocks}
    else:
        result={"message":"the requested patient details cannot be found"}
    return jsonify(result)



@app.route('/block/explorer', methods=['POST','GET'])
def block_explorer():
    values = request.get_json()
    index = values.get('block')
    print(index)
    for blocks in blockchain.chain:
        if blocks["index"]==int(index):
            print("Yes")
            response=blocks
            break
    else:
        response={"status":"failed","message":"Invalid block index"}
    return jsonify(response)


@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    values = request.get_json()

    nodes = values.get('nodes')
    if nodes is None:
        return "Error: Please supply a valid list of nodes", 400

    for node in nodes:
        blockchain.register_node(node)

    response = {
        'message': 'New nodes have been added',
        'total_nodes': list(blockchain.nodes),
    }
    return jsonify(response), 201


@app.route('/retrive/latest', methods=['POST'])
def retrives_latest():
    values = request.get_json()
    patient_id = values["uid"]
    try:
        ipfsver.retrive_lastest(patient_id)
        with open(f"{uid}_medical_report.json","r") as file:
            data=json.load(file)
        return jsonify(data)
    except:
        return jsonify({"message":"Invalid UID "})

@app.route('/nodes/resolve', methods=['GET'])
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

    return jsonify(response), 200

@app.errorhandler(404)
def not_found(e):
    return jsonify({"message":"Sorry! Invlaid page"})


if __name__ == '__main__':
    port=input("Enter port no : ")
    app.run(host='127.0.0.1', port=port)
