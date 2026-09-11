from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ModelKey = Literal["sol", "terra", "luna", "astra"]
Decision = Literal[
    "allowed", "needs_approval", "needs_info", "not_covered", "not_allowed"
]

MODEL_SPECS: dict[str, tuple[str, str]] = {
    "sol": ("gpt-5.6-sol", "2026-07-09"),
    "terra": ("gpt-5.6-terra", "2026-07-09"),
    "luna": ("gpt-5.6-luna", "2026-07-09"),
    "astra": ("gpt-6-astra", "2026-09-03"),
}


class Invocation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str = Field(min_length=1, max_length=2000)
    model_key: ModelKey
    case_id: str = Field(pattern=r"^[A-Za-z0-9_-]{1,64}$")
    run_id: str = Field(pattern=r"^[A-Za-z0-9_-]{1,80}$")


class PolicyAnswer(BaseModel):
    model_config = ConfigDict(extra="forbid")

    answer: str
    decision: Decision
    citations: list[str]
