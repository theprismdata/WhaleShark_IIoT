import minimalmodbus as minimalmodbus
import serial

if __name__ == '__main__':
    instrument = minimalmodbus.Instrument("/dev/tty.usbserial-AQ00WOQH", 1,'rtu')
    instrument.serial.baudrate = 19200  # Baud
    instrument.serial.bytesize = 8
    instrument.serial.parity = serial.PARITY_NONE
    instrument.serial.stopbits = 2
    instrument.serial.timeout = 1  # seconds
    try:
        #read pv from Inut Regiseters
        #Address 301001(03E8)
        print(instrument.read_register(0x03E8, 0,  functioncode=int('0x04', 16)))
    except IOError:
        print("Failed to read from instrument")
