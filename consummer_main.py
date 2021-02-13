import json
import pika


def callback_mqreceive(ch, method, properties, body):
    body = body.decode('utf-8')
    facility_msg_json = json.loads(body)
    print('mqreceice:%s' % (facility_msg_json))

def fanout_exchange_consum():
    credentials = pika.PlainCredentials('whaleshark', 'whaleshark')
    param = pika.ConnectionParameters('localhost', 5672, '/', credentials)
    connection = pika.BlockingConnection(param)
    channel = connection.channel()
    q_name = 'hq1'
    mq = channel.queue_declare(queue=q_name).method.queue
    channel.basic_consume(mq, on_message_callback=callback_mqreceive, auto_ack=True)
    channel.start_consuming()

def direct_exchange_consum():
    credentials = pika.PlainCredentials('whaleshark', 'whaleshark')
    param = pika.ConnectionParameters('localhost', 5672, '/', credentials)
    connection = pika.BlockingConnection(param)
    channel = connection.channel()
    q_name = 'hq_logs'
    mq = channel.queue_declare(queue=q_name).method.queue
    channel.basic_consume(mq, on_message_callback=callback_mqreceive, auto_ack=True)
    channel.start_consuming()

if __name__ == '__main__':
    fanout_exchange_consum()
    #direct_exchange_consum()
