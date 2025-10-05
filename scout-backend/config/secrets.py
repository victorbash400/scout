"""
AWS Secrets Manager integration for secure API key storage
"""

import boto3
import json
import logging
import os
from typing import Dict, Optional
from botocore.exceptions import ClientError, NoCredentialsError

logger = logging.getLogger(__name__)

class SecretsManager:
    """Manages retrieval of secrets from AWS Secrets Manager with fallback to environment variables."""
    
    def __init__(self, region: str = "eu-north-1"):
        """
        Initialize the SecretsManager.
        
        :param region: AWS region where secrets are stored
        """
        self.region = region
        self.client = None
        self._secrets_cache: Dict[str, str] = {}
        
        # Try to initialize AWS client
        try:
            self.client = boto3.client('secretsmanager', region_name=region)
            logger.info(f"Initialized AWS Secrets Manager client for region {region}")
        except (NoCredentialsError, Exception) as e:
            logger.warning(f"Could not initialize AWS Secrets Manager client: {e}")
            logger.info("Will fallback to environment variables for secrets")
    
    def get_secret(self, secret_name: str, fallback_env_var: Optional[str] = None) -> Optional[str]:
        """
        Retrieve a secret from AWS Secrets Manager with fallback to environment variables.
        
        :param secret_name: Name of the secret in AWS Secrets Manager
        :param fallback_env_var: Environment variable name to use as fallback
        :return: Secret value or None if not found
        """
        # Check cache first
        if secret_name in self._secrets_cache:
            return self._secrets_cache[secret_name]
        
        # Try AWS Secrets Manager first
        if self.client:
            try:
                response = self.client.get_secret_value(SecretId=secret_name)
                secret_value = response['SecretString']
                
                # Cache the secret
                self._secrets_cache[secret_name] = secret_value
                logger.info(f"Retrieved secret '{secret_name}' from AWS Secrets Manager")
                return secret_value
                
            except ClientError as e:
                error_code = e.response['Error']['Code']
                if error_code == 'ResourceNotFoundException':
                    logger.warning(f"Secret '{secret_name}' not found in AWS Secrets Manager")
                elif error_code == 'InvalidRequestException':
                    logger.error(f"Invalid request for secret '{secret_name}': {e}")
                elif error_code == 'InvalidParameterException':
                    logger.error(f"Invalid parameter for secret '{secret_name}': {e}")
                else:
                    logger.error(f"Error retrieving secret '{secret_name}': {e}")
            except Exception as e:
                logger.error(f"Unexpected error retrieving secret '{secret_name}': {e}")
        
        # Fallback to environment variable
        if fallback_env_var:
            env_value = os.getenv(fallback_env_var)
            if env_value:
                logger.info(f"Using environment variable '{fallback_env_var}' for secret '{secret_name}'")
                self._secrets_cache[secret_name] = env_value
                return env_value
            else:
                logger.warning(f"Environment variable '{fallback_env_var}' not found")
        
        logger.error(f"Could not retrieve secret '{secret_name}' from AWS or environment variables")
        return None
    
    def get_json_secret(self, secret_name: str, fallback_env_vars: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """
        Retrieve a JSON secret from AWS Secrets Manager with fallback to multiple environment variables.
        
        :param secret_name: Name of the JSON secret in AWS Secrets Manager
        :param fallback_env_vars: Dictionary mapping JSON keys to environment variable names
        :return: Dictionary of secret values
        """
        # Try AWS Secrets Manager first
        if self.client:
            try:
                response = self.client.get_secret_value(SecretId=secret_name)
                secret_json = json.loads(response['SecretString'])
                logger.info(f"Retrieved JSON secret '{secret_name}' from AWS Secrets Manager")
                return secret_json
                
            except ClientError as e:
                logger.warning(f"Could not retrieve JSON secret '{secret_name}' from AWS: {e}")
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in secret '{secret_name}': {e}")
            except Exception as e:
                logger.error(f"Unexpected error retrieving JSON secret '{secret_name}': {e}")
        
        # Fallback to environment variables
        if fallback_env_vars:
            result = {}
            for key, env_var in fallback_env_vars.items():
                value = os.getenv(env_var)
                if value:
                    result[key] = value
                    logger.info(f"Using environment variable '{env_var}' for secret key '{key}'")
                else:
                    logger.warning(f"Environment variable '{env_var}' not found for key '{key}'")
            
            if result:
                return result
        
        logger.error(f"Could not retrieve any values for JSON secret '{secret_name}'")
        return {}
    
    def load_api_keys(self) -> Dict[str, str]:
        """
        Load all required API keys for the SCOUT application.
        
        :return: Dictionary of API keys
        """
        api_keys = {}
        
        # Tavily API Key
        tavily_key = self.get_secret(
            secret_name="scout/tavily-api-key",
            fallback_env_var="TAVILY_API_KEY"
        )
        if tavily_key:
            api_keys['tavily_api_key'] = tavily_key
        
        # Google Places API Key
        google_key = self.get_secret(
            secret_name="scout/google-places-key", 
            fallback_env_var="GOOGLE_PLACES_API_KEY"
        )
        if google_key:
            api_keys['google_places_api_key'] = google_key
        
        # Perplexity API Key
        perplexity_key = self.get_secret(
            secret_name="scout/perplexity-api-key",
            fallback_env_var="PERPLEXITY_API_KEY"
        )
        if perplexity_key:
            api_keys['perplexity_api_key'] = perplexity_key
        
        # AWS credentials (if needed for external services)
        aws_access_key = self.get_secret(
            secret_name="scout/aws-access-key",
            fallback_env_var="AWS_ACCESS_KEY_ID"
        )
        if aws_access_key:
            api_keys['aws_access_key_id'] = aws_access_key
        
        aws_secret_key = self.get_secret(
            secret_name="scout/aws-secret-key",
            fallback_env_var="AWS_SECRET_ACCESS_KEY"
        )
        if aws_secret_key:
            api_keys['aws_secret_access_key'] = aws_secret_key
        
        logger.info(f"Loaded {len(api_keys)} API keys successfully")
        return api_keys
    
    def test_connection(self) -> bool:
        """
        Test connection to AWS Secrets Manager.
        
        :return: True if connection is successful, False otherwise
        """
        if not self.client:
            return False
        
        try:
            # Try to list secrets (this requires minimal permissions)
            self.client.list_secrets(MaxResults=1)
            logger.info("AWS Secrets Manager connection test successful")
            return True
        except Exception as e:
            logger.error(f"AWS Secrets Manager connection test failed: {e}")
            return False
    
    def clear_cache(self):
        """Clear the secrets cache."""
        self._secrets_cache.clear()
        logger.info("Secrets cache cleared")

# Global secrets manager instance
secrets_manager = SecretsManager()