import socket
import time
import minimalmodbus
import serial
import pandas as pd

client_socket = socket.socket()
host = 'localhost'
port = 1233

def read_controller(filepath):
    try:
        controller_df = pd.read_csv(filepath)
        return controller_df
    except Exception as e:
        print(e)

def get_serialinterface(port, slaveaddr, mode, baudrate):
    instrument = minimalmodbus.Instrument(port, slaveaddr)
    instrument.serial.baudrate = baudrate  # Baud
    instrument.serial.bytesize = 8
    instrument.serial.parity = serial.PARITY_NONE
    instrument.serial.stopbits = 2
    instrument.serial.timeout = 1  # seconds
    instrument.mode = mode
    return instrument
    
if __name__ == '__main__':
    instrument_list = []
    accessinfo_df = read_controller(filepath='controllerinfo.csv')
    fun_length = accessinfo_df.shape[0]
    for index, row in accessinfo_df.iterrows():
        conn = get_serialinterface(port='/dev/tty.usbserial-AQ00WOQH',
                                   slaveaddr=row['STATIONID'],
                                   mode=row['MODE'],
                                   baudrate=row['BAUDRATE'])
        acces_info ={'conn':conn,'address':row['ADDRESS']}
        instrument_list.append(acces_info)
        
    while True:
        for instrument in instrument_list:
            try:
                conn = instrument['conn']
                address = instrument['address']
                print(address)
                print(conn.read_register(int(address, 16), 0, functioncode=int('0x04', 16)))
                time.sleep(1)
            except IOError:
                print("Failed to read from instrument")