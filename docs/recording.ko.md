# 15분 녹화본

> 이 문서는 **기존 로컬 콘솔 영상**의 설명이다. 요청에 맞춰 새로 촬영한 [실제 Foundry 포털 녹화본](portal-recording.ko.md)은 별도 폴더에 있으며, 기존 MP4는 그대로 보존했다.

요청한 형식은 **Playwright headless, 약 15분, 대기 구간 제거**다.

**제작 완료:** [15분 MP4](../artifacts/recording/foundry-learning-loop-15min-ko.mp4) · [핵심 자막 SRT](../artifacts/recording/captions-ko.srt) · [챕터](../artifacts/recording/chapters.txt) · [검증 결과](../artifacts/recording/delivery-verification.json)

최종 MP4·자막·챕터·검수 기록과 contact sheet는 공개 저장소에 포함한다. `raw/`, `probe/`, 중간 음성 파일과 개인 실행 환경은 로컬에만 보존한다.

최종 파일은 **15:00 정각, 1920×1080, H.264/AAC, 약 46MB**다. 2026-09-11에 격리된 이름으로 실습 29단계를 다시 실행했고, 모델 응답 64건과 실제 trace 64개를 검증했다. 녹화용 임시 Azure 자원도 삭제 재확인했다.

## 녹화 방식

- 이전 검증 자료와 섞지 않는 새 작업 폴더·리소스 접두사를 사용한다.
- 브라우저의 실행 버튼이 실제 Azure CLI/SDK 명령을 실행한다.
- 배포·평가·권한 전파의 대기 구간은 편집본에서 제외한다.
- 최종 영상은 그 실제 실행기록, 코드, trace와 결과를 읽기 좋은 속도로 재구성한 **녹화용 로컬 콘솔 walkthrough**다.
- **Microsoft Foundry 포털 화면을 흉내 낸 UI가 아니다.** 포털은 별도 브라우저 로그인이 필요하여 로그인 화면을 녹화하지 않는다.
- 1080p 화면, 한국어 핵심 자막, 한국어 AI 합성 음성, 12개 챕터를 사용한다.
- 영상의 녹화 화면에는 이메일, 토큰, 연결 문자열과 개인 경로를 노출하지 않는다.

기술적인 실행 성공과 업무 품질 합격, 사람의 운영 승인은 구분한다. 실제 실행 결과가 예상과 다르면 결과를 바꾸지 않는다.

## 파일

| 파일 | 내용 |
|---|---|
| `artifacts/recording/foundry-learning-loop-15min-ko.mp4` | 15분 편집본 |
| `artifacts/recording/captions-ko.srt` | 한국어 핵심 자막 |
| `artifacts/recording/chapters.txt` | 챕터 타임스탬프 |
| `artifacts/recording/video-verification.json` | 길이·해상도·코덱·디코딩 검증 |
| `artifacts/recording/raw/` | 대기·실패도 포함한 원본 headless 녹화 및 편집용 화면 녹화. 로컬 전용, Git 제외 |
| `.recording/` | 개인 실행 환경과 상세 실행 기록. 배포 자료에 포함하지 않는다. |

## 재현에 쓰는 코드

`recording/prepare.py`는 기존 실습 소스를 격리된 폴더로 복제한다. `recording/server.py`는 localhost에서만 실행되며, 임의의 shell 명령이나 파일 경로를 받지 않는다. 명령은 allowlist에 고정되어 있고 상태 변경 요청에는 동일 origin과 녹화용 토큰이 필요하다.

`recording/live_capture.js`는 Playwright의 `recordVideo`로 실제 명령 실행을 기록한다. `recording/story.json`과 `prepare_media.py`는 정확히 900초인 한국어 설명·자막 타임라인을 만든다. `render_capture.js`는 실제 실행이 끝난 뒤 결과 화면을 headless로 녹화하고, `finish_video.py`가 영상과 음성·챕터를 합친다.

UI의 표시 결과는 실제 실행 파일에서 읽는다. 가상의 성공 결과를 미리 채워 놓는 방식은 사용하지 않는다.

## 최종 확인

영상 전체 디코딩, 900초 길이, 1080p 해상도, 음성 트랙, 12개 챕터를 확인했다. 46개 장면 전환의 계획 대비 최대 지연은 110ms였다. 영상의 주요 화면을 추출해 가독성을 확인했고, 표시 로그에서 계정·토큰·연결 키 노출 여부를 검사했다.

초기 토큰 갱신 timeout은 실패 기록을 남긴 뒤 재시도했다. 처음 설치 장면과 이후 성공한 실행은 원본 영상에 별도로 보존했다. 최종 MP4는 대기 구간 대신 코드·결과 설명을 배치한 **실제 실행기록의 편집 walkthrough**이며, 포털 UI 녹화나 15분 만의 신규 Azure 환경 구축을 의미하지 않는다.
