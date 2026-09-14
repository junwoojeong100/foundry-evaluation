# 절차별 실제 화면과 통합 영상

**CLI와 실제 Azure / Foundry 포털을 실습가이드 순서로 연결한 기록입니다.**

[통합 영상 바로 재생](https://github.com/user-attachments/assets/98446bdb-072d-44a5-95d7-4965ccf1c010) · [로컬 챕터 플레이어 사용법](#로컬에서-챕터를-눌러-재생하기) · [챕터](assets/live-20260914-2034/chapters.txt) · [한국어 자막](assets/live-20260914-2034/captions.ko.srt)

GitHub에서는 아래 플레이어의 재생 버튼을 누르거나 위 **바로 재생** 링크를 사용합니다. 영상 원본은 저장소에 보존하고, 재생 링크는 GitHub의 동영상 첨부 주소를 사용합니다.

https://github.com/user-attachments/assets/98446bdb-072d-44a5-95d7-4965ccf1c010

영상 00:21:55 · CLI 78개 절차 · 포털 43개 절차. 실패한 시도도 성공으로 바꾸지 않고 구분했습니다.

실습 조작과 녹화는 Playwright headless입니다. 인증만 사용자가 별도 창에서 수행했으며, 로그인·PIN 화면은 녹화하지 않았습니다. CLI는 실제 명령 출력을 보여 주는 로컬 녹화 콘솔이며 Cloud Shell 화면이 아닙니다.

대기·화면 확인 구간은 줄였고, 설명 띠는 원래 화면 아래에 추가했습니다. 원본의 실행 시각과 편집 위치는 별도로 보존합니다. 영상 길이를 Azure 준비·실습의 실제 소요 시간으로 해석하지 않습니다.

사진의 개인 경로·구독·리소스 이름을 그대로 복사하지 말고 **본문의 명령**과 본인 설정을 사용하세요.

| 절차 | 화면 | 결과 | 시작 | 실행 전 | 실행 후 |
|---|---|---|---|---|---|
| `00-01-source` 새 실행용 소스와 설정 준비 | CLI | 실행 완료 | 00:00:00 | [전](assets/live-20260914-2034/screenshots/00-01-source-before.webp) | [후](assets/live-20260914-2034/screenshots/00-01-source-after.webp) |
| `00-02-venv` Python 3.13 가상환경 생성 | CLI | 실행 완료 | 00:00:04 | [전](assets/live-20260914-2034/screenshots/00-02-venv-before.webp) | [후](assets/live-20260914-2034/screenshots/00-02-venv-after.webp) |
| `00-02-check-packages` 새 가상환경의 의존성 확인 | CLI | **실패한 시도** | 00:00:10 | [전](assets/live-20260914-2034/screenshots/00-02-check-packages-before.webp) | [후](assets/live-20260914-2034/screenshots/00-02-check-packages-after.webp) |
| `00-03-dependencies` 고정된 의존성 설치 | CLI | 실행 완료 | 00:00:15 | [전](assets/live-20260914-2034/screenshots/00-03-dependencies-before.webp) | [후](assets/live-20260914-2034/screenshots/00-03-dependencies-after.webp) |
| `00-04-tests` Azure 실행 전 로컬 검사 | CLI | 실행 완료 | 00:00:27 | [전](assets/live-20260914-2034/screenshots/00-04-tests-before.webp) | [후](assets/live-20260914-2034/screenshots/00-04-tests-after.webp) |
| `00-05-account` 지정 계정과 구독 확인 | CLI | 실행 완료 | 00:00:39 | [전](assets/live-20260914-2034/screenshots/00-05-account-before.webp) | [후](assets/live-20260914-2034/screenshots/00-05-account-after.webp) |
| `00-06-groups` 기존 리소스 그룹의 소유권 조사 | CLI | 실행 완료 | 00:00:44 | [전](assets/live-20260914-2034/screenshots/00-06-groups-before.webp) | [후](assets/live-20260914-2034/screenshots/00-06-groups-after.webp) |
| `00-07-old-resources` 이전 환경이 공유 자원인지 확인 | CLI | 실행 완료 | 00:00:55 | [전](assets/live-20260914-2034/screenshots/00-07-old-resources-before.webp) | [후](assets/live-20260914-2034/screenshots/00-07-old-resources-after.webp) |
| `00-08-model-catalog` Sweden Central의 네 모델과 보조 모델 확인 | CLI | 실행 완료 | 00:01:05 | [전](assets/live-20260914-2034/screenshots/00-08-model-catalog-before.webp) | [후](assets/live-20260914-2034/screenshots/00-08-model-catalog-after.webp) |
| `00-09-quota` 실제 모델 배포의 남은 할당량 확인 | CLI | 실행 완료 | 00:01:17 | [전](assets/live-20260914-2034/screenshots/00-09-quota-before.webp) | [후](assets/live-20260914-2034/screenshots/00-09-quota-after.webp) |
| `00-10-identity` 지정 계정과 디렉터리 신원을 엄격하게 대조 | CLI | **실패한 시도** | 00:01:27 | [전](assets/live-20260914-2034/screenshots/00-10-identity-before.webp) | [후](assets/live-20260914-2034/screenshots/00-10-identity-after.webp) |
| `00-10-identity-retry` 지정 구독의 인증 토큰으로 신원 재확인 | CLI | 실행 완료 | 00:01:33 | [전](assets/live-20260914-2034/screenshots/00-10-identity-retry-before.webp) | [후](assets/live-20260914-2034/screenshots/00-10-identity-retry-after.webp) |
| `00-11-ownership` 기존 리포 전용 그룹과 공유 환경 구분 | CLI | 실행 완료 | 00:01:38 | [전](assets/live-20260914-2034/screenshots/00-11-ownership-before.webp) | [후](assets/live-20260914-2034/screenshots/00-11-ownership-after.webp) |
| `00-12-group` 새 전용 리소스 그룹 생성 | CLI | 실행 완료 | 00:01:44 | [전](assets/live-20260914-2034/screenshots/00-12-group-before.webp) | [후](assets/live-20260914-2034/screenshots/00-12-group-after.webp) |
| `00-P01-group` Azure Portal에서 새 리소스 그룹 열기 | PORTAL | 실행 완료 | 00:01:56 | [전](assets/live-20260914-2034/screenshots/00-P01-group-before.webp) | [후](assets/live-20260914-2034/screenshots/00-P01-group-after.webp) |
| `00-P02-tags` 새 전용 그룹의 소유권 태그 확인 | PORTAL | 실행 완료 | 00:02:08 | [전](assets/live-20260914-2034/screenshots/00-P02-tags-before.webp) | [후](assets/live-20260914-2034/screenshots/00-P02-tags-after.webp) |
| `00-13-foundry` 새 Foundry 계정 생성 | CLI | 실행 완료 | 00:02:20 | [전](assets/live-20260914-2034/screenshots/00-13-foundry-before.webp) | [후](assets/live-20260914-2034/screenshots/00-13-foundry-after.webp) |
| `00-14-project` 새 Foundry 프로젝트 생성 | CLI | 실행 완료 | 00:02:32 | [전](assets/live-20260914-2034/screenshots/00-14-project-before.webp) | [후](assets/live-20260914-2034/screenshots/00-14-project-after.webp) |
| `00-15-logs` 새 Log Analytics workspace 생성 | CLI | 실행 완료 | 00:02:44 | [전](assets/live-20260914-2034/screenshots/00-15-logs-before.webp) | [후](assets/live-20260914-2034/screenshots/00-15-logs-after.webp) |
| `00-16-insights` 새 Application Insights 생성 | CLI | 실행 완료 | 00:02:56 | [전](assets/live-20260914-2034/screenshots/00-16-insights-before.webp) | [후](assets/live-20260914-2034/screenshots/00-16-insights-after.webp) |
| `00-17-search` 새 Azure AI Search 서비스 생성 | CLI | **실패한 시도** | 00:03:05 | [전](assets/live-20260914-2034/screenshots/00-17-search-before.webp) | [후](assets/live-20260914-2034/screenshots/00-17-search-after.webp) |
| `00-17-search-status` Search의 실제 상태와 대기 원인 확인 | CLI | 실행 완료 | 00:03:17 | [전](assets/live-20260914-2034/screenshots/00-17-search-status-before.webp) | [후](assets/live-20260914-2034/screenshots/00-17-search-status-after.webp) |
| `00-18-user-foundry` 참가자의 Foundry 데이터 권한 설정 | CLI | 실행 완료 | 00:03:24 | [전](assets/live-20260914-2034/screenshots/00-18-user-foundry-before.webp) | [후](assets/live-20260914-2034/screenshots/00-18-user-foundry-after.webp) |
| `00-19-user-model` 참가자의 모델 추론 권한 설정 | CLI | 실행 완료 | 00:03:39 | [전](assets/live-20260914-2034/screenshots/00-19-user-model-before.webp) | [후](assets/live-20260914-2034/screenshots/00-19-user-model-after.webp) |
| `00-20-user-search-service` 지식 객체 작성 권한 설정 | CLI | 실행 완료 | 00:03:52 | [전](assets/live-20260914-2034/screenshots/00-20-user-search-service-before.webp) | [후](assets/live-20260914-2034/screenshots/00-20-user-search-service-after.webp) |
| `00-21-user-search-data` 합성 문서 적재 권한 설정 | CLI | 실행 완료 | 00:04:04 | [전](assets/live-20260914-2034/screenshots/00-21-user-search-data-before.webp) | [후](assets/live-20260914-2034/screenshots/00-21-user-search-data-after.webp) |
| `00-22-project-monitor` 프로젝트의 telemetry 조회 권한 설정 | CLI | 실행 완료 | 00:04:16 | [전](assets/live-20260914-2034/screenshots/00-22-project-monitor-before.webp) | [후](assets/live-20260914-2034/screenshots/00-22-project-monitor-after.webp) |
| `00-23-insights-connection` Foundry와 Application Insights 연결 | CLI | 실행 완료 | 00:04:28 | [전](assets/live-20260914-2034/screenshots/00-23-insights-connection-before.webp) | [후](assets/live-20260914-2034/screenshots/00-23-insights-connection-after.webp) |
| `00-24-search-connection` Foundry와 Search 연결 | CLI | 실행 완료 | 00:04:37 | [전](assets/live-20260914-2034/screenshots/00-24-search-connection-before.webp) | [후](assets/live-20260914-2034/screenshots/00-24-search-connection-after.webp) |
| `00-17-search-wait` 동일 Search 서비스의 준비 완료까지 이어서 확인 | CLI | 실행 완료 | 00:04:44 | [전](assets/live-20260914-2034/screenshots/00-17-search-wait-before.webp) | [후](assets/live-20260914-2034/screenshots/00-17-search-wait-after.webp) |
| `00-24-model-capacity` 같은 리전에서 실제 모델 capacity 확인 | CLI | 실행 완료 | 00:04:52 | [전](assets/live-20260914-2034/screenshots/00-24-model-capacity-before.webp) | [후](assets/live-20260914-2034/screenshots/00-24-model-capacity-after.webp) |
| `00-25-auxiliary` 고정 planner/judge 배포 생성 | CLI | 실행 완료 | 00:05:04 | [전](assets/live-20260914-2034/screenshots/00-25-auxiliary-before.webp) | [후](assets/live-20260914-2034/screenshots/00-25-auxiliary-after.webp) |
| `00-26-ready` 반환된 실제 endpoint와 새 환경 확인 | CLI | 실행 완료 | 00:05:15 | [전](assets/live-20260914-2034/screenshots/00-26-ready-before.webp) | [후](assets/live-20260914-2034/screenshots/00-26-ready-after.webp) |
| `00-27-preflight` 네 후보 배포 전 사전 점검 | CLI | 실행 완료 | 00:05:23 | [전](assets/live-20260914-2034/screenshots/00-27-preflight-before.webp) | [후](assets/live-20260914-2034/screenshots/00-27-preflight-after.webp) |
| `00-28-models` 실제 네 후보 모델 배포 | CLI | 실행 완료 | 00:05:35 | [전](assets/live-20260914-2034/screenshots/00-28-models-before.webp) | [후](assets/live-20260914-2034/screenshots/00-28-models-after.webp) |
| `00-29-bind` azd를 새 프로젝트에 바인딩 | CLI | 실행 완료 | 00:05:47 | [전](assets/live-20260914-2034/screenshots/00-29-bind-before.webp) | [후](assets/live-20260914-2034/screenshots/00-29-bind-after.webp) |
| `00-30-ready` 참가자 시작 조건 확인 | CLI | 실행 완료 | 00:06:04 | [전](assets/live-20260914-2034/screenshots/00-30-ready-before.webp) | [후](assets/live-20260914-2034/screenshots/00-30-ready-after.webp) |
| `00-31-calibrate` 고정 judge calibration 실행 | CLI | 실행 완료 | 00:06:16 | [전](assets/live-20260914-2034/screenshots/00-31-calibrate-before.webp) | [후](assets/live-20260914-2034/screenshots/00-31-calibrate-after.webp) |
| `00-P03-resources` 새 환경의 구성 자원 확인 | PORTAL | 실행 완료 | 00:06:28 | [전](assets/live-20260914-2034/screenshots/00-P03-resources-before.webp) | [후](assets/live-20260914-2034/screenshots/00-P03-resources-after.webp) |
| `00-P04-project` 새 Foundry 프로젝트의 Azure 정보 열기 | PORTAL | 실행 완료 | 00:06:40 | [전](assets/live-20260914-2034/screenshots/00-P04-project-before.webp) | [후](assets/live-20260914-2034/screenshots/00-P04-project-after.webp) |
| `00-P06-project-home` Foundry 프로젝트 홈과 endpoint 확인 | PORTAL | 실행 완료 | 00:06:52 | [전](assets/live-20260914-2034/screenshots/00-P06-project-home-before.webp) | [후](assets/live-20260914-2034/screenshots/00-P06-project-home-after.webp) |
| `00-P07-models` 실제 후보 네 모델과 별도 judge 배포 확인 | PORTAL | 실행 완료 | 00:07:04 | [전](assets/live-20260914-2034/screenshots/00-P07-models-before.webp) | [후](assets/live-20260914-2034/screenshots/00-P07-models-after.webp) |
| `A01-policies` 합성 정책 문서와 적용일 확인 | CLI | 실행 완료 | 00:07:16 | [전](assets/live-20260914-2034/screenshots/A01-policies-before.webp) | [후](assets/live-20260914-2034/screenshots/A01-policies-after.webp) |
| `A02-prepare-iq` Foundry IQ 지식 객체와 합성 문서 생성 | CLI | 실행 완료 | 00:07:24 | [전](assets/live-20260914-2034/screenshots/A02-prepare-iq-before.webp) | [후](assets/live-20260914-2034/screenshots/A02-prepare-iq-after.webp) |
| `A03-retrieve` 실제 knowledge base 검색 | CLI | 실행 완료 | 00:07:36 | [전](assets/live-20260914-2034/screenshots/A03-retrieve-before.webp) | [후](assets/live-20260914-2034/screenshots/A03-retrieve-after.webp) |
| `A-P01-knowledge` 실제 Foundry IQ knowledge base 목록 확인 | PORTAL | 실행 완료 | 00:07:51 | [전](assets/live-20260914-2034/screenshots/A-P01-knowledge-before.webp) | [후](assets/live-20260914-2034/screenshots/A-P01-knowledge-after.webp) |
| `A-P02-kb-details` 실제 knowledge base의 구성과 source 확인 | PORTAL | 실행 완료 | 00:08:03 | [전](assets/live-20260914-2034/screenshots/A-P02-kb-details-before.webp) | [후](assets/live-20260914-2034/screenshots/A-P02-kb-details-after.webp) |
| `A-P03-source` IQ source가 연결한 실제 Search index 확인 | PORTAL | 실행 완료 | 00:08:15 | [전](assets/live-20260914-2034/screenshots/A-P03-source-before.webp) | [후](assets/live-20260914-2034/screenshots/A-P03-source-after.webp) |
| `A-P04-source-fields` Source의 고급 설정 확인 | PORTAL | 실행 완료 | 00:08:27 | [전](assets/live-20260914-2034/screenshots/A-P04-source-fields-before.webp) | [후](assets/live-20260914-2034/screenshots/A-P04-source-fields-after.webp) |
| `A-P05-index` Foundry Indexes 탭과 Search index를 구분 | PORTAL | 실행 완료 | 00:08:39 | [전](assets/live-20260914-2034/screenshots/A-P05-index-before.webp) | [후](assets/live-20260914-2034/screenshots/A-P05-index-after.webp) |
| `A-P06-search-service` Azure Search에서 실제 인덱스와 문서 확인 | PORTAL | 실행 완료 | 00:08:51 | [전](assets/live-20260914-2034/screenshots/A-P06-search-service-before.webp) | [후](assets/live-20260914-2034/screenshots/A-P06-search-service-after.webp) |
| `B01-source` Python 에이전트의 처리 흐름 읽기 | CLI | 실행 완료 | 00:09:03 | [전](assets/live-20260914-2034/screenshots/B01-source-before.webp) | [후](assets/live-20260914-2034/screenshots/B01-source-after.webp) |
| `B02-v1` 부족한 초기 지침 V1 확인 | CLI | 실행 완료 | 00:09:11 | [전](assets/live-20260914-2034/screenshots/B02-v1-before.webp) | [후](assets/live-20260914-2034/screenshots/B02-v1-after.webp) |
| `B03-select-v1` V1 지침 선택 | CLI | 실행 완료 | 00:09:15 | [전](assets/live-20260914-2034/screenshots/B03-select-v1-before.webp) | [후](assets/live-20260914-2034/screenshots/B03-select-v1-after.webp) |
| `B04-local-start` 로컬 에이전트 서버 시작 | CLI | 서버 실행 유지 | 00:09:22 | [전](assets/live-20260914-2034/screenshots/B04-local-start-before.webp) | [후](assets/live-20260914-2034/screenshots/B04-local-start-after.webp) |
| `B05-readiness` 로컬 readiness HTTP 200 확인 | CLI | 실행 완료 | 00:09:35 | [전](assets/live-20260914-2034/screenshots/B05-readiness-before.webp) | [후](assets/live-20260914-2034/screenshots/B05-readiness-after.webp) |
| `B06-local-smoke` 로컬에서 실제 IQ·Sol 호출 | CLI | **실패한 시도** | 00:09:39 | [전](assets/live-20260914-2034/screenshots/B06-local-smoke-before.webp) | [후](assets/live-20260914-2034/screenshots/B06-local-smoke-after.webp) |
| `B06-parser-check` HTTP 응답과 azd 안내문 분리 검증 | CLI | 실행 완료 | 00:09:52 | [전](assets/live-20260914-2034/screenshots/B06-parser-check-before.webp) | [후](assets/live-20260914-2034/screenshots/B06-parser-check-after.webp) |
| `B06-local-smoke-retry` 같은 로컬 에이전트에서 실제 응답 재확인 | CLI | 실행 완료 | 00:10:02 | [전](assets/live-20260914-2034/screenshots/B06-local-smoke-retry-before.webp) | [후](assets/live-20260914-2034/screenshots/B06-local-smoke-retry-after.webp) |
| `B07-local-stop` 로컬 서버를 Ctrl+C로 종료 | CLI | **실패한 시도** | 00:10:14 | [전](assets/live-20260914-2034/screenshots/B07-local-stop-before.webp) | [후](assets/live-20260914-2034/screenshots/B07-local-stop-after.webp) |
| `B07-local-stop-confirm` 로컬 프로세스와 포트의 종료 재확인 | CLI | 실행 완료 | 00:10:19 | [전](assets/live-20260914-2034/screenshots/B07-local-stop-confirm-before.webp) | [후](assets/live-20260914-2034/screenshots/B07-local-stop-confirm-after.webp) |
| `B08-deploy-v1` Hosted Agent V1 실제 배포 | CLI | 실행 완료 | 00:10:23 | [전](assets/live-20260914-2034/screenshots/B08-deploy-v1-before.webp) | [후](assets/live-20260914-2034/screenshots/B08-deploy-v1-after.webp) |
| `B09-agent-access` 실제 agent instance의 데이터 권한 설정 | CLI | 실행 완료 | 00:10:35 | [전](assets/live-20260914-2034/screenshots/B09-agent-access-before.webp) | [후](assets/live-20260914-2034/screenshots/B09-agent-access-after.webp) |
| `B10-remote-smoke` 원격 Hosted Agent 실제 호출 | CLI | 실행 완료 | 00:10:47 | [전](assets/live-20260914-2034/screenshots/B10-remote-smoke-before.webp) | [후](assets/live-20260914-2034/screenshots/B10-remote-smoke-after.webp) |
| `00-P05-foundry-retry` 새 녹화 세션에서 실제 V1 에이전트 확인 | PORTAL | 실행 완료 | 00:10:59 | [전](assets/live-20260914-2034/screenshots/00-P05-foundry-retry-before.webp) | [후](assets/live-20260914-2034/screenshots/00-P05-foundry-retry-after.webp) |
| `B-P01-v1-playground` 실제 Hosted Agent V1 Playground 열기 | PORTAL | 실행 완료 | 00:11:11 | [전](assets/live-20260914-2034/screenshots/B-P01-v1-playground-before.webp) | [후](assets/live-20260914-2034/screenshots/B-P01-v1-playground-after.webp) |
| `B-P02-v1-invoke` 포털에서 V1에 실제 합성 질문 전송 | PORTAL | 실행 완료 | 00:11:23 | [전](assets/live-20260914-2034/screenshots/B-P02-v1-invoke-before.webp) | [후](assets/live-20260914-2034/screenshots/B-P02-v1-invoke-after.webp) |
| `B-P03-v1-answer` V1 실제 답변의 판단·한도·인용 읽기 | PORTAL | 실행 완료 | 00:11:35 | [전](assets/live-20260914-2034/screenshots/B-P03-v1-answer-before.webp) | [후](assets/live-20260914-2034/screenshots/B-P03-v1-answer-after.webp) |
| `B-P04-v1-details` 버전 선택과 agent identity·endpoint 설정을 구분 | PORTAL | 실행 완료 | 00:11:47 | [전](assets/live-20260914-2034/screenshots/B-P04-v1-details-before.webp) | [후](assets/live-20260914-2034/screenshots/B-P04-v1-details-after.webp) |
| `C01-baseline` 네 모델의 baseline 응답 수집 | CLI | 실행 완료 | 00:11:59 | [전](assets/live-20260914-2034/screenshots/C01-baseline-before.webp) | [후](assets/live-20260914-2034/screenshots/C01-baseline-after.webp) |
| `C02-evaluation` Foundry native baseline 평가 | CLI | 실행 완료 | 00:12:11 | [전](assets/live-20260914-2034/screenshots/C02-evaluation-before.webp) | [후](assets/live-20260914-2034/screenshots/C02-evaluation-after.webp) |
| `C-P01-evaluations` 프로젝트의 실제 데이터셋 평가 목록 열기 | PORTAL | 실행 완료 | 00:12:23 | [전](assets/live-20260914-2034/screenshots/C-P01-evaluations-before.webp) | [후](assets/live-20260914-2034/screenshots/C-P01-evaluations-after.webp) |
| `C-P02-baseline-report` 실제 baseline Foundry 평가 결과 열기 | PORTAL | 실행 완료 | 00:12:35 | [전](assets/live-20260914-2034/screenshots/C-P02-baseline-report-before.webp) | [후](assets/live-20260914-2034/screenshots/C-P02-baseline-report-after.webp) |
| `D01-compare` 실제 baseline의 실패 행 확인 | CLI | 실행 완료 | 00:12:46 | [전](assets/live-20260914-2034/screenshots/D01-compare-before.webp) | [후](assets/live-20260914-2034/screenshots/D01-compare-after.webp) |
| `D02-monitor` baseline의 실제 trace 대조 | CLI | 실행 완료 | 00:12:57 | [전](assets/live-20260914-2034/screenshots/D02-monitor-before.webp) | [후](assets/live-20260914-2034/screenshots/D02-monitor-after.webp) |
| `D-P01-traces` 실제 에이전트의 Traces 열기 | PORTAL | 실행 완료 | 00:13:09 | [전](assets/live-20260914-2034/screenshots/D-P01-traces-before.webp) | [후](assets/live-20260914-2034/screenshots/D-P01-traces-after.webp) |
| `D-P02-trace-search` 검토한 baseline 실패의 실제 trace ID 검색 | PORTAL | 실행 완료 | 00:13:21 | [전](assets/live-20260914-2034/screenshots/D-P02-trace-search-before.webp) | [후](assets/live-20260914-2034/screenshots/D-P02-trace-search-after.webp) |
| `D-P03-trace-detail` baseline 실패의 실제 span tree 열기 | PORTAL | 실행 완료 | 00:13:33 | [전](assets/live-20260914-2034/screenshots/D-P03-trace-detail-before.webp) | [후](assets/live-20260914-2034/screenshots/D-P03-trace-detail-after.webp) |
| `D-P04-graph` 실제 요청의 검색·모델 호출 경로를 그래프로 확인 | PORTAL | 실행 완료 | 00:13:45 | [전](assets/live-20260914-2034/screenshots/D-P04-graph-before.webp) | [후](assets/live-20260914-2034/screenshots/D-P04-graph-after.webp) |
| `D-P05-retrieval-span` 실제 IQ retrieve span의 KB와 참조 수 확인 | PORTAL | 실행 완료 | 00:13:57 | [전](assets/live-20260914-2034/screenshots/D-P05-retrieval-span-before.webp) | [후](assets/live-20260914-2034/screenshots/D-P05-retrieval-span-after.webp) |
| `D-P06-model-span` 실제 모델 호출과 응답 이력 확인 | PORTAL | 실행 완료 | 00:14:09 | [전](assets/live-20260914-2034/screenshots/D-P06-model-span-before.webp) | [후](assets/live-20260914-2034/screenshots/D-P06-model-span-after.webp) |
| `D-P07-model-metadata` 동일 요청의 실제 응답 모델 ID와 사용량 확인 | PORTAL | 실행 완료 | 00:14:21 | [전](assets/live-20260914-2034/screenshots/D-P07-model-metadata-before.webp) | [후](assets/live-20260914-2034/screenshots/D-P07-model-metadata-after.webp) |
| `D03-review` 실패 응답과 실제 trace를 함께 검토 | CLI | 실행 완료 | 00:14:33 | [전](assets/live-20260914-2034/screenshots/D03-review-before.webp) | [후](assets/live-20260914-2034/screenshots/D03-review-after.webp) |
| `D04-feedback` 검토한 실패를 회귀 데이터로 보존 | CLI | 실행 완료 | 00:14:41 | [전](assets/live-20260914-2034/screenshots/D04-feedback-before.webp) | [후](assets/live-20260914-2034/screenshots/D04-feedback-after.webp) |
| `E01-prompt-diff` V1과 제공된 개선 후보 V2 비교 | CLI | 실행 완료 | 00:14:47 | [전](assets/live-20260914-2034/screenshots/E01-prompt-diff-before.webp) | [후](assets/live-20260914-2034/screenshots/E01-prompt-diff-after.webp) |
| `E02-select-v2` V2 지침 선택 | CLI | 실행 완료 | 00:14:55 | [전](assets/live-20260914-2034/screenshots/E02-select-v2-before.webp) | [후](assets/live-20260914-2034/screenshots/E02-select-v2-after.webp) |
| `E03-deploy-v2` Hosted Agent의 새 V2 버전 배포 | CLI | 실행 완료 | 00:15:02 | [전](assets/live-20260914-2034/screenshots/E03-deploy-v2-before.webp) | [후](assets/live-20260914-2034/screenshots/E03-deploy-v2-after.webp) |
| `E04-smoke-v2` 새 원격 버전과 V2 지침 확인 | CLI | 실행 완료 | 00:15:14 | [전](assets/live-20260914-2034/screenshots/E04-smoke-v2-before.webp) | [후](assets/live-20260914-2034/screenshots/E04-smoke-v2-after.webp) |
| `E-P01-versions` 동일 에이전트의 V1/V2 비교 화면 열기 | PORTAL | 실행 완료 | 00:15:26 | [전](assets/live-20260914-2034/screenshots/E-P01-versions-before.webp) | [후](assets/live-20260914-2034/screenshots/E-P01-versions-after.webp) |
| `E-P02-compare-invoke` 동일 합성 질문을 실제 V1과 V2에 각각 전송 | PORTAL | 실행 완료 | 00:15:38 | [전](assets/live-20260914-2034/screenshots/E-P02-compare-invoke-before.webp) | [후](assets/live-20260914-2034/screenshots/E-P02-compare-invoke-after.webp) |
| `E-P03-compare-results` 실제 V1/V2 응답의 인용 차이 읽기 | PORTAL | 실행 완료 | 00:15:50 | [전](assets/live-20260914-2034/screenshots/E-P03-compare-results-before.webp) | [후](assets/live-20260914-2034/screenshots/E-P03-compare-results-after.webp) |
| `E05-collect` 같은 dev를 네 모델로 재실행 | CLI | 실행 완료 | 00:15:53 | [전](assets/live-20260914-2034/screenshots/E05-collect-before.webp) | [후](assets/live-20260914-2034/screenshots/E05-collect-after.webp) |
| `E06-evaluate` V2의 실제 Foundry 재평가 | CLI | 실행 완료 | 00:16:05 | [전](assets/live-20260914-2034/screenshots/E06-evaluate-before.webp) | [후](assets/live-20260914-2034/screenshots/E06-evaluate-after.webp) |
| `E-P04-improved-report` V2 dev의 실제 Foundry 평가 결과 확인 | PORTAL | 실행 완료 | 00:16:17 | [전](assets/live-20260914-2034/screenshots/E-P04-improved-report-before.webp) | [후](assets/live-20260914-2034/screenshots/E-P04-improved-report-after.webp) |
| `E07-compare` V1/V2를 동일 조건으로 비교 | CLI | 실행 완료 | 00:16:29 | [전](assets/live-20260914-2034/screenshots/E07-compare-before.webp) | [후](assets/live-20260914-2034/screenshots/E07-compare-after.webp) |
| `F01-collect` 고정한 후보로 교육용 holdout 실행 | CLI | 실행 완료 | 00:16:41 | [전](assets/live-20260914-2034/screenshots/F01-collect-before.webp) | [후](assets/live-20260914-2034/screenshots/F01-collect-after.webp) |
| `F02-evaluate` holdout의 실제 Foundry 평가 | CLI | 실행 완료 | 00:16:53 | [전](assets/live-20260914-2034/screenshots/F02-evaluate-before.webp) | [후](assets/live-20260914-2034/screenshots/F02-evaluate-after.webp) |
| `F-P01-holdout-report` 고정된 V2의 실제 holdout 평가 확인 | PORTAL | 실행 완료 | 00:17:05 | [전](assets/live-20260914-2034/screenshots/F-P01-holdout-report-before.webp) | [후](assets/live-20260914-2034/screenshots/F-P01-holdout-report-after.webp) |
| `F03-compare` 세 코호트의 결과와 유지된 자산 비교 | CLI | 실행 완료 | 00:17:17 | [전](assets/live-20260914-2034/screenshots/F03-compare-before.webp) | [후](assets/live-20260914-2034/screenshots/F03-compare-after.webp) |
| `G00-kql` 실제 agent와 run에 한정한 KQL 확인 | CLI | 실행 완료 | 00:17:29 | [전](assets/live-20260914-2034/screenshots/G00-kql-before.webp) | [후](assets/live-20260914-2034/screenshots/G00-kql-after.webp) |
| `G01-improved-monitor` V2 dev의 실제 telemetry 확인 | CLI | 실행 완료 | 00:17:38 | [전](assets/live-20260914-2034/screenshots/G01-improved-monitor-before.webp) | [후](assets/live-20260914-2034/screenshots/G01-improved-monitor-after.webp) |
| `G02-holdout-monitor` holdout의 실제 telemetry 확인 | CLI | 실행 완료 | 00:17:50 | [전](assets/live-20260914-2034/screenshots/G02-holdout-monitor-before.webp) | [후](assets/live-20260914-2034/screenshots/G02-holdout-monitor-after.webp) |
| `G-P01-monitor` 실제 Agent Monitor의 운영 지표 확인 | PORTAL | 실행 완료 | 00:18:02 | [전](assets/live-20260914-2034/screenshots/G-P01-monitor-before.webp) | [후](assets/live-20260914-2034/screenshots/G-P01-monitor-after.webp) |
| `G-P02-monitor-window` 운영 지표의 실제 관측 기간을 하루로 지정 | PORTAL | 실행 완료 | 00:18:14 | [전](assets/live-20260914-2034/screenshots/G-P02-monitor-window-before.webp) | [후](assets/live-20260914-2034/screenshots/G-P02-monitor-window-after.webp) |
| `G-P03-tools` 코드 내부의 도구 호출과 포털 연결 도구 목록을 구분 | PORTAL | 실행 완료 | 00:18:26 | [전](assets/live-20260914-2034/screenshots/G-P03-tools-before.webp) | [후](assets/live-20260914-2034/screenshots/G-P03-tools-after.webp) |
| `G-P04-operational-detail` 운영 집계의 토큰·컴퓨트·오류율을 따로 읽기 | PORTAL | 실행 완료 | 00:18:38 | [전](assets/live-20260914-2034/screenshots/G-P04-operational-detail-before.webp) | [후](assets/live-20260914-2034/screenshots/G-P04-operational-detail-after.webp) |
| `G03-verify` 전체 learning-loop 증거 검증 | CLI | 실행 완료 | 00:18:54 | [전](assets/live-20260914-2034/screenshots/G03-verify-before.webp) | [후](assets/live-20260914-2034/screenshots/G03-verify-after.webp) |
| `H01-cleanup-plan` 실습 자원의 정리 계획 확인 | CLI | 실행 완료 | 00:19:08 | [전](assets/live-20260914-2034/screenshots/H01-cleanup-plan-before.webp) | [후](assets/live-20260914-2034/screenshots/H01-cleanup-plan-after.webp) |
| `H00-sessions` 이번 에이전트의 실제 세션 목록 확인 | CLI | 실행 완료 | 00:19:18 | [전](assets/live-20260914-2034/screenshots/H00-sessions-before.webp) | [후](assets/live-20260914-2034/screenshots/H00-sessions-after.webp) |
| `H00-pause` 추가 포털 촬영을 위해 객체는 보존하고 세션 컴퓨트 중지 | CLI | 실행 완료 | 00:19:31 | [전](assets/live-20260914-2034/screenshots/H00-pause-before.webp) | [후](assets/live-20260914-2034/screenshots/H00-pause-after.webp) |
| `H01-final-plan` 포털 촬영 후 최종 삭제 대상을 다시 확인 | CLI | 실행 완료 | 00:19:43 | [전](assets/live-20260914-2034/screenshots/H01-final-plan-before.webp) | [후](assets/live-20260914-2034/screenshots/H01-final-plan-after.webp) |
| `H02-cleanup` 이번 실습의 agent·세션·모델·KB 정리 | CLI | 실행 완료 | 00:19:56 | [전](assets/live-20260914-2034/screenshots/H02-cleanup-before.webp) | [후](assets/live-20260914-2034/screenshots/H02-cleanup-after.webp) |
| `H03-cleanup-check` Azure에서 실제 정리 결과 재확인 | CLI | 실행 완료 | 00:20:08 | [전](assets/live-20260914-2034/screenshots/H03-cleanup-check-before.webp) | [후](assets/live-20260914-2034/screenshots/H03-cleanup-check-after.webp) |
| `H-P01-agent-absent` 포털에서 실습 에이전트 삭제 결과 확인 | PORTAL | 실행 완료 | 00:20:20 | [전](assets/live-20260914-2034/screenshots/H-P01-agent-absent-before.webp) | [후](assets/live-20260914-2034/screenshots/H-P01-agent-absent-after.webp) |
| `H-P02-models-cleaned` 네 후보 삭제와 보존된 보조 모델 구분 | PORTAL | 실행 완료 | 00:20:31 | [전](assets/live-20260914-2034/screenshots/H-P02-models-cleaned-before.webp) | [후](assets/live-20260914-2034/screenshots/H-P02-models-cleaned-after.webp) |
| `H-P03-knowledge-cleaned` 실습 KB 삭제와 Search 연결 보존 확인 | PORTAL | 실행 완료 | 00:20:43 | [전](assets/live-20260914-2034/screenshots/H-P03-knowledge-cleaned-before.webp) | [후](assets/live-20260914-2034/screenshots/H-P03-knowledge-cleaned-after.webp) |
| `H-P05-foundation-retained` 정리 후 보존된 기반 서비스와 잔여 비용 확인 | PORTAL | 실행 완료 | 00:20:55 | [전](assets/live-20260914-2034/screenshots/H-P05-foundation-retained-before.webp) | [후](assets/live-20260914-2034/screenshots/H-P05-foundation-retained-after.webp) |
| `H-P06-arm-history` 남아 있는 ARM 배포 실패 이력도 구분해 확인 | PORTAL | 실행 완료 | 00:21:07 | [전](assets/live-20260914-2034/screenshots/H-P06-arm-history-before.webp) | [후](assets/live-20260914-2034/screenshots/H-P06-arm-history-after.webp) |
| `H-P07-arm-error` 추가 경보/정책 배포 실패의 원인 확인 | PORTAL | 실행 완료 | 00:21:19 | [전](assets/live-20260914-2034/screenshots/H-P07-arm-error-before.webp) | [후](assets/live-20260914-2034/screenshots/H-P07-arm-error-after.webp) |
| `H-P08-policy-error` 정책 관련 배포 실패 이력도 별도로 확인 | PORTAL | 실행 완료 | 00:21:31 | [전](assets/live-20260914-2034/screenshots/H-P08-policy-error-before.webp) | [후](assets/live-20260914-2034/screenshots/H-P08-policy-error-after.webp) |
| `H-P04-evidence-retained` 실행 자원 정리 후 남아 있는 평가 자산 확인 | PORTAL | 실행 완료 | 00:21:43 | [전](assets/live-20260914-2034/screenshots/H-P04-evidence-retained-before.webp) | [후](assets/live-20260914-2034/screenshots/H-P04-evidence-retained-after.webp) |

## 로컬에서 챕터를 눌러 재생하기

HTML은 GitHub에서 소스로 표시될 수 있습니다. 저장소 루트에서 다음을 실행한 뒤 브라우저로 로컬 주소를 엽니다.

```bash
python3 recording/media_server.py --directory docs/assets/live-20260914-2034 --port 8899
```

`http://127.0.0.1:8899/index.html`에서 챕터를 누르면 해당 시각으로 이동합니다. MP4 파일은 일반 동영상 플레이어로도 열 수 있습니다.


## 기록의 범위

- 구성 요소의 실행 완료와 모델별 업무 품질·실제 운영 승인은 별개입니다.
- 기존 교육용 dev/holdout을 재실행했습니다. 새로운 독립 검증셋으로 포장하지 않습니다.
- 원본 영상·원본 PNG·환경별 상세 결과는 로컬에 보존하며, 공개용은 비식별 화면과 선별 결과입니다.
- 초기 브라우저 연결 재설정으로 중단된 이동은 완료로 처리하지 않았고, 별도 인증 후 같은 실제 대상을 다시 확인했습니다.

[참가자 가이드](../README.md) · [새 환경 준비](environment.ko.md) · [실제 Azure 검증](validation.ko.md)
