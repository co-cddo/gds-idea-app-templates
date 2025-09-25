from dataclasses import dataclass, field


@dataclass
class WebAppContainerProperties:
    """A structured class for default WebApp Container settings."""

    # ECS Task settings
    cpu: int = 256
    """The number of CPU units to reserve for the container (256 = 0.25 vCPU)."""

    memory_limit_mib: int = 512
    """The amount of memory (in MiB) to reserve for the container."""

    desired_count: int = 1
    """The desired number of tasks for the service."""

    container_port: int = 80
    """The port number on the container that is bound to the host port."""

    environment_variables: dict[str, str] = field(default_factory=dict)
    """A dictionary of environment variables to pass to the container."""

    # ALB Health Check settings
    health_check_path: str = "/"
    """The destination for the health check request."""
