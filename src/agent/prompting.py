import hashlib
import json

from contracts import PolicyAnswer
from settings import SOURCE_DIR


def load_prompt(version: str) -> tuple[str, str]:
    if version not in {"v1", "v2"}:
        raise ValueError("Unknown prompt version.")
    instructions = (SOURCE_DIR / "prompts" / f"{version}.txt").read_text(encoding="utf-8")
    schema = json.dumps(PolicyAnswer.model_json_schema(), ensure_ascii=False)
    instructions += (
        "\n\n출력 계약: 아래 JSON schema에 맞는 JSON 객체 하나만 출력하세요. "
        "Markdown 코드 블록이나 JSON 밖의 설명을 쓰지 마세요. "
        "decision은 schema의 enum 값 중 하나를 그대로 사용하세요.\n"
        + schema
    )
    return instructions, hashlib.sha256(instructions.encode()).hexdigest()
