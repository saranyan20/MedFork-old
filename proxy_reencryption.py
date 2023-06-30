import random
import umbral
from umbral import pre, keys, config, signing


umbral.config.set_default_curve()
alices_private_key = keys.UmbralPrivateKey.gen_key()
alices_public_key = alices_private_key.get_pubkey()
print('alice key',alices_public_key)
alices_signing_key = keys.UmbralPrivateKey.gen_key()
alices_verifying_key = alices_signing_key.get_pubkey()
alices_signer = signing.Signer(private_key=alices_signing_key)
plaintext = b'EHR using Blockchain'
ciphertext, capsule = pre.encrypt(alices_public_key, plaintext)
print("The encrypted text ",ciphertext,end="\n\n")
cleartext = pre.decrypt(ciphertext=ciphertext,
                        capsule=capsule,
                        decrypting_key=alices_private_key)
print("The text decrypted by Alice ",cleartext,end="\n\n")
bobs_private_key = keys.UmbralPrivateKey.gen_key()
bobs_public_key = bobs_private_key.get_pubkey()
bob_capsule = capsule
try:
    fail_decrypted_data = pre.decrypt(ciphertext=ciphertext,
                                      capsule=bob_capsule,
                                      decrypting_key=bobs_private_key)
except pre.UmbralDecryptionError:
    print("Decryption failed! Bob doesn't has access granted yet.",end="\n\n")
kfrags = pre.generate_kfrags(delegating_privkey=alices_private_key,
                             signer=alices_signer,
                             receiving_pubkey=bobs_public_key,
                             threshold=10,
                             N=20)
print("the type",type(kfrags[0]))
print("The key fragments ",kfrags,end="\n\n")

import random
kfrags = random.sample(kfrags,10)
bob_capsule.set_correctness_keys(delegating=alices_public_key,
                                 receiving=bobs_public_key,
                                 verifying=alices_verifying_key)

print("Bob collecting the keyfragment from proxies",end="\n\n")

cfrags = list()
for kfrag in kfrags:
    cfrag = pre.reencrypt(kfrag=kfrag, capsule=bob_capsule)
    cfrags.append(cfrag)
for cfrag in cfrags:
    bob_capsule.attach_cfrag(cfrag)
print("Bob decrypting...",end="\n\n")
bob_cleartext = pre.decrypt(ciphertext=ciphertext, capsule=bob_capsule, decrypting_key=bobs_private_key)
print("The original text ",bob_cleartext)
