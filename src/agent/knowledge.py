import asyncio
import hashlib
import json
from typing import Any
from urllib.parse import quote

import httpx
from azure.core.credentials import TokenCredential
from opentelemetry import trace

from settings import RuntimeConfig

SEARCH_API_VERSION = "2026-05-01-preview"
SEARCH_SCOPE = "https://search.azure.com/.default"


def canonical_context(documents: list[dict[str, str]]) -> tuple[str, str]:
    ordered = sorted(documents, key=lambda doc: doc["id"])
    text = json.dumps(ordered, ensure_ascii=False, sort_keys=True)
    return text, hashlib.sha256(text.encode()).hexdigest()


async def retrieve(
    config: RuntimeConfig, token_credential: TokenCredential, query: str
) -> dict[str, Any]:
    tracer = trace.get_tracer("learning-loop")
    with tracer.start_as_current_span("foundry_iq.retrieve") as span:
        span.set_attributes(
            {
                "gen_ai.operation.name": "execute_tool",
                "gen_ai.tool.name": "foundry_iq_retrieve",
                "lab.knowledge_base": config.kb_name,
            }
        )
        access_token = await asyncio.to_thread(token_credential.get_token, SEARCH_SCOPE)
        headers = {"Authorization": f"Bearer {access_token.token}"}
        async with httpx.AsyncClient(
            headers=headers, timeout=120, follow_redirects=False
        ) as client:
            response = await client.post(
                f"{config.search_endpoint}/knowledgebases/{config.kb_name}/retrieve",
                params={"api-version": SEARCH_API_VERSION},
                json={
                    "messages": [
                        {"role": "user", "content": [{"type": "text", "text": query}]}
                    ],
                    "includeActivity": True,
                    "knowledgeSourceParams": [
                        {
                            "kind": "searchIndex",
                            "knowledgeSourceName": config.source_name,
                            "includeReferences": True,
                            "includeReferenceSourceData": True,
                        }
                    ],
                },
            )
            response.raise_for_status()
            payload = response.json()
            references = payload.get("references")
            activity = payload.get("activity")
            if not isinstance(references, list) or not isinstance(activity, list):
                raise ValueError("Foundry IQ response is missing references/activity.")
            if any(item.get("error") for item in activity):
                raise ValueError("Foundry IQ reported a failed retrieval activity.")
            documents: dict[str, dict[str, str]] = {}
            for reference in references:
                source = reference.get("sourceData")
                if not isinstance(source, dict):
                    key = reference.get("docKey")
                    if not isinstance(key, str) or not key:
                        raise ValueError("A Foundry IQ reference has no source data or docKey.")
                    lookup = await client.get(
                        f"{config.search_endpoint}/indexes/{config.index_name}/docs/{quote(key, safe='')}",
                        params={"api-version": SEARCH_API_VERSION},
                    )
                    lookup.raise_for_status()
                    source = lookup.json()
                if not all(isinstance(source.get(k), str) for k in ("id", "title", "content")):
                    raise ValueError("Retrieved source lacks id/title/content strings.")
                documents[source["id"]] = {
                    key: source[key] for key in ("id", "title", "content")
                }
        context, context_hash = canonical_context(list(documents.values()))
        span.set_attribute("lab.reference_count", len(documents))
        span.set_attribute("lab.context_hash", context_hash)
        return {
            "knowledge_base": config.kb_name,
            "context": context,
            "context_hash": context_hash,
            "documents": list(documents.values()),
            "references": references,
            "activity": activity,
        }
