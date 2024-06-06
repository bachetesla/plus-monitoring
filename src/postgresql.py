import psycopg2
from threading import Thread, Event
import time
from src.logger import logger
from typing import Dict
from .base import Base
from prometheus_client import Gauge

class PostgreSQLConnection:
    """
    Singleton class to manage PostgreSQL connections.

    Attributes:
    - username (str): PostgreSQL username.
    - password (str): PostgreSQL password.
    - database (str): Database name.
    - fqdn (str): Fully qualified domain name of the PostgreSQL server.
    - port (int): Port number for the PostgreSQL server.
    - connection (psycopg2.connection): PostgreSQL connection object.
    """
    _instance = None

    def __new__(cls, authentication: Dict, fqdn: str, port: int):
        """
        Create a new instance of PostgreSQLConnection if one does not already exist.

        Parameters:
        - authentication (Dict): Dictionary containing 'username', 'password', and 'db'.
        - fqdn (str): Fully qualified domain name of the PostgreSQL server.
        - port (int): Port number for the PostgreSQL server.

        Returns:
        - PostgreSQLConnection: The singleton instance of PostgreSQLConnection.
        """
        if cls._instance is None:
            cls._instance = super(PostgreSQLConnection, cls).__new__(cls)
            cls._instance.username = authentication.get("username", None)
            cls._instance.password = authentication.get("password", None)
            cls._instance.database = authentication.get("db", None)
            cls._instance.fqdn = fqdn
            cls._instance.port = port
            cls._instance.connection = None
        return cls._instance

    def get_connection(self):
        """
        Get the PostgreSQL connection, connecting if necessary.

        Returns:
        - psycopg2.connection: PostgreSQL connection object.
        """
        if not self.connection:
            self.connect()
        return self.connection

    def connect(self):
        """
        Establish a connection to the PostgreSQL server.
        """
        try:
            self.connection = psycopg2.connect(
                user=self.username,
                password=self.password,
                host=self.fqdn,
                port=self.port,
                database=self.database
            )
        except psycopg2.Error as err:
            logger.error(f"Error connecting to PostgreSQL: {err}")

class postgresql_test(Base):
    """
    Class to perform health checks on a PostgreSQL server.

    Attributes:
    - postgresql_connection (PostgreSQLConnection): Instance of PostgreSQLConnection.
    - check_interval (int): Interval in seconds for performing health checks.
    - stop_event (Event): Event to signal stopping of the health check thread.
    - result (bool): Result of the last health check.
    - registry (CollectorRegistry): Registry for Prometheus metrics.
    """

    def __init__(self, authentication: Dict, fqdn: str, port: int, check_interval: int, registry):
        """
        Initialize the PostgreSQL test class.

        Parameters:
        - authentication (Dict): Dictionary containing 'username', 'password', and 'db'.
        - fqdn (str): Fully qualified domain name of the PostgreSQL server.
        - port (int): Port number for the PostgreSQL server.
        - check_interval (int): Interval in seconds for performing health checks.
        - registry (CollectorRegistry): Registry for Prometheus metrics.
        """
        self.postgresql_connection = PostgreSQLConnection(authentication, fqdn, port)
        self.check_interval = check_interval
        self.stop_event = Event()
        self.result = False
        self.registry = registry

    def query_check(self, metric: Gauge):
        """
        Perform a health check by executing a simple SQL query.

        Parameters:
        - metric (Gauge): Prometheus gauge metric to update with the test result.
        """
        while not self.stop_event.is_set():
            try:
                connection = self.postgresql_connection.get_connection()
                cursor = connection.cursor()

                # Replace this with your specific SQL query
                query = "SELECT 1"

                cursor.execute(query)

                if cursor.fetchone()[0] == 1:
                    logger.info("PostgreSQL query successful")
                    self.result = True
                else:
                    logger.error("PostgreSQL query failed")
                    self.result = False

            except psycopg2.Error as err:
                logger.error(f"PostgreSQL error: {err}")
                self.result = False

            # Update the Prometheus metric with the result of the health check
            metric.set(1 if self.result else 0)
            time.sleep(self.check_interval)

    def stop_threads(self):
        """
        Signal the health check thread to stop.
        """
        self.stop_event.set()

    def test(self, metric: Gauge):
        """
        Start the health check thread to continuously perform health checks.

        Parameters:
        - metric (Gauge): Prometheus gauge metric to update with the test result.
        """
        query_thread = Thread(target=self.query_check, args=(metric,))
        query_thread.start()

        # The thread will run indefinitely until you manually stop the program.
        # If you want to stop the program, you can use Ctrl+C or any other appropriate method.
