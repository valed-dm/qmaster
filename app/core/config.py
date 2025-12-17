from enum import Enum
from pathlib import Path
from typing import Annotated

from pydantic import AnyHttpUrl
from pydantic import Field
from pydantic_settings import SettingsConfigDict

from app.core.db_config import DatabaseSettings


class Environment(str, Enum):
    """Runtime environment options."""

    DEVELOPMENT = "DEVELOPMENT"
    PRODUCTION = "PRODUCTION"


class Settings(DatabaseSettings):
    """
    Application settings with environment variable loading.

    Inherits database settings from DatabaseSettings and adds
    application-specific configuration, authentication parameters,
    monitoring options, and infrastructure (Redis/RabbitMQ) settings.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Core Application Settings ---
    APP_NAME: Annotated[
        str,
        Field(
            ...,
            validation_alias="APP_NAME",
            description="Name of the application.",
            examples=["My App"],
        ),
    ]

    ENVIRONMENT: Annotated[
        Environment,
        Field(
            default=Environment.DEVELOPMENT,
            validation_alias="ENVIRONMENT",
            description="Runtime environment.",
        ),
    ]

    LOG_LEVEL: Annotated[
        str,
        Field(
            default="INFO",
            validation_alias="LOG_LEVEL",
            description="Application log level.",
            pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$",
        ),
    ]

    # --- HTTP/Network Settings ---
    AIOHTTP_TIMEOUT_SECONDS: Annotated[
        int,
        Field(
            default=30,
            validation_alias="AIOHTTP_TIMEOUT_SECONDS",
            description="Timeout for HTTP requests in seconds.",
            gt=0,
        ),
    ]

    CORS_ORIGINS: Annotated[
        list[AnyHttpUrl],
        Field(
            default_factory=list,
            validation_alias="CORS_ORIGINS",
            description="Allowed CORS origins.",
        ),
    ]

    # --- Monitoring ---
    GLITCHTIP_DSN: Annotated[
        str | None,
        Field(
            default=None,
            validation_alias="GLITCHTIP_DSN",
            description="Error monitoring DSN (set to None to disable).",
            min_length=0,
            examples=["https://publickey@your-subdomain.example.com/1"],
        ),
    ]

    # --- Authentication Settings ---
    ACCESS_TOKEN_EXPIRE_MINUTES: Annotated[
        int,
        Field(
            default=30,
            validation_alias="ACCESS_TOKEN_EXPIRE_MINUTES",
            description="JWT expiration time in minutes.",
            gt=0,
        ),
    ]

    ALGORITHM: Annotated[
        str,
        Field(
            default="HS256",
            validation_alias="ALGORITHM",
            description="JWT signing algorithm.",
        ),
    ]

    SECRET_KEY: Annotated[
        str,
        Field(
            ...,
            validation_alias="SECRET_KEY",
            description="JWT signing secret.",
            min_length=32,
        ),
    ]

    TOKEN_TYPE: Annotated[
        str,
        Field(
            default="Bearer",
            validation_alias="TOKEN_TYPE",
            description="JWT token type prefix.",
        ),
    ]

    # --- Infrastructure Settings (Redis & RabbitMQ) ---
    REDIS_HOST: Annotated[
        str,
        Field(
            default="redis",
            validation_alias="REDIS_HOST",
            description="Redis host address.",
        ),
    ]

    REDIS_PORT: Annotated[
        int,
        Field(
            default=6379,
            validation_alias="REDIS_PORT",
            description="Redis port.",
        ),
    ]

    RABBITMQ_HOST: Annotated[
        str,
        Field(
            default="rabbitmq",
            validation_alias="RABBITMQ_HOST",
            description="RabbitMQ host address.",
        ),
    ]

    RABBITMQ_PORT: Annotated[
        int,
        Field(
            default=5672,
            validation_alias="RABBITMQ_PORT",
            description="RabbitMQ port.",
        ),
    ]

    RABBITMQ_USER: Annotated[
        str,
        Field(
            default="guest",
            validation_alias="RABBITMQ_USER",
            description="RabbitMQ username.",
        ),
    ]

    RABBITMQ_PASSWORD: Annotated[
        str,
        Field(
            default="guest",
            validation_alias="RABBITMQ_PASSWORD",
            description="RabbitMQ password.",
        ),
    ]

    @property
    def REDIS_URL(self) -> str:
        """Construct Redis Connection URL."""
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"

    @property
    def CELERY_BROKER_URL(self) -> str:
        """Construct RabbitMQ Broker URL."""
        return f"amqp://{self.RABBITMQ_USER}:{self.RABBITMQ_PASSWORD}@{self.RABBITMQ_HOST}:{self.RABBITMQ_PORT}//"

    @property
    def CELERY_RESULT_BACKEND(self) -> str:
        """Use Redis as the result backend for Celery."""
        return self.REDIS_URL

    # --- Path Settings ---
    BASE_DIR: Path = Path(__file__).resolve().parent.parent

    @property
    def LOGS_DIR(self) -> Path:
        """Directory path for application log files."""
        return self.BASE_DIR / "logs"

    @property
    def LOG_FILE(self) -> Path:
        """Full path to the main application log file."""
        return self.LOGS_DIR / "scoped_auth.log"

    # --- Test Settings ---
    TEST_USERNAME: Annotated[
        str,
        Field(..., validation_alias="TEST_USERNAME", description="Test user username."),
    ]

    TEST_PASSWORD: Annotated[
        str,
        Field(..., validation_alias="TEST_PASSWORD", description="Test user password."),
    ]

    TEST_EMAIL: Annotated[
        str,
        Field(
            ...,
            validation_alias="TEST_EMAIL",
            description="Test user email.",
            pattern=r"^[^@]+@[^@]+\.[^@]+$",
        ),
    ]

    TEST_FULL_NAME: Annotated[
        str,
        Field(
            ..., validation_alias="TEST_FULL_NAME", description="Test user full name."
        ),
    ]

    TEST_SCOPE: Annotated[
        str,
        Field(
            ...,
            validation_alias="TEST_SCOPE",
            description="Test user permissions scope.",
        ),
    ]


settings = Settings()
