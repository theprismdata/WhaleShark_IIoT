import json
import pika


def fanout_exange():
    credentials = pika.PlainCredentials('whaleshark', 'whaleshark')
    param = pika.ConnectionParameters('localhost', 5672, '/', credentials)
    connection = pika.BlockingConnection(param)
    channel = connection.channel()
    ex_name = 'home_exchange'
    q_name = 'hq1'
    r_key = 'route1'
    msg_body = json.dumps({'F1': 'TEST3'})
    channel.queue_declare(queue=q_name)
    channel.exchange_declare(exchange=ex_name, exchange_type='fanout')
    channel.queue_bind(queue=q_name, exchange=ex_name, routing_key=r_key)
    channel.basic_publish(exchange=ex_name, routing_key=r_key, body=msg_body)

def direct_exange():
    credentials = pika.PlainCredentials('whaleshark', 'whaleshark')
    param = pika.ConnectionParameters('localhost', 5672, '/', credentials)
    connection = pika.BlockingConnection(param)
    channel = connection.channel()
    ex_name = 'direct_logs'
    q_name = 'hq_logs'
    r_key = 'direct_route1'
    msg_body = json.dumps({'F1': 'LOGS'})
    channel.queue_declare(queue=q_name)
    channel.exchange_declare(exchange=ex_name, exchange_type='direct')
    channel.queue_bind(queue=q_name, exchange=ex_name, routing_key=r_key)
    channel.basic_publish(exchange=ex_name, routing_key=r_key, body=msg_body)

if __name__ == '__main__':
    # direct_exange()
    fanout_exange()
