
SEQUENCE = 0xffffffff.to_bytes(4, byteorder='little')
VERSION_1 = 0x01.to_bytes(4, byteorder='little')
VERSION_2 = 0x02.to_bytes(4, byteorder='little')
LOCK_TIME = 0x00.to_bytes(4, byteorder='little')
HASH_TYPE = 0x01.to_bytes(4, byteorder='little')
WIT_MARKER = b'\x00'
WIT_FLAG = b'\x01'
MESSAGE_LIMIT = 80

OP_0 = b'\x00'
OP_PUSH_32 = b'\x20'
