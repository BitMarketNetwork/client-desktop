import random
from .opcodes import OPCODE
from electrumsv_secp256k1 import ffi,lib as secp256k1 

"""
For tests only!!!
"""

def parse_script(script, segwit=True):
    """
    Parse script and return script type, script address and required signatures count.

    :param script: script in bytes string or HEX encoded string format.
    :param segwit:  (optional) If set to True recognize P2WPKH and P2WSH sripts, by default set to True.

    :return: dictionary:

            - nType - numeric script type
            - type  - script type
            - addressHash - address hash in case address recognized
            - script - script if no address recognized
            - reqSigs - required signatures count
    """
    if not script:
        return {"nType": 7, "type": "NON_STANDARD", "reqSigs": 0, "script": b""}
    if isinstance(script, str):
        try:
            script = bytes.fromhex(script)
        except:
            pass
        assert isinstance(script, bytes)
    l = len(script)
    if segwit:
        if l == 22 and script[0] == 0:
            return {"nType": 5, "type": "P2WPKH", "reqSigs": 1, "addressHash": script[2:]}
        if l == 34 and script[0] == 0:
            return {"nType": 6, "type": "P2WSH", "reqSigs": None, "addressHash": script[2:]}
    if l == 25 and \
       script[:2] == b"\x76\xa9" and \
       script[-2:] == b"\x88\xac":
        return {"nType": 0, "type": "P2PKH", "reqSigs": 1, "addressHash": script[3:-2]}
    if l == 23 and \
       script[0] == 169 and \
       script[-1] == 135:
        return {"nType": 1, "type": "P2SH", "reqSigs": None, "addressHash": script[2:-1]}
    if l == 67 and script[-1] == 172:
        return {"nType": 2, "type": "PUBKEY", "reqSigs": 1, "addressHash": hash160(script[1:-1])}
    if l == 35 and script[-1] == 172:
        return {"nType": 2, "type": "PUBKEY", "reqSigs": 1, "addressHash": hash160(script[1:-1])}
    if script[0] == 106 and l > 1 and l <= 82:
        if script[1] == l - 2:
            return {"nType": 3, "type": "NULL_DATA", "reqSigs": 0, "data": script[2:]}
    if script[0] >= 81 and script[0] <= 96:
        if script[-1] == 174:
            if script[-2] >= 81 and script[-2] <= 96:
                if script[-2] >= script[0]:
                    c, s = 0, 1
                    while l - 2 - s > 0:
                        if script[s] < 0x4c:
                            s += script[s]
                            c += 1
                        else:
                            c = 0
                            break
                        s += 1
                    if c == script[-2] - 80:
                        return {"nType": 4, "type": "MULTISIG", "reqSigs": script[0] - 80, "script": script}

    s, m, n, last, req_sigs = 0, 0, 0, 0, 0
    while l - s > 0:
        if script[s] >= 81 and script[s] <= 96:
            if not n:
                n = script[s] - 80
            else:
                if m == 0:
                    n, m = script[s] - 80, 0
                elif n > m:
                    n, m = script[s] - 80, 0
                elif m == script[s] - 80:
                    last = 0 if last else 2
        elif script[s] < 0x4c:
            s += script[s]
            m += 1
            if m > 16:
                n, m = 0, 0
        elif script[s] == OPCODE["OP_PUSHDATA1"]:
            try:
                s += 1 + script[s + 1]
            except:
                break
        elif script[s] == OPCODE["OP_PUSHDATA2"]:
            try:
                s += 2 + struct.unpack('<H', script[s: s + 2])[0]
            except:
                break
        elif script[s] == OPCODE["OP_PUSHDATA4"]:
            try:
                s += 4 + struct.unpack('<L', script[s: s + 4])[0]
            except:
                break
        else:
            if script[s] == OPCODE["OP_CHECKSIG"]:
                req_sigs += 1
            elif script[s] == OPCODE["OP_CHECKSIGVERIFY"]:
                req_sigs += 1
            elif script[s] in (OPCODE["OP_CHECKMULTISIG"], OPCODE["OP_CHECKMULTISIGVERIFY"]):
                if last:
                    req_sigs += n
                else:
                    req_sigs += 20
            n, m = 0, 0
        if last:
            last -= 1
        s += 1
    return {"nType": 7, "type": "NON_STANDARD", "reqSigs": req_sigs, "script": script}


FLAG_SIGN = secp256k1.SECP256K1_CONTEXT_SIGN
FLAG_VERIFY = secp256k1.SECP256K1_CONTEXT_VERIFY
ALL_FLAGS = FLAG_SIGN | FLAG_VERIFY
NO_FLAGS = secp256k1.SECP256K1_CONTEXT_NONE
ECDSA_CONTEXT_SIGN = secp256k1.secp256k1_context_create(FLAG_SIGN)
ECDSA_CONTEXT_VERIFY = secp256k1.secp256k1_context_create(FLAG_VERIFY)
ECDSA_CONTEXT_ALL = secp256k1.secp256k1_context_create(ALL_FLAGS)
ECDSA_SEC256K1_ORDER = 0xfffffffffffffffffffffffffffffffebaaedce6af48a03bbfd25e8cd0364141
secp256k1.secp256k1_context_randomize(ECDSA_CONTEXT_SIGN,
                                      random.SystemRandom().randint(0, ECDSA_SEC256K1_ORDER).to_bytes(32, byteorder="big"))

def verify_signature(sig, pub_key, msg):
    """
    Verify signature for message and given public key

    :param sig: signature in bytes or HEX encoded string.
    :param pub_key:  public key in bytes or HEX encoded string.
    :param msg:  message in bytes or HEX encoded string.
    :return: boolean.
    """
    if not isinstance(sig, bytes):
        if isinstance(sig, bytearray):
            sig = bytes(sig)
        elif isinstance(sig, str):
            sig = bytes.fromhex(sig)
        else:
            raise TypeError("signature must be a bytes or hex encoded string")
    if not isinstance(pub_key, bytes):
        if isinstance(pub_key, bytearray):
            pub_key = bytes(pub_key)
        elif isinstance(pub_key, str):
            pub_key = bytes.fromhex(pub_key)
        else:
            raise TypeError("public key must be a bytes or hex encoded string")
    if not isinstance(msg, bytes):
        if isinstance(msg, bytearray):
            msg = bytes(msg)
        elif isinstance(msg, str):
            msg = bytes.fromhex(msg)
        else:
            raise TypeError("message must be a bytes or hex encoded string")

    raw_sig = ffi.new('secp256k1_ecdsa_signature *')
    raw_pubkey = ffi.new('secp256k1_pubkey *')
    if not secp256k1.secp256k1_ecdsa_signature_parse_der(ECDSA_CONTEXT_VERIFY, raw_sig, sig, len(sig)):
        raise TypeError("signature must be DER encoded")
    if not secp256k1.secp256k1_ec_pubkey_parse(ECDSA_CONTEXT_VERIFY, raw_pubkey, pub_key, len(pub_key)):
        raise TypeError("public key format error")
    result = secp256k1.secp256k1_ecdsa_verify(ECDSA_CONTEXT_VERIFY, raw_sig, msg, raw_pubkey)
    return True if result else False