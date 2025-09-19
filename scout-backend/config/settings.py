"""
SCOUT Configuration Settings
Central configuration for the SCOUT AI system
"""

import os
from typing import Dict, Any
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    app_name: str = "SCOUT AI System"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # AWS Configuration
    aws_region: str = "eu-north-1"
    aws_access_key_id: str = Field(default="", env="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: str = Field(default="", env="AWS_SECRET_ACCESS_KEY")
    
    # Legacy API Key (not used, but needed to avoid validation error)
    bedrock_api_key_legacy: str = Field(default="", alias="bedrockapikey-l77x-at-547688237843")
    
    # Bedrock Configuration
    bedrock_model_id: str = "arn:aws:bedrock:eu-north-1:547688237843:inference-profile/eu.anthropic.claude-sonnet-4-20250514-v1:0"
    bedrock_max_tokens: int = 4000
    bedrock_temperature: float = 0.1
    
    # S3 Configuration
    s3_bucket_name: str = "scout-documents"
    s3_reports_bucket: str = "scout-reports"
    
    # Agent Configuration
    max_concurrent_agents: int = 4
    agent_timeout_seconds: int = 1800  # 30 minutes
    
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: list = ["http://localhost:3000", "http://localhost:5173"]

    # Storage Configuration
    storage_backend: str = "local" # 'local' or 's3'
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Global settings instance
settings = Settings()

# Agent configurations
AGENT_CONFIGS = {
    "planner": {
        "name": "Planner Agent",
        "description": "Converts business plans into structured research tasks",
        "max_tokens": 4000,
        "temperature": 0.1,
        "timeout": 300  # 5 minutes
    },
    "orchestrator": {
        "name": "Orchestrator Agent", 
        "description": "Coordinates and monitors specialist agents",
        "max_tokens": 2000,
        "temperature": 0.1,
        "timeout": 1800  # 30 minutes
    },
    "competition": {
        "name": "Competition Agent",
        "description": "Deep competitor intelligence gathering",
        "max_tokens": 4000,
        "temperature": 0.2,
        "timeout": 1800  # 30 minutes
    },
    "market": {
        "name": "Market Agent",
        "description": "Comprehensive market and customer analysis", 
        "max_tokens": 4000,
        "temperature": 0.2,
        "timeout": 1800  # 30 minutes
    },
    "financial": {
        "name": "Financial Agent",
        "description": "Business model and financial viability analysis",
        "max_tokens": 4000,
        "temperature": 0.1,
        "timeout": 1800  # 30 minutes
    },
    "risk": {
        "name": "Risk Agent",
        "description": "Identifies and analyzes all potential threats",
        "max_tokens": 4000,
        "temperature": 0.2,
        "timeout": 1800  # 30 minutes
    },
    "synthesis": {
        "name": "Synthesis Agent",
        "description": "Transforms intelligence into executive reports",
        "max_tokens": 4000,
        "temperature": 0.1,
        "timeout": 1800  # 30 minutes
    }
}
