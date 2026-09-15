import hashlib
import json

from contracts import PolicyAnswer
from settings import Language, SOURCE_DIR, validate_language


def load_prompt(version: str, language: Language = "ko") -> tuple[str, str]:
    if version not in {"v1", "v2"}:
        raise ValueError("Unknown prompt version.")
    selected = validate_language(language)
    directory = SOURCE_DIR / "prompts"
    if selected == "en":
        directory = directory / "en"
    instructions = (directory / f"{version}.txt").read_text(encoding="utf-8")
    schema = json.dumps(PolicyAnswer.model_json_schema(), ensure_ascii=False)
    if selected == "en":
        instructions += (
            "\n\nOutput contract: return exactly one JSON object matching the JSON schema below. "
            "Do not use Markdown code fences or explanations outside the JSON. "
            "Use one of the schema's decision enum values exactly as written.\n"
            + schema
        )
    else:
        instructions += (
            "\n\n출력 계약: 아래 JSON schema에 맞는 JSON 객체 하나만 출력하세요. "
            "Markdown 코드 블록이나 JSON 밖의 설명을 쓰지 마세요. "
            "decision은 schema의 enum 값 중 하나를 그대로 사용하세요.\n"
            + schema
        )
    return instructions, hashlib.sha256(instructions.encode()).hexdigest()
