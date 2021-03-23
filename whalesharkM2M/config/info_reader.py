import os
import pandas as pd

device_path = os.getcwd() +'/config/controllerinfo.csv'
def read_controller(filepath):
    """
    Return dataframe from csv file
    """
    try:
        controller_df = pd.read_csv(filepath)

        return controller_df
    except Exception as e:
        print(e)
        
def read_deviceinfo(ctrl_info_path):
    """
    Return information dictionary which has device info (controllerinfo.csv)
    """
    try:
        ci_df = pd.read_csv(ctrl_info_path)

        equip_info = {}
        recv_key = ci_df.RECV_KEY.unique().tolist()[0]
        equip_list = ci_df[(ci_df.RECV_KEY == recv_key)]['EQUIPID'].unique().tolist()
        for quip_id in equip_list:
            equip_info[quip_id] = dict()

        for quip_id in equip_list:
            sensor_cds = ci_df[(ci_df.RECV_KEY == recv_key) & (ci_df.EQUIPID == quip_id)]['SENSOR_CODE'].tolist()
            for sensor_cd in sensor_cds:
                sensor_name = ci_df[(ci_df.RECV_KEY == recv_key) & (ci_df.EQUIPID == quip_id) & (ci_df.SENSOR_CODE == sensor_cd)]['SENSOR_NAME'].tolist()[0]
                equip_info[quip_id]['%04d' % (sensor_cd)] = sensor_name
        return recv_key, equip_info
    except Exception as e:
        print(e)