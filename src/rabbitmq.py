import pika
from threading import Thread, Event
import time
from src.logger import logger
from typing import Dict
from .base import Base
from prometheus_client import Gauge

class RabbitMQConnection:
    """
    Singleton class to manage RabbitMQ connections.

    Attributes:
    - username (str): RabbitMQ username.
    - password (str): RabbitMQ password.
    - fqdn (str): Fully qualified domain name of the RabbitMQ server.
    - port (int): Port number for the RabbitMQ server.
    - connection (pika.BlockingConnection): RabbitMQ connection object.
    """
    _instance = None

    def __new__(cls, authentication: Dict, fqdn: str, port: int):
        """
        Create a new instance of RabbitMQConnection if one does not already exist.

        Parameters:
        - authentication (Dict): Dictionary containing 'username' and 'password'.
        - fqdn (str): Fully qualified domain name of the RabbitMQ server.
        - port (int): Port number for the RabbitMQ server.

        Returns:
        - RabbitMQConnection: The singleton instance of RabbitMQConnection.
        """
        if cls._instance is None:
            cls._instance = super(RabbitMQConnection, cls).__new__(cls)
            cls._instance.username = authentication.get("username")
            cls._instance.password = authentication.get("password")
            cls._instance.fqdn = fqdn
            cls._instance.port = port
            cls._instance.connection = None
        return cls._instance

    def get_connection(self):
        """
        Get the RabbitMQ connection, reconnecting if necessary.

        Returns:
        - pika.BlockingConnection: RabbitMQ connection object.
        """
        if not self.connection or self.connection.is_closed:
            self.connect()
        return self.connection

    def connect(self):
        """
        Establish a connection to the RabbitMQ server.
        """
        try:
            self.connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=self.fqdn,
                    port=self.port,
                    credentials=pika.PlainCredentials(self.username, self.password)
                )
            )
        except Exception as e:
            logger.error(f"Error connecting to RabbitMQ: {e}")

class rabbitmq_test(Base):
    """
    Class to perform health checks on a RabbitMQ server.

    Attributes:
    - registry (CollectorRegistry): Registry for Prometheus metrics.
    - rabbitmq_connection (RabbitMQConnection): Instance of RabbitMQConnection.
    - queue (str): Name of the test queue.
    - payload (str): Payload to send in the test message.
    - check_interval (int): Interval in seconds for performing health checks.
    - stop_event (Event): Event to signal stopping of the health check thread.
    """
    def __init__(self, authentication: Dict, fqdn: str, port: int, check_interval: int, registry):
        """
        Initialize the RabbitMQ test class.

        Parameters:
        - authentication (Dict): Dictionary containing 'username' and 'password'.
        - fqdn (str): Fully qualified domain name of the RabbitMQ server.
        - port (int): Port number for the RabbitMQ server.
        - check_interval (int): Interval in seconds for performing health checks.
        - registry (CollectorRegistry): Registry for Prometheus metrics.
        """
        self.registry = registry
        self.rabbitmq_connection = RabbitMQConnection(authentication, fqdn, port)
        self.queue = "SRE_TEST_QUEUE"
        self.payload = "SRE_TEST_PAYLOAD"
        self.check_interval = check_interval
        self.stop_event = Event()

    def send_message_test(self, metric: Gauge):
        """
        Perform a health check by sending a message to the RabbitMQ server.

        Parameters:
        - metric (Gauge): Prometheus gauge metric to update with the test result.
        """
        while not self.stop_event.is_set():
            try:
                connection = self.rabbitmq_connection.get_connection()
                channel = connection.channel()

                channel.queue_declare(queue=self.queue)

                channel.basic_publish(exchange='', routing_key=self.queue, body=self.payload)
                logger.info(f"Sent Message: {self.payload}")

                metric.set(1)
                time.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Error sending message: {e}")
                metric.set(0)
                time.sleep(self.check_interval)

    def read_message_test(self, metric: Gauge):
        """
        Perform a health check by reading a message from the RabbitMQ server.

        Parameters:
        - metric (Gauge): Prometheus gauge metric to update with the test result.
        """
        while not self.stop_event.is_set():
            try:
                connection = self.rabbitmq_connection.get_connection()
                channel = connection.channel()

                channel.queue_declare(queue=self.queue)

                def callback(ch, method, properties, body):
                    logger.info(f"Received message: {body}")
                    metric.set(1)

                channel.basic_consume(queue=self.queue, on_message_callback=callback, auto_ack=True)
                channel.start_consuming()
            except Exception as e:
                logger.error(f"Error reading message: {e}")
                metric.set(0)
                time.sleep(self.check_interval)

    def stop_threads(self):
        """
        Signal the health check threads to stop.
        """
        self.stop_event.set()

    def test(self, metric: Gauge):
        """
        Start the health check threads to continuously perform health checks.

        Parameters:
        - metric (Gauge): Prometheus gauge metric to update with the test result.
        """
        send_thread = Thread(target=self.send_message_test, args=(metric,))
        read_thread = Thread(target=self.read_message_test, args=(metric,))

        send_thread.start()
        read_thread.start()

        # The threads will run indefinitely until you manually stop the program.
        # If you want to stop the program, you can use Ctrl+C or any other appropriate method.
