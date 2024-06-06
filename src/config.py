"""
Load Config
"""
import yaml
from src.logger import logger
from typing import Dict

class Config:
    """
    Configuration class to load and provide access to configuration settings from a YAML file.
    """

    @property
    def conf(self) -> Dict:
        """
        Load and return the configuration from a YAML file.

        This method attempts to read the configuration from a specified YAML file and
        returns it as a dictionary. If there is an error while loading the file, it logs the error
        and returns an empty dictionary.

        Returns:
        - Dict: The configuration settings loaded from the YAML file.
        """
        conf_file = "conf-test.yml"  # Test configuration file
        conf_file = "/config/conf.yml"  # Production configuration file

        try:
            # Open and read the YAML configuration file
            with open(conf_file) as f:
                configs = yaml.safe_load(f)
            logger.info(f"Configuration loaded: {configs}")
            return configs
        except Exception as e:
            logger.critical(f"Failed to load configuration: {e}")
            return {}

    @property
    def services(self) -> Dict:
        """
        Get the 'services' section from the configuration.

        This method retrieves the 'services' section from the loaded configuration dictionary.

        Returns:
        - Dict: The 'services' section of the configuration, or None if not present.
        """
        return self.conf.get("services", None)
