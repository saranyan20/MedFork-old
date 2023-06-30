from ipld import marshal, multihash, unmarshal
import ipfshttpclient
obj1 = { "name.txt": "nandu.txt " }
obj1Data = marshal(obj1)
obj1Hash = multihash(obj1Data)
obj2 = { "files":[{"/": obj1Hash },]}
obj2Data = marshal(obj2)
obj2Hash = multihash(obj2Data)
with ipfshttpclient.connect() as client:
    print(client.add(obj1)['Hash'])
    print(client.add(obj2)['Hash'])
