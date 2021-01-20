
SEQUENCE = 0xffffffff.to_bytes(4, byteorder='little')
VERSION_1 = 0x01.to_bytes(4, byteorder='little')
VERSION_2 = 0x02.to_bytes(4, byteorder='little')
LOCK_TIME = 0x00.to_bytes(4, byteorder='little')
HASH_TYPE = 0x01.to_bytes(4, byteorder='little')
WIT_MARKER = b'\x00'
WIT_FLAG = b'\x01'
MESSAGE_LIMIT = 80

# Scripts:
OP_0 = b'\x00'
OP_CHECKLOCKTIMEVERIFY = b'\xb1'
OP_CHECKSIG = b'\xac'
OP_CHECKMULTISIG = b'\xae'
OP_DUP = b'v'
OP_EQUALVERIFY = b'\x88'
OP_HASH160 = b'\xa9'
OP_PUSH_20 = b'\x14'
OP_PUSH_32 = b'\x20'
OP_RETURN = b'\x6a'
OP_EQUAL = b'\x87'

PRIVATE_KEY_COMPRESSED_PUBKEY = b'\x01'
