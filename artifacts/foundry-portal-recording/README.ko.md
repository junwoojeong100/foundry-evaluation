# 실제 Foundry 포털 녹화

**[15분 영상 바로 재생](https://github.com/user-attachments/assets/72d4588f-5a6d-450b-819c-bcab035020fe)**

https://github.com/user-attachments/assets/72d4588f-5a6d-450b-819c-bcab035020fe

실제 Microsoft Foundry와 Azure Portal Cloud Shell을 Playwright headless로 녹화했다. 한국어 AI 합성 음성·핵심 자막을 포함하며, 대기를 잘라내고 읽기용 화면 정지를 명시했다. 기존 `../recording/` 영상은 그대로 보존했다.

- [상세 설명·실행 결과·제약](../../docs/portal-recording.ko.md)
- [자막](captions-ko.srt) · [챕터](chapters.txt)
- [이번 실행 결과·정리 요약](../../docs/portal-recording.ko.md)
- [편집 구간](edit-decision-list.json) · [원본 해시](source-footage.json) · [검수 기록](delivery-verification.json)
- [실습 소스](../../src/agent/) · [녹화·편집 코드](../../portal_recording/)

`raw/`, `review/`, `capture-metadata.json`은 개인 경로 등이 포함될 수 있는 **로컬 전용 중간 자료**다. 환경 식별자가 담긴 `portal-final-evidence.zip`, `run-summary.json`, `portal-workshop-source.zip`도 로컬에만 보존한다. 공개 공유에는 최종 MP4와 자막·챕터·선별 검수 기록을 사용한다.
