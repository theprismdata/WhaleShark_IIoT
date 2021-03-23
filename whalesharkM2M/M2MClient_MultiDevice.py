# -*- coding: utf-8 -*-

import json
import socket
import time
from datetime import datetime
import os
import sys
import minimalmodbus
import serial
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
from datautil.hexconversion import str2hex, int2hex
from config.info_reader import read_controller
from pyModbusTCP.client import ModbusClient


agent_host = 'localhost'
agent_port = 1244
device_path = 'config/controllerinfo.csv'

def get_serialresource(port, slaveaddr, mode, baudrate):
    """
    시스템에 연결된 직렬 포트 정보를 할당받아 리턴한다.<br>
    Allocates and returns serial port information connected to the system.
    """
    try:
        instrument = minimalmodbus.Instrument(port, slaveaddr)
        instrument.serial.baudrate = baudrate  # Baud
        instrument.serial.bytesize = 8
        instrument.serial.parity = serial.PARITY_NONE
        instrument.serial.stopbits = 2
        instrument.serial.timeout = 1  # seconds
        instrument.mode = mode
        return instrument
    except Exception as e:
        return None

def get_tcpresource(host, port):
    """
    시스템에 연결된 직렬 포트 정보를 할당받아 리턴한다.<br>
    Allocates and returns serial port information connected to the system.
    """
    try:
        instrument = ModbusClient(host=host, port=port, auto_open=True)
        return instrument
    except Exception as e:
        return None

def get_all_daq_values(instrument_list):
    """
    Scanning all linked daq devices and get values
    """
    device_status = dict()
    for daq_key in instrument_list.keys():
        try:
            instrument = instrument_list[daq_key]
            if instrument is None: continue

            contype = instrument[0]
            conn_obj = instrument[1]
            if contype == 'TCP':
                device_res = instrument[2]
                sensor_map = device_res['meta']
                meta_map = dict()
                for s_key, chan_info in sensor_map.items():
                    nm = chan_info['sensor_nm']
                    dtype = chan_info['datatype']
                    memaddress = int(chan_info['maddress'])
                    size = int(chan_info['datasize'])
                    precision = int(chan_info['precision'])
                    stationid = chan_info['stationid']
                    funname = chan_info['funnm']
                    value = 0
                    values = conn_obj.read_input_registers(memaddress, size)
                    for v in values:
                        value += v
                    meta_map[s_key] = (nm, dtype, value, precision, stationid, funname)
                device_status[device_res['equipnm']+device_res['equipid']] = meta_map
            return device_status

        except IOError:
            print("Failed to read from instrument")


if __name__ == '__main__':
    import json
    instrument_list = {}
    ctrinfo_df = read_controller(filepath=device_path)
    try:
        for index, row in ctrinfo_df.iterrows():
            #CONNTION ID 중복 체크
            connnectionid = row['CONID']
            if connnectionid not in instrument_list:
                instrument_list[connnectionid] = None
                conn = 'None'
                if row['CONTYPE'] == 'RS485':
                    conn = get_serialresource(port=row['CONID'],
                                              slaveaddr=row['STATIONID'],
                                              mode=row['MODE'],
                                              baudrate=row['BAUDRATE'])
                    resource_map = None
                if row['CONTYPE'] == 'TCP':
                    address = row['CONID'].split(':')[0]
                    daq_port = row['CONID'].split(':')[1]
                    conn = get_tcpresource(host=address, port=daq_port)
                    sensor_map = dict()
                    ctrinfo_df = ctrinfo_df[ctrinfo_df.CONTYPE == 'TCP']
                    equip_list = ctrinfo_df['EQUIPID'].unique().tolist()
                    for equip_idnm in equip_list:
                        equip_nm = equip_idnm[:2]
                        equip_id = equip_idnm[2:]
                        sensorlist = ctrinfo_df[(ctrinfo_df.EQUIPID == equip_idnm)]['SENSOR_CODE'].tolist()
                        for scd in sensorlist:
                            nm = ctrinfo_df[(ctrinfo_df.SENSOR_CODE == scd)]['SENSOR_NAME'].to_list()[0]
                            dtype = ctrinfo_df[(ctrinfo_df.SENSOR_CODE == scd)]['DATATYPE'].to_list()[0]
                            memaddress = ctrinfo_df[(ctrinfo_df.SENSOR_CODE == scd)]['ADDRESS'].to_list()[0]
                            size = ctrinfo_df[(ctrinfo_df.SENSOR_CODE == scd)]['BYTES'].to_list()[0]
                            precision = ctrinfo_df[(ctrinfo_df.SENSOR_CODE == scd)]['FLOATPOINT'].to_list()[0]
                            equipid = ctrinfo_df[(ctrinfo_df.SENSOR_CODE == scd)]['EQUIPID'].to_list()[0]
                            stationid = ctrinfo_df[(ctrinfo_df.SENSOR_CODE == scd)]['STATIONID'].to_list()[0]
                            funname = ctrinfo_df[(ctrinfo_df.SENSOR_CODE == scd)]['FUNCTION'].to_list()[0]
                            sensor_map[scd]={'sensor_nm':nm,
                                             'datatype':dtype,
                                             'maddress':memaddress,
                                             'datasize':size,
                                             'precision':int(precision),
                                             'stationid':stationid,
                                             'funnm':funname
                                             }
                        resource_map = (row['CONTYPE'], conn, {'equipnm': equip_nm,
                                                               'equipid': equip_id,
                                                               'meta': sensor_map})
                if conn != None:
                    instrument_list[connnectionid] = resource_map
                    print('장비 연결 {} {}'.format(connnectionid, (row['CONTYPE'], resource_map)))
                else:
                    instrument_list.pop(connnectionid)

        if len(instrument_list) > 0:
            print(instrument_list)
    except Exception as e:
        print('Serial Device connection failed {er}'.format(er=e))
        print('Run on simulation mode')
    try_cnt = 0
    while True:
        try:
            daq_socket = socket.socket()
            daq_socket.connect((agent_host, agent_port))
            break
        except Exception as e:
            print('DAQ SERVER 연동 오류', e)
            time.sleep(1)
            try_cnt += 1
        if try_cnt > 10:
            sys.exit()

    while True:
        if len(instrument_list) > 0:
            try:
                device_status_dict = get_all_daq_values(instrument_list)
                for equip_idnm, meta in device_status_dict.items():
                    status = 'success'
                    stx = hex(2)
                    now = datetime.now()
                    str_time = '%d%d%d%d%d%d%d' % (
                        now.year, now.month, now.day, now.hour, now.minute, now.second, now.microsecond / 1000)
                    int_time = int(str_time)
                    now_time = hex(int_time).replace('0x', '')
                    equip_nm = equip_idnm[:2]
                    equip_id = int(equip_idnm[2:])
                    equiphex = str2hex(equip_nm) + str2hex('%04d' % (equip_id))
                    meta = list()
                    packet_body = dict()
                    packet_body['equipmentid'] = equiphex
                    # data += json.dumps({'equipmentid': equiphex})
                    for scd, value in device_status_dict[equip_idnm].items():
                        sensor_meta = dict()
                        sensor_meta['sensor_cd'] = str2hex('%04d'%(scd))
                        sensor_meta['fun_cd'] = str2hex(value[0])
                        sensor_meta['sensor_value'] = int2hex(value[2])
                        sensor_meta['decimal_point'] = int2hex(value[3])
                        meta.append(json.dumps(sensor_meta))

                    packet_body['pub_time'] = now_time
                    packet_body['meta'] = meta
                    body = json.dumps(packet_body)
                    body = body.replace('\\','').replace('"{','{').replace('}"','}')
                    etx = hex(3)
                    data_len = len(stx) + len(body) + len(etx)
                    print('data len', int2hex(data_len))
                    data = stx + int2hex(data_len) + body +etx
                    print(len(data), data)
                    try:
                        while True:
                            if 'success' in status:
                                daq_socket.sendall(bytes(data, encoding='utf-8'))
                                recv = daq_socket.recv(len(data)+10)
                                status = recv.decode()[:7]
                                print('rtn', status)
                                break

                        time.sleep(0.3)
                    except Exception as e:
                        print(e)
                        daq_socket = socket.socket()
                        daq_socket.connect((agent_host, agent_port))

            except Exception as e:
                print(e)
        else: #test mode
            try:
                for index, row in ctrinfo_df.iterrows():
                    sensor_id = '%04d'%(row['SENSOR_CODE'])
                    station_class = 'HM'
                    station_id = '%04d' % (1)
                    fun_cd = row['FUNCTION']
                    now = datetime.now()
                    str_time = '%d%d%d%d%d%d%d' % (
                        now.year, now.month, now.day, now.hour, now.minute, now.second, now.microsecond / 1000)
                    int_time = int(str_time)
                    now_time = hex(int_time).replace('0x', '')
                    status_dict = {}
                    status_dict['sensor_cd'] = str2hex(sensor_id)
                    status_dict['fun_cd'] = str2hex(fun_cd)
                    status_dict['sensor_value'] = int2hex(202)
                    status_dict['decimal_point'] = int2hex(1)
                    status_dict['pub_time'] = now_time
                    measured_dict = {'equipmentid': str2hex(station_class)+str2hex(station_id),
                        'meta': status_dict}
                    data = hex(2)+json.dumps(measured_dict) + hex(3)
                    print(data)
                    daq_socket.sendall(bytes(data, encoding='utf-8'))
                    recv = daq_socket.recv()
                    print(recv)
                    time.sleep(1)
            except Exception as e:
                print(e)

