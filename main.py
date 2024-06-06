"""
Plus Monitoring
"""
import time
import importlib
import threading
from prometheus_client import Gauge, start_http_server, CollectorRegistry
from src.config import Config
from src.logger import logger

# Initialize Prometheus metrics registry
REG = CollectorRegistry()

# Define label names and metrics
LABEL_NAMES = ['name', 'fqdn', 'port', 'type']
PLUS_MONITORING_METRIC = Gauge('plus_monitoring', "Plus Monitoring", registry=REG, labelnames=LABEL_NAMES)
THREAD_COUNT_METRIC = Gauge('plus_monitoring_thread_count', "Plus Monitoring Thread Count", registry=REG)


def create_monitoring_thread(service, data):
    """
    Create and start a monitoring thread for a specific service.

    Parameters:
    - service (str): Name of the service to be monitored.
    - data (dict): Configuration data for the service which includes:
        - type (str): Type of service (e.g., 'rabbitmq', 'redis', 'database').
        - fqdn (str): Fully qualified domain name of the service.
        - authentication (dict): Authentication details for the service.
        - port (int): Port number on which the service is running.
        - check_interval (int): Interval in seconds for performing health checks.

    Returns:
    - thread (Thread): The created and started thread for the service monitoring.
    """
    service_type = data.get("type")
    fqdn = data.get("fqdn")
    authentication = data.get("authentication")
    port = data.get("port")
    check_interval = data.get("check_interval")

    # Dynamically import the module for the service type
    module = importlib.import_module(f'src.{service_type}')
    # Get the test method for the service type
    module_method = getattr(module, f'{service_type}_test')(authentication=authentication, fqdn=fqdn, port=port,
                                                            check_interval=check_interval, registry=REG)

    # Create and start the monitoring thread
    thread = threading.Thread(target=module_method.test,
                              args=(
                              PLUS_MONITORING_METRIC.labels(name=service, fqdn=fqdn, port=port, type=service_type),))
    thread.start()
    return thread


def monitor_active_thread_count(metric):
    """
    Monitor and set the active thread count every 5 seconds.

    Parameters:
    - metric (Gauge): Prometheus gauge metric to update with the active thread count.
    """
    while True:
        try:
            # Get the current active thread count
            active_thread_count = threading.active_count()
            # Update the Prometheus metric with the active thread count
            metric.set(active_thread_count)
            logger.info(f"Set active thread count: {active_thread_count}")
        except Exception as e:
            logger.error(f"Failed to set active thread count: {e}")
        time.sleep(5)


def trigger_monitoring():
    """
    Load configuration and trigger monitoring for all configured services.

    This function performs the following steps:
    1. Load the configuration which contains the list of services to monitor.
    2. Create and start a thread to monitor the active thread count.
    3. Create and start a monitoring thread for each service based on the configuration.
    4. Wait for all threads to complete their execution.
    """
    # Load configuration
    config = Config()
    services = config.services

    # List to hold all created threads
    thread_pool = []

    # Create and start a thread to monitor the active thread count
    active_thread_count_thread = threading.Thread(target=monitor_active_thread_count, args=(THREAD_COUNT_METRIC,))
    active_thread_count_thread.start()
    thread_pool.append(active_thread_count_thread)

    # Create and start a monitoring thread for each service
    for service, data in services.items():
        thread = create_monitoring_thread(service, data)
        thread_pool.append(thread)

    # Wait for all threads to complete
    for thread in thread_pool:
        thread.join()


if __name__ == "__main__":
    # Start the Prometheus HTTP server to expose the metrics
    start_http_server(9101, registry=REG)

    logger.info("Starting monitoring jobs...")
    # Trigger the monitoring process
    trigger_monitoring()
