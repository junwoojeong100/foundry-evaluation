import json
import logging
import os
from json import JSONDecodeError
from typing import Any

import httpx
from agent_framework.observability import enable_instrumentation
from agent_framework.exceptions import ChatClientException
from azure.ai.agentserver.invocations import InvocationAgentServerHost
from azure.ai.projects import AIProjectClient
from azure.core.credentials import TokenCredential
from azure.core.exceptions import AzureError
from openai import APIError
from pydantic import ValidationError
from starlette.requests import Request
from starlette.responses import JSONResponse

from contracts import Invocation
from policy_agent import answer_question
from settings import RuntimeConfig, credential

logger = logging.getLogger("learning-loop")
EXTERNAL_MODEL_KEY = "sol"


def invocation_payload(body: Any) -> Any:
    # Foundry target evaluation posts the rendered message content; its text holds an invocation or a plain question.
    if not (isinstance(body, dict) and body.get("type") == "input_text" and isinstance(body.get("text"), str)):
        return body
    try:
        parsed = json.loads(body["text"])
    except JSONDecodeError:
        parsed = None
    if isinstance(parsed, dict):
        return parsed
    return {"query": body["text"], "model_key": EXTERNAL_MODEL_KEY, "case_id": "external", "run_id": "foundry-evaluation"}


def telemetry_connection(config: RuntimeConfig, token_credential: TokenCredential) -> str | None:
    injected = os.environ.get("APPLICATIONINSIGHTS_CONNECTION_STRING")
    if injected:
        return injected
    if os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT"):
        return None
    if os.environ.get("LAB_AUTH_MODE") != "cli":
        raise ValueError("Hosted telemetry must be supplied through App Insights or OTLP configuration.")
    with AIProjectClient(endpoint=config.project_endpoint, credential=token_credential) as project:
        connection_string = project.telemetry.get_application_insights_connection_string()
    if not connection_string:
        raise ValueError("Connect Application Insights to the Foundry project before running.")
    return connection_string


def build_host() -> InvocationAgentServerHost:
    config = RuntimeConfig.from_env()
    os.environ.setdefault("AZURE_EXPERIMENTAL_ENABLE_GENAI_TRACING", "true")
    os.environ.setdefault("FOUNDRY_AGENT_NAME", config.agent_name)
    enable_instrumentation(enable_sensitive_data=False)
    token_credential = credential()
    app = InvocationAgentServerHost(
        applicationinsights_connection_string=telemetry_connection(config, token_credential),
        openapi_spec={
            "openapi": "3.1.0",
            "info": {"title": "Learning Loop Policy Agent", "version": "1.0.0"},
            "paths": {"/invocations": {"post": {
                "operationId": "answerPolicyQuestion",
                "requestBody": {"required": True, "content": {"application/json": {"schema": Invocation.model_json_schema()}}},
                "responses": {"200": {"description": "Policy answer and experiment lineage"}},
            }}},
        },
    )

    @app.invoke_handler
    async def handle(request: Request) -> JSONResponse:
        try:
            invocation = Invocation.model_validate(invocation_payload(await request.json()))
        except (ValidationError, JSONDecodeError) as exc:
            logger.warning("Invalid invocation: %s", type(exc).__name__)
            return JSONResponse(
                {"error": {"code": "invalid_request", "message": str(exc)}},
                status_code=422,
            )
        try:
            result = await answer_question(invocation, config, token_credential)
        except (httpx.HTTPError, AzureError, APIError, ChatClientException, ValueError) as exc:
            logger.exception("Agent invocation failed: %s", type(exc).__name__)
            return JSONResponse(
                {
                    "error": {
                        "code": "upstream_failure",
                        "message": type(exc).__name__,
                        "case_id": invocation.case_id,
                    }
                },
                status_code=502,
            )
        return JSONResponse(result)

    return app


if __name__ == "__main__":
    build_host().run()
