import hashlib
import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

CURRICULUM_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data" / "curriculum"


def get_curriculum_hash() -> str:
    """Обчислює єдиний SHA-256 хеш усіх JSON файлів навчальної програми."""
    hasher = hashlib.sha256()
    if not CURRICULUM_DIR.exists():
        return ""

    for file_path in sorted(CURRICULUM_DIR.glob("grade_*.json")):
        hasher.update(file_path.read_bytes())

    return hasher.hexdigest()[:16]


def load_curriculum() -> list[dict[str, Any]]:
    """Завантажує всі теми з JSON-фікстур у каталозі data/curriculum/."""
    curriculum: list[dict[str, Any]] = []

    if not CURRICULUM_DIR.exists():
        logger.warning("каталог із даними програми не знайдено: %s", CURRICULUM_DIR)
        return curriculum

    json_files = sorted(CURRICULUM_DIR.glob("grade_*.json"))
    for file_path in json_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                grade_topics: list[dict[str, Any]] = json.load(f)
                curriculum.extend(grade_topics)
        except Exception as e:
            logger.error("помилка зчитування файлу %s: %s", file_path.name, e)

    return curriculum
