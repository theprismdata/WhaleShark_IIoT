import binascii


def str2hex(arg_str):
    '''
    문자열을 16진수로 변환하려 리턴한다.
    변환된 16진수는 바이트 타입에서 스트링으로 변환된다.
    '''
    fun_id = arg_str.encode('ASCII')
    hex_fun_id = binascii.hexlify(fun_id)#return byte type
    hex_fun_id = hex_fun_id.decode('ASCII')
    return hex_fun_id

def hex2str(arg_hex):
    '''
    16진수를 ASCII문자열로 변환하여 리턴한다.
    '''
    #Hex to String
    fun_id_byte = bytes.fromhex(arg_hex)
    fun_id_str = fun_id_byte.decode('ASCII')
    return fun_id_str

def int2hex(arg_int):
    '''
    정수를 16진수로 변환하려 리턴한다.
    '''
    return hex(arg_int)

def hex2int(arg_hex):
    '''
    16진수를 정수로 변환하여 리턴한다.
    '''
    return int(arg_hex, 16)