import pika
import json
from loguru import logger
import os
from dotenv import load_dotenv

class MessageBroker:
    """
    Message Broker service using RabbitMQ for event-driven communication
    This enables loose coupling between components
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MessageBroker, cls).__new__(cls)
            cls._instance.initialized = False
        return cls._instance

    def __init__(self):
        if self.initialized:
            return
        
        load_dotenv()
        self.host = os.getenv('RABBITMQ_HOST', 'localhost')
        self.port = int(os.getenv('RABBITMQ_PORT', '5672'))
        self.user = os.getenv('RABBITMQ_USER', 'guest')
        self.password = os.getenv('RABBITMQ_PASS', 'guest')
        
        self.initialized = True
        self.connection = None
        self.channel = None
    
    def connect(self):
        """Connect to RabbitMQ and return a channel"""
        if self.connection and self.connection.is_open:
            return self.channel
            
        try:
            credentials = pika.PlainCredentials(self.user, self.password)
            parameters = pika.ConnectionParameters(
                host=self.host,
                port=self.port,
                credentials=credentials
            )
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            return self.channel
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            return None
    
    def declare_queue(self, queue_name):
        """Declare a new queue"""
        channel = self.connect()
        if channel:
            channel.queue_declare(queue=queue_name, durable=True)
            logger.info(f"Queue {queue_name} declared")
            return True
        return False
    
    def publish_message(self, queue_name, message):
        """Publish a message to a queue"""
        channel = self.connect()
        if not channel:
            return False
            
        try:
            if not isinstance(message, str):
                message = json.dumps(message)
                
            channel.basic_publish(
                exchange='',
                routing_key=queue_name,
                body=message,
                properties=pika.BasicProperties(
                    delivery_mode=2,  # make message persistent
                )
            )
            logger.info(f"Published message to {queue_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to publish message: {e}")
            return False
    
    def consume_messages(self, queue_name, callback):
        """Start consuming messages from a queue with a callback function"""
        channel = self.connect()
        if not channel:
            return False
            
        try:
            self.declare_queue(queue_name)
            channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
            logger.info(f"Started consuming messages from {queue_name}")
            channel.start_consuming()
        except Exception as e:
            logger.error(f"Failed to consume messages: {e}")
            return False
    
    def stop_consuming(self):
        """Stop consuming messages"""
        if self.channel:
            try:
                self.channel.stop_consuming()
                logger.info("Stopped consuming messages")
            except Exception as e:
                logger.error(f"Failed to stop consuming: {e}")
    
    def close(self):
        """Close the connection"""
        if self.connection and self.connection.is_open:
            self.connection.close()
            logger.info("Connection closed")