import sys
from copy import deepcopy
from random import *
from influxdb import InfluxDBClient
import time

client = InfluxDBClient('localhost', 8086, 'krmim', 'krmim_2017', 'stress_test')
f = open("./influx_stress_test.log", 'w')
json_body = [ {"measurement": 'm1', "fields": {'f1':randint(1,100)}} for i in range(0, 40000)]
for count in range(0,86400):
    start = time.time()  # 시작 시간 저장
    try:
        if client.write_points(json_body) is True:
            duringtime = time.time() - start
            f.writelines("ProcessTime,%s,runtime(msec),%0.3f\n"%(time.strftime('%y-%m-%d %H:%M:%S'), duringtime * 1000))
            f.flush()
        else:
            print('influx write faile:' + str(json_body))
    except Exception as e:
        print(e.args)
    time.sleep(1)
client.close()
f.close()
