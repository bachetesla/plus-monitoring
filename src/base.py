"""
This module serves as the base class for monitoring services.
"""
from prometheus_client import CollectorRegistry, Gauge

class Base:
    """
    Base class for all monitoring service modules.

    Attributes:
    - result (bool): Indicates the result of the test. Default is False.
    - registry (CollectorRegistry): Registry for Prometheus metrics.
    """
    result = False
    registry = None

    def test(self, metric: Gauge) -> bool:
        """
        Perform a test to check the health/status of the service.

        This method should be implemented by each subclass to perform the actual health check.

        Parameters:
        - metric (Gauge): Prometheus gauge metric to update with the test result.

        Returns:
        - bool: Result of the test (True for success, False for failure).
        """
        raise NotImplementedError("Implement this method in each subclass.")
