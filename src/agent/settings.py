import os
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

from azure.core.credentials import TokenCredential
from azure.core.credentials_async import AsyncTokenCredential
from azure.identity import AzureCliCredential, DefaultAzureCredential
from azure.identity.aio import AzureCliCredential as AsyncAzureCliCredential
from azure.identity.aio import DefaultAzureCredential as AsyncDefaultAzureCredential
from dotenv import load_dotenv

from contracts import MODEL_SPECS

SOURCE_DIR = Path(__file__).resolve().parent
REPO_ROOT = SOURCE_DIR.parent.parent


def load_settings_env() -> None:
    load_dotenv(REPO_ROOT / ".env", override=False)
    load_dotenv(SOURCE_DIR / ".env", override=False)


def required(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value or "<" in value or ">" in value:
        raise ValueError(f"{name} must be configured; placeholders are not allowed.")
    return value


def safe_name(value: str, field: str) -> str:
    if not re.fullmatch(r"[a-z][a-z0-9-]{2,49}", value):
        raise ValueError(f"{field} must be 3-50 lowercase letters/digits/hyphens.")
    return value


def azure_url(value: str, suffix: str, field: str) -> str:
    parsed = urlparse(value)
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or not parsed.hostname.endswith(suffix)
        or parsed.username
        or parsed.password
        or parsed.port
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError(f"{field} must be an HTTPS Azure endpoint, without credentials.")
    return value.rstrip("/")


def credential() -> TokenCredential:
    mode = os.environ.get("LAB_AUTH_MODE", "managed")
    if mode == "cli":
        return AzureCliCredential(
            subscription=required("AZURE_SUBSCRIPTION_ID"),
            process_timeout=60,
        )
    if mode != "managed":
        raise ValueError("LAB_AUTH_MODE must be cli or managed.")
    return DefaultAzureCredential(
        exclude_azure_cli_credential=True,
        exclude_developer_cli_credential=True,
        exclude_interactive_browser_credential=True,
    )


def async_credential() -> AsyncTokenCredential:
    mode = os.environ.get("LAB_AUTH_MODE", "managed")
    if mode == "cli":
        return AsyncAzureCliCredential(
            subscription=required("AZURE_SUBSCRIPTION_ID"), process_timeout=60
        )
    if mode != "managed":
        raise ValueError("LAB_AUTH_MODE must be cli or managed.")
    return AsyncDefaultAzureCredential(
        exclude_azure_cli_credential=True,
        exclude_developer_cli_credential=True,
        exclude_interactive_browser_credential=True,
    )


@dataclass(frozen=True)
class RuntimeConfig:
    project_endpoint: str
    model_endpoint: str
    search_endpoint: str
    prefix: str
    agent_name: str
    deployments: dict[str, str]
    prompt_version: str
    as_of_date: str
    max_output_tokens: int

    @classmethod
    def from_env(cls) -> "RuntimeConfig":
        load_settings_env()
        version = os.environ.get("LAB_PROMPT_VERSION", "v1")
        if version not in {"v1", "v2"}:
            raise ValueError("LAB_PROMPT_VERSION must be v1 or v2.")
        as_of = os.environ.get("LAB_AS_OF_DATE", "2026-09-10")
        date.fromisoformat(as_of)
        token_limit = int(os.environ.get("LAB_MAX_OUTPUT_TOKENS", "2048"))
        if not 256 <= token_limit <= 4096:
            raise ValueError("LAB_MAX_OUTPUT_TOKENS must be between 256 and 4096.")
        return cls(
            project_endpoint=azure_url(
                required("FOUNDRY_PROJECT_ENDPOINT"),
                ".services.ai.azure.com",
                "FOUNDRY_PROJECT_ENDPOINT",
            ),
            model_endpoint=azure_url(
                required("AZURE_OPENAI_ENDPOINT"),
                ".openai.azure.com",
                "AZURE_OPENAI_ENDPOINT",
            ),
            search_endpoint=azure_url(
                required("AZURE_SEARCH_ENDPOINT"),
                ".search.windows.net",
                "AZURE_SEARCH_ENDPOINT",
            ),
            prefix=safe_name(required("LAB_PREFIX"), "LAB_PREFIX"),
            agent_name=safe_name(required("LAB_AGENT_NAME"), "LAB_AGENT_NAME"),
            deployments={
                key: safe_name(required(f"MODEL_{key.upper()}_DEPLOYMENT"), key)
                for key in MODEL_SPECS
            },
            prompt_version=version,
            as_of_date=as_of,
            max_output_tokens=token_limit,
        )

    @property
    def index_name(self) -> str:
        return f"{self.prefix}-policies"

    @property
    def source_name(self) -> str:
        return f"{self.prefix}-source"

    @property
    def kb_name(self) -> str:
        return f"{self.prefix}-kb"
