from npre import bbs98
pre = bbs98.PRE()
sk_a = pre.gen_priv(dtype=bytes)
pk_a = pre.priv2pub(sk_a)
pk_b = pre.priv2pub(sk_b)
msg = b"Hello world"
emsg = pre.encrypt(pk_a, msg)
print(pre.decrypt(sk_a, emsg))
