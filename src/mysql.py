import mysql.connector
from threading import Thread, Event
import time
from src.logger import logger
from typing import Dict
from .base import Base
from prometheus_client import Gauge

class MySQLConnection:
    """
    Singleton class to manage MySQL connections.

    Attributes:
    - username (str): MySQL username.
    - password (str): MySQL password.
    - database (str): Database name.
    - fqdn (str): Fully qualified domain name of the MySQL server.
    - port (int): Port number for the MySQL server.
    - connection (mysql.connector.connection.MySQLConnection): MySQL connection object.
    """
    _instance = None

    def __new__(cls, authentication: Dict, fqdn: str, port: int):
        """
        Create a new instance of MySQLConnection if one does not already exist.

        Parameters:
        - authentication (Dict): Dictionary containing 'username', 'password', and 'db'.
        - fqdn (str): Fully qualified domain name of the MySQL server.
        - port (int): Port number for the MySQL server.

        Returns:
        - MySQLConnection: The singleton instance of MySQLConnection.
        """
        if cls._instance is None:
            cls._instance = super(MySQLConnection, cls).__new__(cls)
            cls._instance.username = authentication.get("username", None)
            cls._instance.password = authentication.get("password", None)
            cls._instance.database = authentication.get("db", None)
            cls._instance.fqdn = fqdn
            cls._instance.port = port
            cls._instance.connection = None
        return cls._instance

    def get_connection(self, force: bool = False):
        """
        Get the MySQL connection, optionally forcing a reconnect.

        Parameters:
        - force (bool): If True, forces a reconnect. Default is False.

        Returns:
        - mysql.connector.connection.MySQLConnection: MySQL connection object.
        """
        if force:
            self.connect()
            return self.connection
        if not self.connection:
            self.connect()
        return self.connection

    def connect(self):
        """
        Establish a connection to the MySQL server.
        """
        try:
            self.connection = mysql.connector.connect(
                user=self.username,
                password=self.password,
                host=self.fqdn,
                port=self.port,
                database=self.database
            )
        except mysql.connector.Error as err:
            logger.error(f"Error connecting to MySQL: {err}")

class mysql_test(Base):
    """
    Class to perform health checks on a MySQL server.

    Attributes:
    - mysql_connection (MySQLConnection): Instance of MySQLConnection.
    - check_interval (int): Interval in seconds for performing health checks.
    - stop_event (Event): Event to signal stopping of the health check thread.
    - result (bool): Result of the last health check.
    - registry (CollectorRegistry): Registry for Prometheus metrics.
    """

    def __init__(self, authentication: Dict, fqdn: str, port: int, check_interval: int, registry):
        """
        Initialize the MySQL test class.

        Parameters:
        - authentication (Dict): Dictionary containing 'username', 'password', and 'db'.
        - fqdn (str): Fully qualified domain name of the MySQL server.
        - port (int): Port number for the MySQL server.
        - check_interval (int): Interval in seconds for performing health checks.
        - registry (CollectorRegistry): Registry for Prometheus metrics.
        """
        self.mysql_connection = MySQLConnection(authentication, fqdn, port)
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
                if not self.result:
                    connection = self.mysql_connection.get_connection(force=True)
                else:
                    connection = self.mysql_connection.get_connection(force=False)
                cursor = connection.cursor()

                # Replace this with your specific SQL query
                query = "SELECT 1"

                cursor.execute(query)

                if cursor.fetchone()[0] == 1:
                    logger.info("MySQL query successful")
                    self.result = True
                else:
                    logger.error("MySQL query failed")
                    self.result = False

            except mysql.connector.Error as err:
                logger.error(f"MySQL error: {err}")
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
