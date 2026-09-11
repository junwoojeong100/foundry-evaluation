# 실제 Foundry 포털 녹화본

[15분 MP4](../artifacts/foundry-portal-recording/foundry-portal-learning-loop-15min-ko.mp4) · [한국어 자막](../artifacts/foundry-portal-recording/captions-ko.srt) · [챕터](../artifacts/foundry-portal-recording/chapters.txt) · [검수 기록](../artifacts/foundry-portal-recording/delivery-verification.json)

**공개 범위:** 최종 영상·자막·챕터·검수 화면·편집 구간·원본 해시와 제작 코드를 포함한다. 환경 식별자가 담긴 `portal-final-evidence.zip`, `run-summary.json`, `portal-workshop-source.zip`과 녹화 원본·편집 중간 자료는 로컬에 보존하며 공개 저장소에는 포함하지 않는다.

**실제 `ai.azure.com`과 `portal.azure.com`을 조작한 별도 영상이다.** 기존 로컬 콘솔 영상은 덮어쓰지 않았다. 새 파일은 `artifacts/foundry-portal-recording/`에 있다.

## 녹화·편집 방식

- 사용자가 직접 로그인한 뒤 인증 상태를 **메모리에서만** headless Edge로 전달했다. 로그인·암호·MFA 화면은 녹화하지 않았다.
- 모델 배포, Knowledge, Data, Hosted Agent Playground, Traces, Graph view, 주석, 평가 마법사, 평가 결과, 버전 비교와 Monitor는 **실제 Foundry UI**다.
- Python 설치·실행, `azd` 배포, 배치 수집·평가, 회귀 데이터와 정리는 **Azure Portal의 네이티브 Cloud Shell**에서 수행했다. 사용자 PC의 로컬 웹 콘솔이나 재구성한 포털 UI를 촬영한 것이 아니다.
- 실제 포털 원본 59구간을 편집했다. 설치·배포·평가 대기와 UI 자동화 탐색·오류 해결 구간을 제외했다. 읽기 어려운 결과에는 원본 마지막 프레임을 유지하는 **설명용 화면 정지 약 6분 12초**를 넣고 영상에 표시했다. 결과나 화면 내용을 만들어 넣지 않았다.
- 완성본은 **15:00, 1920×1080, H.264/AAC, 약 38MB**다. 한국어 AI 합성 음성, 핵심 자막 47개, 챕터 12개를 포함한다. 자막은 전체 발화의 축어록이 아니라 핵심 요약이다.
- 원래 UI의 입력창·버튼을 자막이 가리지 않도록 전체 포털 화면을 축소하고 하단 설명 영역을 분리했다. Foundry 화면은 10분 57초, Azure Cloud Shell 화면은 4분 3초다.

이 영상은 **15분 만에 새 Azure 환경을 구축했다는 기록이 아니다.** 원본은 준비·대기·자동화 확인을 포함해 약 142분이다. 가이드의 120분 시간표는 [강사 사전 준비](instructor.ko.md)가 끝난 참가자 환경 기준이다.

## 이번 새 실행의 결과

2026-09-11에 `portal0911` 접두사와 `portal-learning-loop-0911` 에이전트로 다시 실행했다. 이전 실행의 점수·trace를 재사용한 영상이 아니다.

| 단계 | Agent version | 모델 응답 | Groundedness 통과 | Relevance 통과 | 업무 검사 통과 |
|---|---:|---:|---:|---:|---:|
| Baseline dev | 1 | 24 | 24/24 | 21/24 | 0/24 |
| Improved dev | 2 | 24 | 24/24 | 22/24 | 24/24 |
| Holdout | 2 | 16 | 16/16 | 16/16 | 16/16 |

Groundedness와 Relevance는 **1~5점 중 4점 이상**을 통과로 계산했다. 업무 검사는 판단·금액·실제 검색 근거·정책 ID 인용 등의 별도 계약이다. V1은 정책 ID 대신 제목을 인용해 업무 검사를 통과하지 못했다. 높은 LLM 평가 점수와 업무 계약 충족을 구분하는 사례다.

네 후보의 실제 모델·버전은 `gpt-5.6-sol`, `gpt-5.6-terra`, `gpt-5.6-luna`의 `2026-07-09`, `gpt-6-astra`의 `2026-09-03`이다. `gpt-5.4-mini`는 기존의 고정 검색 계획·평가 보조 모델이다.

**본 실험 64응답과 실제 trace 64개**를 대조했다. 실패 사례의 출처를 회귀 데이터에 연결했고 V2 검증에서도 유지했다. 합성 사례와 표본 크기의 제약이 있으며, 모델 순위·실제 기업 업무 정확도를 보장하지 않는다. **`production_release_approved`는 `false`**다. AI 보조 검토를 실제 업무 담당자의 승인으로 표시하지 않았다.

같은 KB를 사용해도 개별 호출의 검색 결과는 달라질 수 있어 context hash를 보존했다. 따라서 위 숫자를 검색 결과까지 완전히 통제한 모델 성능 순위나 지침 변경만의 인과 효과로 해석하지 않는다.

추가로 네이티브 평가 마법사에서 `portal0911-ui-baseline`을 제출해 완료를 확인했다. 동일한 baseline 24응답을 다시 평가한 작업이므로 새로운 모델 응답 24건으로 더하지 않는다. Playground와 버전 비교 호출도 본 실험과 별도다.

| 평가 | Evaluation ID | Run ID |
|---|---|---|
| Baseline | `eval_df3df2fc3ff14e3b8c508dfa94f21e6c` | `evalrun_225dcb1a8e584653b97bb0cec603cefa` |
| Improved | `eval_6ab7c665f5c34218a562b2b22a7c3ca0` | `evalrun_55e3feafbeea4e7d93b83e1de0369239` |
| Holdout | `eval_1fe2fe9383564339aca29ee0f909711b` | `evalrun_46a09e5ffd7941e68644d9b0c6cb372b` |
| 추가 UI baseline | `eval_e20c9991d66840a2b9ecb8f363924dda` | `evalrun_89079f3226c5438ea2e9bd37120f1e6c` |

Monitor에는 추가 호출을 포함한 **73 runs, 약 196.6K tokens, 오류율 약 7.45%**가 표시됐다. 이 운영 집계의 분모를 본 실험 64건과 동일시하지 않는다. 표시된 추정 비용 `$0`도 실제 청구 무료를 의미하지 않는다.

## 가이드와 포털의 차이·미완료 기능

- **Cloud Shell 조회 경로:** 기본 Application Insights audience의 토큰 취득이 실패해 `portal_monitor.py`에서 공식 `LogsQueryClient.query_resource`와 Cloud Shell이 지원하는 로그 audience를 사용했다. 동일한 KQL과 기존 응답·trace 검증 로직을 사용했으며 가짜 telemetry나 성공 기본값으로 대체하지 않았다.
- **Trace → Create dataset:** 네이티브 화면과 권한 해결을 확인했지만 전파 확인이 끝나지 않아 **포털의 trace 기반 데이터셋 생성은 완료하지 않았다.** 실제 회귀 데이터 작성·재사용은 가이드의 Cloud Shell 명령으로 완료했다. 실패한 네이티브 생성 화면을 성공 화면처럼 편집하지 않았다.
- **Continuous / scheduled evaluation:** Monitor의 운영 차트와 설정 가능 여부를 확인했다. 지속·예약 평가 정책은 **활성화하지 않았다.**
- 이번 평가는 응답 데이터셋을 대상으로 한 프로젝트의 **전역 Evaluations**에 있다. 에이전트 상세의 자동 평가 목록과 같은 대상이라고 가정하지 않는다.
- 초기 설치 경로, 누락된 `uv`/Foundry 확장, 토큰 audience 오류 등의 해결 과정은 원본에 남아 있지만 15분 편집본에서 생략했다. 처음부터 오류 없이 진행됐다는 주장이 아니다.

## 정리한 자원과 남긴 자산

이번 Hosted Agent V1·V2, `portal0911-kb`, `portal0911-source`, `portal0911-policies`, 네 `portal0911-*` 모델 배포와 임시 역할 3개를 삭제 확인했다. 이 중 모델 네 개는 UI에서 만들었으므로 UI에서 별도 삭제했다. 추가 Monitoring Reader 역할은 정확한 ID·principal·scope·생성 시각을 대조하고 제거했다.

**기존 Foundry 프로젝트, Search, Application Insights, `gpt-5.4-mini`, 공유 에이전트와 공유 KB는 보존했다.** `portal0911-dev:1`, 평가 실행과 자동 생성 평가 데이터셋, telemetry·주석은 증거로 남겼다. 따라서 공유 인프라나 보관 데이터의 비용까지 없어졌다는 뜻은 아니다.

## 관련 파일

| 경로 | 내용 |
|---|---|
| `artifacts/foundry-portal-recording/foundry-portal-learning-loop-15min-ko.mp4` | 실제 포털 편집본 |
| `captions-ko.srt`, `chapters.txt` | 핵심 자막·챕터 |
| `portal-final-evidence.zip`, `run-summary.json` | 이번 실행의 결과·lineage·정리 증거. 환경 식별자를 포함하므로 로컬 전용 |
| `portal-workshop-source.zip` | Cloud Shell에 업로드한 소스와 환경 설정. `.env`·인증 저장소는 없지만 구독·tenant 설정이 있으므로 로컬 전용 |
| `source-footage.json`, `edit-decision-list.json` | 원본 해시, 탭별 시각, 원본→최종 편집 구간 |
| `delivery-verification.json`, `screenshots/` | 미디어·증거·보존 확인과 최종 영상 장면 |
| `raw/`, `review/`, `capture-metadata.json` | 로컬 전용 원본·편집 중간 자료. Git 제외 |
| `portal_recording/` | 이번 녹화·Cloud Shell 보조 실행·편집·검수 코드 |

**공개 공유에는 MP4·자막·챕터·선별 검수 기록을 사용한다.** 편집 전 `raw/`, `review/`, `capture-metadata.json`에는 개인 경로나 초기 미가림 화면이 있을 수 있다. 원본과 환경별 실행 증거 ZIP을 공개 배포용으로 취급하지 않는다. 최종 영상은 선택 구간의 처음·중간·끝 프레임을 오프라인 OCR과 육안으로 점검하며, 계정 영역·업로드 알림·필요한 개인 경로를 마스킹한다.

## 원본에서 다시 편집하기

macOS, Python 3.13 이상, FFmpeg, Pillow 12.2.0, 한국어 Yuna 음성과 Apple SD Gothic Neo 글꼴을 사용했다. OCR 검수에는 macOS Vision을 사용하며 외부 서비스로 화면을 전송하지 않는다.

```bash
python3 portal_recording/build_video.py prepare
python3 portal_recording/build_video.py render
python3 portal_recording/verify_delivery.py inspect
swift portal_recording/inspect_frames.swift \
  .portal-recording/verification-frames .portal-recording/ocr-findings.json
python3 portal_recording/verify_delivery.py finalize
```

이미 저장된 원본과 capture metadata가 필요하다. `start_capture.js`와 `stop_capture.js`는 인증된 Playwright 세션에서 쓰는 녹화 보조 함수이며 단독 CLI 로그인 도구가 아니다. UI 동작 전체를 무인 재실행하는 범용 자동화 스크립트도 아니다. `portal_cleanup.py`는 **이번 녹화의 정확한 역할 ID·생성 시각에 묶인 일회성 정리 보조 코드**이므로 다른 실습에 그대로 사용하지 않는다.
