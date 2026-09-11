# 출처와 사실 확인

확인일: **2026-09-10**. 아래 내용은 직접 확인한 문서와 서비스 조회를 기준으로 한다. 검색 도구의 요약만으로 모델 지원이나 인용문을 확정하지 않았다.

| 출처 | 이 가이드에서 사용한 근거 |
|---|---|
| [Satya Nadella 직접 게시물](https://x.com/satyanadella/status/2066182223213293753) | 기업이 learning loop를 소유하고, 범용 모델을 교체해도 조직의 지식이 남아야 한다는 문제의식. 이 가이드의 실습 구조는 작성자의 교육적 해석이다. |
| [Introducing CoreAI, 2025-01-13](https://blogs.microsoft.com/blog/2025/01/13/introducing-core-ai-platform-and-tools/) | agentic application stack, management/observability, 제품과 플랫폼 사이의 feedback loop. |
| [Foundry 모델 카탈로그](https://ai.azure.com/explore/models) | 모델 ID 발견. 실제 사용 가능성은 대상 구독의 지역별 모델 목록·할당량·배포·호출로 따로 확인한다. |
| [Foundry Models sold by Azure](https://learn.microsoft.com/azure/ai-foundry/foundry-models/concepts/models-sold-directly-by-azure) | 모델·지역·배포 유형의 구분. |
| [Agent Framework Foundry hosting](https://learn.microsoft.com/agent-framework/hosting/foundry-hosted-agent?pivots=programming-language-python) | Python Agent, Invocations/Responses hosting. 관리형 hosting 서비스와 통합 SDK의 출시 상태 구분. |
| [Agent Framework OpenAI 프로토콜 adapter](https://learn.microsoft.com/agent-framework/integrations/by-component/model-providers/openai) | 넓은 모델 호환성이 필요한 경우 `OpenAIChatCompletionClient` 사용. Azure Foundry 계정으로 인증된 client를 주입한다. |
| [AIProjectClient API](https://learn.microsoft.com/python/api/azure-ai-projects/azure.ai.projects.aiprojectclient) | `get_openai_client()`의 공식 `base_url` 및 token-provider override로 같은 계정 endpoint를 사용한다. |
| [Azure AI Agent Server Core](https://learn.microsoft.com/python/api/overview/azure/ai-agentserver-core-readme?view=azure-python) | readiness, request context, 자동 OpenTelemetry export. |
| [Azure AI Agent Server Invocations](https://learn.microsoft.com/python/api/overview/azure/ai-agentserver-invocations-readme?view=azure-python) | `InvocationAgentServerHost`와 명시적 JSON 입출력. |
| [Hosted session 관리](https://learn.microsoft.com/azure/foundry/agents/how-to/manage-hosted-sessions?pivots=python) | SDK로 버전에 고정한 session을 만들고 `agent_session_id`로 HTTP 요청을 재사용하는 batch 경로. |
| [구조화 출력](https://learn.microsoft.com/agent-framework/agents/structured-outputs?pivots=programming-language-python) | 서비스 강제 schema와 애플리케이션의 JSON 검증 구분. 실제 Astra 제약 때문에 본문은 공통 JSON 텍스트 계약과 Pydantic 검증을 사용한다. |
| [Foundry IQ hosted quickstart](https://learn.microsoft.com/azure/foundry/agents/quickstarts/quickstart-foundry-iq-hosted-agent) | knowledge source/base, Search managed identity, hosted agent 읽기 권한. 본 실습은 toolbox 대신 공식 REST retrieve를 사용한다. |
| [Agentic retrieval pipeline](https://learn.microsoft.com/azure/search/agentic-retrieval-how-to-create-pipeline) | semantic index, knowledge source, knowledge base, extractiveData. |
| [Knowledge base retrieve](https://learn.microsoft.com/azure/search/agentic-retrieval-how-to-retrieve) | 실제 retrieval 요청, activity, references, docKey/sourceData의 의미. |
| [Foundry dataset cloud evaluation](https://learn.microsoft.com/azure/foundry/observability/how-to/cloud-evaluation-datasets) | 새 Foundry Evals API, `jsonl`, `file_content`, `azure_ai_evaluator`, 명시적 field mapping. |
| [Hosted agent 평가 quickstart](https://learn.microsoft.com/azure/foundry/observability/quickstarts/quickstart-evaluate-hosted-agent) | agent-target 평가와 데이터셋 평가의 구분, judge deployment. |
| [Foundry tracing 설정](https://learn.microsoft.com/azure/foundry/observability/how-to/trace-agent-setup) | Application Insights 연결, server/client tracing, 개인정보·보존·지연 주의사항. |
| [Agent Monitoring Dashboard](https://learn.microsoft.com/azure/foundry/observability/how-to/how-to-monitor-agents-dashboard) | operational metrics, 평가 결과, continuous evaluation의 구분. |
| [OpenTelemetry sampling](https://learn.microsoft.com/azure/azure-monitor/app/opentelemetry-configuration#enable-sampling) | Python의 기본 rate-limited sampling과 `microsoft.fixed_percentage`/`1.0` 설정. 실습 데이터만 100% 수집한다. |
| [공식 Python hosted 샘플](https://github.com/microsoft-foundry/foundry-samples/tree/main/samples/python/hosted-agents/agent-framework) | azd direct-code deployment, Python runtime, protocol manifest 형식. |

## 모델 조회 결과의 해석

Foundry MCP `model_catalog_list`와 Azure CLI `az cognitiveservices model list --location swedencentral`에서 다음을 확인했다.

| 모델 | 버전 | 필요한 capability | 실습 SKU |
|---|---|---|---|
| gpt-5.6-sol | 2026-07-09 | responses, chatCompletion | GlobalStandard |
| gpt-5.6-terra | 2026-07-09 | responses, chatCompletion | GlobalStandard |
| gpt-5.6-luna | 2026-07-09 | responses, chatCompletion | GlobalStandard |
| gpt-6-astra | 2026-09-03 | responses, chatCompletion | GlobalStandard |

카탈로그에 나온다는 사실과 실제 구독에서 호출에 성공했다는 사실은 다르다. 실행 확인 보고서는 이를 별도로 기록한다. CLI에서 선택 가능한 모델 이름을 Azure 배포 ID로 간주하지 않았다.

## 평가 해석의 한계

6개 dev/4개 holdout은 실습용 smoke dataset이다. 통계적 유의성, 실제 업무 전체의 품질, 한국어 전체 성능, 보안, production readiness를 보증하지 않는다. 검색 근거·네트워크 지연·judge 변동이 함께 포함되는 **end-to-end 시스템 비교**다.
