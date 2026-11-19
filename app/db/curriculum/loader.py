import functools
import hashlib
import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

CURRICULUM_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data" / "curriculum"


def get_curriculum_hash() -> str:
    """Обчислює єдиний SHA-256 хеш усіх JSON файлів навчальної програми."""
    if not CURRICULUM_DIR.exists():
        return ""
    hasher = hashlib.sha256()
    for file_path in sorted(CURRICULUM_DIR.glob("grade_*.json")):
        hasher.update(file_path.read_bytes())
    return hasher.hexdigest()[:16]


@functools.lru_cache(maxsize=1)
def load_curriculum() -> list[dict[str, Any]]:
    """Завантажує всі теми з JSON-фікстур у каталозі data/curriculum/ (кешується в пам'яті)."""
    if not CURRICULUM_DIR.exists():
        logger.warning("каталог із даними програми не знайдено: %s", CURRICULUM_DIR)
        return []

    curriculum: list[dict[str, Any]] = []
    for file_path in sorted(CURRICULUM_DIR.glob("grade_*.json")):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                curriculum.extend(json.load(f))
        except Exception as e:
            logger.error("помилка зчитування файлу %s: %s", file_path.name, e)
    return curriculum
