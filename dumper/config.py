"""
Infrastructure configuration for CDK deployment.

Reads from config.toml with validation via Pydantic.
"""

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppConfig(BaseSettings):
    """Application configuration section."""

    model_config = SettingsConfigDict(
        toml_file="config.toml",
        env_prefix="APP_",
    )

    name: str = Field(description="Application name (used for AWS resource naming)")
    docker_context: str = Field(default=".", description="Docker build context path")
    dockerfile: str = Field(default="src/Dockerfile", description="Path to Dockerfile")


class ContainerConfig(BaseSettings):
    """Container configuration section."""

    model_config = SettingsConfigDict(
        toml_file="config.toml",
        env_prefix="CONTAINER_",
    )

    port: int = Field(default=80, description="Container port")
    health_check_path: str = Field(
        default="/_stcore/health", description="Health check endpoint"
    )
    cpu: int = Field(default=256, description="CPU units")
    memory: int = Field(default=512, description="Memory in MiB")
    desired_count: int = Field(default=1, description="Desired task count")


class Config:
    """Root configuration combining all sections."""

    def __init__(self, config_path: str | Path = "config.toml"):
        # Override toml_file for both configs
        AppConfig.model_config["toml_file"] = str(config_path)
        ContainerConfig.model_config["toml_file"] = str(config_path)

        self.app = AppConfig()
        self.container = ContainerConfig()

    @property
    def auth_secret_name(self) -> str:
        """Generate auth secret name following pattern: {app_name}/access."""
        return f"{self.app.name}/access"


def load_config(config_path: str | Path = "config.toml") -> Config:
    """Load and validate configuration from TOML file."""
    return Config(config_path)
