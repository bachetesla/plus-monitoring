import redis
from threading import Thread, Event
import time
from src.logger import logger
from typing import Dict
from .base import Base
from prometheus_client import Gauge

class RedisConnection:
    """
    Singleton class to manage Redis connections.

    Attributes:
    - password (str): Redis password.
    - db (int): Redis database number.
    - fqdn (str): Fully qualified domain name of the Redis server.
    - port (int): Port number for the Redis server.
    - connection (redis.StrictRedis): Redis connection object.
    """
    _instance = None

    def __new__(cls, authentication: Dict, fqdn: str, port: int):
        """
        Create a new instance of RedisConnection if one does not already exist.

        Parameters:
        - authentication (Dict): Dictionary containing 'password' and 'db'.
        - fqdn (str): Fully qualified domain name of the Redis server.
        - port (int): Port number for the Redis server.

        Returns:
        - RedisConnection: The singleton instance of RedisConnection.
        """
        if cls._instance is None:
            cls._instance = super(RedisConnection, cls).__new__(cls)
            cls._instance.password = authentication.get('password', None)
            cls._instance.db = int(authentication.get("db", 0))
            cls._instance.fqdn = fqdn
            cls._instance.port = port
            cls._instance.connection = None
        return cls._instance

    def get_connection(self):
        """
        Get the Redis connection, reconnecting if necessary.

        Returns:
        - redis.StrictRedis: Redis connection object.
        """
        if not self.connection:
            self.connect()
        return self.connection

    def connect(self):
        """
        Establish a connection to the Redis server.
        """
        try:
            self.connection = redis.StrictRedis(
                host=self.fqdn,
                port=self.port,
                db=self.db,
                password=self.password
            )
        except Exception as e:
            logger.error(f"Error connecting to Redis: {e}")

class redis_test(Base):
    """
    Class to perform health checks on a Redis server.

    Attributes:
    - registry (CollectorRegistry): Registry for Prometheus metrics.
    - redis_connection (RedisConnection): Instance of RedisConnection.
    - check_interval (int): Interval in seconds for performing health checks.
    - stop_event (Event): Event to signal stopping of the health check thread.
    - key (str): Key used for testing Redis operations.
    - payload (str): Payload to set in the Redis test key.
    """
    def __init__(self, authentication: Dict, fqdn: str, port: int, check_interval: int, registry):
        """
        Initialize the Redis test class.

        Parameters:
        - authentication (Dict): Dictionary containing 'password' and 'db'.
        - fqdn (str): Fully qualified domain name of the Redis server.
        - port (int): Port number for the Redis server.
        - check_interval (int): Interval in seconds for performing health checks.
        - registry (CollectorRegistry): Registry for Prometheus metrics.
        """
        self.registry = registry
        self.redis_connection = RedisConnection(authentication, fqdn, port)
        self.check_interval = check_interval
        self.stop_event = Event()
        self.key = "DEVOPS_TEST_KEY"
        self.payload = 'DEVOPS_TEST_VALUE'

    def test_redis(self, metric: Gauge):
        """
        Perform a health check on the Redis server by setting, getting, incrementing, and deleting a key.

        Parameters:
        - metric (Gauge): Prometheus gauge metric to update with the test result.
        """
        while not self.stop_event.is_set():
            try:
                connection = self.redis_connection.get_connection()

                # Set a key-value pair in Redis
                connection.set(self.key, self.payload)
                logger.info(f'Set key "{self.key}" with value "{self.payload}"')

                # Get the value of the key from Redis
                value = connection.get(self.key)
                if value and value.decode("utf-8") == self.payload:
                    logger.info(f'Value for key "{self.key}": {value.decode("utf-8")}')

                    # Increment a test counter
                    connection.incr('SRE_TEST_COUNTER', 1)
                    counter_value = connection.get('SRE_TEST_COUNTER')
                    logger.info(f'Incremented counter: {counter_value.decode("utf-8")}')

                    # Delete the key and counter from Redis
                    connection.delete(self.key)
                    connection.delete('SRE_TEST_COUNTER')
                    logger.info(f'Deleted key "{self.key}" and counter')

                    # Verify the key is deleted
                    key_exists = connection.exists(self.key)
                    logger.info(f'Does key "{self.key}" exist? {key_exists == 1}')
                    self.result = key_exists == 0
                else:
                    logger.error(f'Key "{self.key}" not found or value mismatch.')
                    self.result = False
            except Exception as e:
                logger.error(f'Redis operation error: {str(e)}')
                self.result = False

            metric.set(1 if self.result else 0)
            time.sleep(self.check_interval)

    def stop_threads(self):
        """
        Signal the health check threads to stop.
        """
        self.stop_event.set()

    def test(self, metric: Gauge):
        """
        Start the health check thread to continuously perform health checks.

        Parameters:
        - metric (Gauge): Prometheus gauge metric to update with the test result.
        """
        send_thread = Thread(target=self.test_redis, args=(metric,))
        send_thread.start()

        # The thread will run indefinitely until you manually stop the program.
        # If you want to stop the program, you can use Ctrl+C or any other appropriate method.
