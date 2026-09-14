"""Register the README's commands without changing the experiment's inputs."""

import argparse
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def register(directory: Path):
    config = json.loads((directory / "config.json").read_text())
    path = directory / "actions.json"
    actions = json.loads(path.read_text())
    workspace = Path(config["workspace"])
    python = str(workspace / "src/agent/.venv/bin/python")
    environment = {
        "VIRTUAL_ENV": str(workspace / "src/agent/.venv"),
        "PATH": str(workspace / "src/agent/.venv/bin") + os.pathsep + os.environ["PATH"],
    }
    existing = {action["id"] for action in actions}

    def add(action_id, guide, title, check, argv, **extra):
        if action_id in existing:
            raise ValueError(f"An action with this ID already exists: {action_id}")
        actions.append({
            "id": action_id, "guide": guide, "title": title, "check": check,
            "argv": argv, "environment": environment, "timeout": 1900, **extra,
        })
        existing.add(action_id)

    def workshop(action_id, guide, title, check, *args):
        add(action_id, guide, title, check, [python, "scripts/workshop.py", *args])

    workshop("00-27-preflight", "00 · 강사 사전 준비", "네 후보 배포 전 사전 점검", "새 프로젝트·Search·관측 연결 · 아직 없는 네 배포만 구분", "preflight", "--allow-missing-models")
    workshop("00-28-models", "00 · 강사 사전 준비", "실제 네 후보 모델 배포", "Sol/Terra/Luna/Astra · 모델/버전 고정 · 각 50 capacity", "prepare-models")
    workshop("00-29-bind", "00 · 강사 사전 준비", "azd를 새 프로젝트에 바인딩", "반환된 실제 project ARM ID · 기존 프로젝트 재프로비저닝 없음", "bind")
    workshop("00-30-ready", "00 · 강사 사전 준비", "참가자 시작 조건 확인", "네 배포의 실제 model.name / model.version과 관측 연결", "preflight")
    workshop("00-31-calibrate", "00 · 강사 사전 준비", "고정 judge calibration 실행", "고정 정답·오답 예제 2개 · 본평가 64응답과 별도", "calibrate")

    add("A01-policies", "A · 조직의 기억", "합성 정책 문서와 적용일 확인", "현행·과거 규정과 승인·영수증 조건 · 실제 회사 자료 아님",
        [python, "-c", "from pathlib import Path; print(Path('data/policies.json').read_text())"])
    workshop("A02-prepare-iq", "A · 조직의 기억", "Foundry IQ 지식 객체와 합성 문서 생성", "새 index / knowledge source / knowledge base만 생성", "prepare-iq")
    workshop("A03-retrieve", "A · 조직의 기억", "실제 knowledge base 검색", "knowledge base 이름·문서 ID·실제 activity", "retrieve", "--query", "2026년 9월 국내 출장 숙박비 한도는 얼마인가요?")

    add("B01-source", "B · Hosted Agent V1", "Python 에이전트의 처리 흐름 읽기", "입력 검증 → 실제 IQ 검색 → 실제 모델 → 출력 계약",
        [python, "-c", "from pathlib import Path; print(Path('src/agent/policy_agent.py').read_text())"])
    add("B02-v1", "B · Hosted Agent V1", "부족한 초기 지침 V1 확인", "문서 식별자를 숨기는 지침 · 코드가 오답을 만들어 넣는 것이 아님",
        [python, "-c", "from pathlib import Path; print(Path('src/agent/prompts/v1.txt').read_text())"])
    workshop("B03-select-v1", "B · Hosted Agent V1", "V1 지침 선택", "로컬 설정과 azd 환경을 일치", "set-prompt", "v1")
    add("B04-local-start", "B · Hosted Agent V1", "로컬 에이전트 서버 시작", "이 실행의 프로세스만 시작 · readiness 200 이후 두 번째 터미널로 진행",
        ["azd", "ai", "agent", "run", "--no-client"], readiness="http://127.0.0.1:8088/readiness")
    add("B05-readiness", "B · Hosted Agent V1", "로컬 readiness HTTP 200 확인", "서버 준비 상태와 모델 추론 성공은 별개",
        ["curl", "--fail", "--silent", "--show-error", "http://127.0.0.1:8088/readiness"])
    workshop("B06-local-smoke", "B · Hosted Agent V1", "로컬에서 실제 IQ·Sol 호출", "모의 응답이 아닌 실제 근거와 model_key=sol", "smoke", "--local")
    add("B07-local-stop", "B · Hosted Agent V1", "로컬 서버를 Ctrl+C로 종료", "녹화가 시작한 프로세스에만 SIGINT · 포트 종료 재확인",
        ["Ctrl+C", "(SIGINT to recording-owned local process)"], stop_service="B04-local-start")
    add("B08-deploy-v1", "B · Hosted Agent V1", "Hosted Agent V1 실제 배포", "Direct code deployment · 새 immutable version · 로컬 Docker 불필요",
        ["azd", "deploy", "--no-prompt"])
    workshop("B09-agent-access", "B · Hosted Agent V1", "실제 agent instance의 데이터 권한 설정", "이번 agent identity의 Search 읽기·모델 추론 권한", "grant-agent-access")
    workshop("B10-remote-smoke", "B · Hosted Agent V1", "원격 Hosted Agent 실제 호출", "prompt_version=v1 · 실제 agent version · 근거와 trace_id", "smoke")

    workshop("C01-baseline", "C · Baseline과 평가", "네 모델의 baseline 응답 수집", "dev 6문항 × 4모델 = 누락·중복·오류 없는 24행", "collect", "--split", "dev", "--label", "baseline")
    workshop("C02-evaluation", "C · Baseline과 평가", "Foundry native baseline 평가", "groundedness/relevance와 결정적 업무 검사를 구분", "evaluate", "--label", "baseline")
    workshop("D01-compare", "D · 실패와 학습 자산", "실제 baseline의 실패 행 확인", "성공한 사례만 고르지 않고 전체 분모 유지", "compare", "--labels", "baseline")
    workshop("D02-monitor", "D · 실패와 학습 자산", "baseline의 실제 trace 대조", "응답의 trace_id와 Application Insights의 실제 요청 연결", "monitor", "--label", "baseline")

    add("E01-prompt-diff", "E · 개선과 재평가", "V1과 제공된 개선 후보 V2 비교", "실패 원인과 지침 변경 이유 · 정답이나 평가 기준은 변경하지 않음",
        [python, "-c", "from pathlib import Path; import difflib; p=Path('src/agent/prompts'); print(''.join(difflib.unified_diff((p/'v1.txt').read_text().splitlines(True),(p/'v2.txt').read_text().splitlines(True),fromfile='v1.txt',tofile='v2.txt')))"])
    workshop("E02-select-v2", "E · 개선과 재평가", "V2 지침 선택", "적용일·문서 ID 인용·근거 없는 질문의 보류", "set-prompt", "v2")
    add("E03-deploy-v2", "E · 개선과 재평가", "Hosted Agent의 새 V2 버전 배포", "V1은 유지하고 새 immutable version 생성",
        ["azd", "deploy", "--no-prompt"])
    workshop("E04-smoke-v2", "E · 개선과 재평가", "새 원격 버전과 V2 지침 확인", "같은 모델 · prompt_version=v2 · 새 agent version", "smoke")
    workshop("E05-collect", "E · 개선과 재평가", "같은 dev를 네 모델로 재실행", "같은 24행 · 소비한 회귀 데이터와 source trace lineage", "collect", "--split", "dev", "--label", "improved")
    workshop("E06-evaluate", "E · 개선과 재평가", "V2의 실제 Foundry 재평가", "오류·null을 성공으로 처리하지 않는 동일 evaluator", "evaluate", "--label", "improved")
    workshop("E07-compare", "E · 개선과 재평가", "V1/V2를 동일 조건으로 비교", "dataset/rubric/모델 고정 · 개선이 없으면 그대로 기록", "compare", "--labels", "baseline", "improved")

    workshop("F01-collect", "F · Holdout", "고정한 후보로 교육용 holdout 실행", "4문항 × 4모델 = 16행 · 이 결과로 prompt 재조정 금지", "collect", "--split", "holdout", "--label", "holdout")
    workshop("F02-evaluate", "F · Holdout", "holdout의 실제 Foundry 평가", "16행의 native 결과와 업무 검사 · 작은 표본의 한계", "evaluate", "--label", "holdout")
    workshop("F03-compare", "F · Holdout", "세 코호트의 결과와 유지된 자산 비교", "모델은 교체하고 지식·평가·지침·실패 이력은 보존", "compare", "--labels", "baseline", "improved", "holdout")

    workshop("G01-improved-monitor", "G · Trace와 Monitor", "V2 dev의 실제 telemetry 확인", "24개의 실제 trace · HTTP 성공률과 업무 통과율 구분", "monitor", "--label", "improved")
    workshop("G02-holdout-monitor", "G · Trace와 Monitor", "holdout의 실제 telemetry 확인", "16개의 실제 trace · 지연/토큰과 수집 상태", "monitor", "--label", "holdout")
    workshop("G03-verify", "G · Trace와 Monitor", "전체 learning-loop 증거 검증", "64응답·64trace·완료된 Foundry run·불변 기준·회귀 lineage", "verify", "--baseline", "baseline", "--candidate", "improved", "--holdout", "holdout")
    workshop("H01-cleanup-plan", "마무리 · 정리", "실습 자원의 정리 계획 확인", "정확한 소유권 기록 · 새 인프라와 과거 공유 자원은 구분", "cleanup", "--dry-run")
    workshop("H02-cleanup", "마무리 · 정리", "이번 실습의 agent·세션·모델·KB 정리", "계획에 기록된 객체만 정리 · 공유 그룹 삭제 없음", "cleanup", "--confirm")
    workshop("H03-cleanup-check", "마무리 · 정리", "Azure에서 실제 정리 결과 재확인", "삭제한 자원과 보존한 기반 서비스·잔여 비용 구분", "check-cleanup")
    path.write_text(json.dumps(actions, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"total_registered": len(actions), "feedback": "Register only after inspecting the actual baseline failure."}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", type=Path, required=True)
    args = parser.parse_args()
    directory = args.run_dir.resolve()
    if not directory.is_relative_to(ROOT / ".recording"):
        raise ValueError("Use this repository's isolated recording directory.")
    register(directory)
