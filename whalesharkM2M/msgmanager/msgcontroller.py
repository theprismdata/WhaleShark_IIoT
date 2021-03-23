import logging
import sys
import math
import json
import time
from datetime import datetime
import pika
from .signalkiller import GracefulInterruptHandler
from ..config.info_reader import read_deviceinfo, device_path
from ..datautil.hexconversion import hex2str, hex2int

"""
   MSGController module
   ~~~~~~~~~~~~~~~~~~~~~

"""


class MSGController(object):
    
    def __init__(self, redis_manager):
        logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s', stream=sys.stdout, level=logging.DEBUG,
                            datefmt='%Y-%m-%d %H:%M:%S')
        # self.mongo_mgr = mongo_manager.MongoMgr()
        self.redis_mgr = redis_manager
    
    def init_facilities_info(self, redis_con):
        self.device_key, self.deviceinfo = read_deviceinfo(device_path)
        redis_con.set(self.device_key, json.dumps(self.deviceinfo))
    
    def get_fac_inf(self, redis_con):
        fac_daq = {}

        self.device_key, self.deviceinfo = read_deviceinfo(device_path)
        facilities_binary = redis_con.get(self.device_key)
        if facilities_binary is None:
            self.init_facilities_info(redis_con)
        
        facilities_decoded = facilities_binary.decode()
        facilities_info = json.loads(facilities_decoded)
        print('fac_info', self.device_key, facilities_info)
        equipment_keys = facilities_info.keys()
        for equipment_key in equipment_keys:
            fac_daq[equipment_key] = {}
            for sensor_id in facilities_info[equipment_key].keys():
                sensor_desc = facilities_info[equipment_key][sensor_id]
                if sensor_desc not in fac_daq[equipment_key].keys():
                    fac_daq[equipment_key][sensor_desc] = 0.0
        return fac_daq
    
    def config_fac_msg(self, equipment_id, fac_daq, sensors_meta, redis_fac_info):
        for sensor_meta in sensors_meta:
            sensor_code = sensor_meta['sensor_cd']
            if sensor_code in redis_fac_info[equipment_id].keys():
                sensor_desc = redis_fac_info[equipment_id][sensor_code]
                sensor_value = sensor_meta['sensor_value']
                decimal_point = sensor_meta['decimal_point']
                pv = float(sensor_value)
                decimal_point = math.pow(10, float(decimal_point))
                fac_daq[equipment_id][sensor_desc] = pv / decimal_point
                logging.debug('{eid} {sd} : {pv}'.format(eid = equipment_id, sd = sensor_desc, pv = fac_daq[equipment_id][sensor_desc]))

        fac_msg = json.dumps({equipment_id: fac_daq[equipment_id]})
        return 'success', fac_msg
    
    def publish_facility_msg(self, mqtt_info, routing_key, json_body):
        """json형식의 센서 데이터를 RabbitMQ Broker로 전송
        """
        try:
            logging.debug('channel is open:' + str(mqtt_info['channel'].is_open))
            if mqtt_info['channel'].is_open is False:
                credentials = pika.PlainCredentials('whaleshark', 'whaleshark')
                param = pika.ConnectionParameters('localhost', 5672, '/', credentials)
                connection = pika.BlockingConnection(param)
                mqtt_info['channel'] = connection.channel()
                mqtt_info['channel'].queue_declare(queue=mqtt_info['exchange'])
                mqtt_info['channel'].exchange_declare(exchange=mqtt_info['exchange'], exchange_type=mqtt_info['exchange_type'])
            
            mqtt_info['channel'].basic_publish(exchange=mqtt_info['exchange'], routing_key=routing_key, body=json_body)
            logging.debug('mqtt publish {ename} {rk} {jb}'.format(ename=mqtt_info['exchange'], rk = routing_key, jb = json_body))
            return mqtt_info['channel'], json.loads(json_body)
        
        except Exception as e:
            logging.exception(str(e))
            return {'Status': str(e)}

    def convert_jsonhex(self, packet_bytes, host, port, mqtt_valid=True):
        etx_idx = packet_bytes.find(hex(3))
        status = 'ER'
        try:
            modbus_msg = dict()

            datasize = hex2int(packet_bytes[3:7])

            print('data size',datasize)
            str_packet = packet_bytes[7:datasize+1]
            logging.debug('hex msg {hm}'.format(hm = packet_bytes))
            logging.debug('data part {packet}'.format(packet=str_packet))
            measured_dict = json.loads(str_packet)
            hex_equip_id = measured_dict['equipmentid']
            str_equip_id = hex2str(hex_equip_id)
            hex_time = measured_dict['pub_time']
            int_time = hex2int(hex_time)
            modbus_msg['equipment_id'] = str_equip_id
            modbus_msg['ip'] = host
            modbus_msg['port'] = port
            modbus_msg['pub_time'] = str(int_time)
            meta_list = list()
            for meta_info in measured_dict['meta']:
                sensor_code = hex2str(meta_info['sensor_cd'])
                fun_cd = hex2str(meta_info['fun_cd'])
                sv_hex = meta_info['sensor_value']
                sv_int = hex2int(sv_hex)
                decimal_point = hex2int(meta_info['decimal_point'])
                meta_list.append({'sensor_cd': sensor_code,
                                    'fun_cd': fun_cd,
                                    'sensor_value': sv_int,
                                    'decimal_point': decimal_point
                                    })
            modbus_msg['meta'] = meta_list
            status = 'OK'
        except Exception as e:
            modbus_msg = None
            logging.exception(str(e))
        return status, str(packet_bytes), modbus_msg
    
    def convert_hex2decimal(self, packet_bytes, host, port, mqtt_valid=True):
        """In the packet, the hexadecimal value is converted to a decimal value, structured in json format, and returned.

        packet           TCP Stream packet from IIot Gateway
        readable_sock       client socket object

        packet specification
        stx is the starting code, the hex value matching STX in the ascii code table
        utc time is the time when the sensor value is received from the iiot gate
        equipment id means the id of the equipment and is predefined in the database.
        sensor code is means the sensor's type like as tempeatur, pressure, voltage,...
        decimal_point means the accuracy of sensor value, decimal point.
        The sensor value means the sensor value installed in the facility.
        """
        status = 'ER'
        modbus_dict = {'equipment_id': '', 'meta': {'ip': '',
                                                    'port': '',
                                                    'time': '',
                                                    'sensor_cd': '',
                                                    'fun_cd': '',
                                                    'sensor_value': '',
                                                    'decimal_point': ''
                                                    }}
        try:
            byte_tuple = tuple(i for i in list(packet_bytes))
            logging.debug('byte message\r\n' + str(byte_tuple))
            if byte_tuple[0] == 2 and (byte_tuple[16] == 3 or byte_tuple[18] == 3):
                group = chr(byte_tuple[5]) + chr(byte_tuple[6])
                group_code = int('0x{:02x}'.format(byte_tuple[7]) + '{:02x}'.format(byte_tuple[8]), 16)
                group_code = '{0:04d}'.format(group_code)
                sensor_code = int('0x{:02x}'.format(byte_tuple[9]) + '{:02x}'.format(byte_tuple[10]), 16)
                sensor_code = '{0:04d}'.format(sensor_code)
                fn = chr(byte_tuple[11]) + chr(byte_tuple[12])
                logging.debug('function name:' + fn)
                
                fv = '0x{:02x}'.format(byte_tuple[13]) + '{:02x}'.format(byte_tuple[14]) + '{:02x}'.format(
                    byte_tuple[15]) + '{:02x}'.format(byte_tuple[16])
                decimal_point = int('0x{:02x}'.format(byte_tuple[17]), 16)
                logging.debug('**8Byte pressure:' + str(sensor_code) + ':' + fv)
                fv = int(fv, 16)
                
                ms_time = time.time()
                pub_time = datetime.fromtimestamp(time.time())
                pub_time = str(pub_time).replace('.', 'ms')

                modbus_dict = {'equipment_id': group + group_code, 'meta': {'ip': host,
                                                                            'port': port,
                                                                            'ms_time': ms_time,
                                                                            'sensor_cd': sensor_code,
                                                                            'fun_cd': fn,
                                                                            'sensor_value': fv,
                                                                            'decimal_point': decimal_point,
                                                                            'pub_time': str(pub_time)
                                                                            }}
                
                status = 'OK'
            else:
                status = 'ER'
        except Exception as e:
            logging.exception(str(e))
        logging.debug(status + str(packet_bytes) + str(modbus_dict))
        return status, str(packet_bytes), modbus_dict
    
    async def get_client(self, event_manger, server_sock, msg_size, mqtt_info):
        """
        It create client socket with server sockt
        event_manger        It has asyncio event loop
        server_socket       Socket corresponding to the client socket
        msg_size            It means the packet size to be acquired at a time from the client socket.
        msg_queue           It means the queue containing the message transmitted from the gateway.
        """
        with GracefulInterruptHandler() as h:
            client = None
            while True:
                if not h.interrupted:
                    client, _ = await event_manger.sock_accept(server_sock)
                    # event_manger.create_task(self.manage_client(event_manger, client, msg_size, rabbit_channel))#deprecated
                    event_manger.create_task(self.m2mmesage_handler(event_manger, client, msg_size, mqtt_info))
                else:
                    client.close()
                    server_sock.close()
                    sys.exit(0)
    
    async def m2mmesage_handler(self, event_manger, client, msg_size, mqtt_info):
            fac_daq = self.get_fac_inf(self.redis_mgr)
            with GracefulInterruptHandler() as h:
                while True:
                    if not h.interrupted:
                        try:
                            packet = (await event_manger.sock_recv(client, msg_size))
                            packet = packet.decode('utf-8')
                            
                        except Exception as e:
                            client.close()
                            logging.debug('Client socket close by exception:' + str(e.args))
                            h.release()
                            break
                        if packet:
                            try:
                                logging.debug('try convert')
                                host, port = client.getpeername()
                                status, packet, modbus_msg = self.convert_jsonhex(packet, host, port)
                                print(status, packet, modbus_msg)
                                if status == 'OK':
                                    equipment_id = modbus_msg['equipment_id']
                                    logging.debug('equipment_id:' + equipment_id)
                                    logging.debug('device_key:' + self.device_key)
                                    try:
                                        device_body = self.redis_mgr.get(self.device_key)
                                        logging.debug('device_body:' + str(device_body))
                                        redis_fac_info = json.loads(device_body)

                                    except Exception as e:
                                        logging.error('redis key error')
                                        logging.error('device_body:'+str(device_body))
                                        logging.error(str(e))
                                        logging.info('recover redis key')
                                        self.get_fac_inf(self.redis_mgr)
                                        # exit(1)

                                    if equipment_id in redis_fac_info.keys():
                                        logging.debug('config factory message')
                                        sensors_meta = modbus_msg['meta']
                                        status, fac_msg = self.config_fac_msg(equipment_id, fac_daq, sensors_meta,
                                                                              redis_fac_info)

                                        if status == 'success':
                                            rabbit_channel, rtn_json = self.publish_facility_msg(
                                                mqtt_info=mqtt_info,
                                                routing_key=equipment_id,
                                                json_body=fac_msg)
                                            if rtn_json == json.loads(fac_msg):
                                                logging.debug(
                                                    'mq body:' + str(json.dumps({equipment_id: fac_daq[equipment_id]})))
                                            else:
                                                logging.exception("MQTT Publish Excetion:" + str(rtn_json))
                                                raise NameError('MQTT Publish exception')
                                        else:
                                            acq_message = status + packet + 'is not exist sensor key\r\n'
                                            logging.debug(acq_message)
                                            client.sendall(acq_message.encode())
                                            continue
                                    else:
                                        acq_message = status + packet + 'is not exist equipment_id key\r\n'
                                        logging.debug(acq_message)
                                        client.sendall(acq_message.encode())
                                        continue
                                acq_message = status + packet + '\r\n'
                                logging.debug('rtn:' + acq_message)
                                client.sendall(acq_message.encode())
                            except Exception as e:
                                client.sendall(packet.encode())
                                logging.exception('message error:' + str(e))
                        else:
                            client.close()
                    else:
                        client.close()
                        sys.exit(0)
    
    async def manage_client(self, event_manger, client, msg_size, mqtt_info):
        """
            It receives modbus data from iiot gateway using client socket.
            event_manger        It has asyncio event loop
            client              It is a client socket that works with multiple iiot gateways.
            msg_size            It means the packet size to be acquired at a time from the client socket.
            msg_queue           It means the queue containing the message transmitted from the gateway.
        """
        
        fac_daq = self.get_fac_inf(self.redis_mgr)
        
        with GracefulInterruptHandler() as h:
            while True:
                if not h.interrupted:
                    try:
                        packet = (await event_manger.sock_recv(client, msg_size))
                    except Exception as e:
                        client.close()
                        logging.debug('Client socket close by exception:' + str(e.args))
                        h.release()
                        break
                    if packet:
                        try:
                            logging.debug('try convert')
                            host, port = client.getpeername()
                            status, packet, modbus_udp = self.convert_hex2decimal(packet, host, port)
                            if status == 'OK':
                                equipment_id = modbus_udp['equipment_id']
                                logging.debug('equipment_id:' + equipment_id)
                                try:
                                    redis_fac_info = json.loads(self.redis_mgr.get(self.device_key))
                                except Exception as e:
                                    logging.error(str(redis_fac_info))
                                    logging.error(str(e))

                                if equipment_id in redis_fac_info.keys():
                                    logging.debug('config factory message')
                                    status, fac_msg = self.config_fac_msg(equipment_id, fac_daq, modbus_udp,
                                                                          redis_fac_info)
                                    if status == 'success':
                                        rabbit_channel, rtn_json = self.publish_facility_msg(mqtt_info=mqtt_info,
                                                                                             routing_key=equipment_id,
                                                                                             json_body=fac_msg)
                                        if rtn_json == json.loads(fac_msg):
                                            logging.debug(
                                                'mq body:' + str(json.dumps({equipment_id: fac_daq[equipment_id]})))
                                        else:
                                            logging.exception("MQTT Publish Excetion:" + str(rtn_json))
                                            raise NameError('MQTT Publish exception')
                                    else:
                                        acq_message = status + packet + 'is not exist sensor key\r\n'
                                        logging.debug(acq_message)
                                        client.sendall(acq_message.encode())
                                        continue
                                else:
                                    acq_message = status + packet + 'is not exist equipment_id key\r\n'
                                    logging.debug(acq_message)
                                    client.sendall(acq_message.encode())
                                    continue
                            acq_message = status + packet + '\r\n'
                            logging.debug('rtn:' + acq_message)
                            client.sendall(acq_message.encode())
                        except Exception as e:
                            client.sendall(packet.encode())
                            logging.exception('message error:' + str(e))
                    else:
                        client.close()
                else:
                    client.close()
                    sys.exit(0)
