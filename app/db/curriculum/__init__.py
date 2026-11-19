"""
Модуль для роботи з навчальною програмою 1–11 класів.
Дані зберігаються у структурованих JSON-файлах у каталозі data/curriculum/.
"""

from app.db.curriculum.loader import get_curriculum_hash, load_curriculum

INITIAL_CURRICULUM = load_curriculum()

__all__ = ["INITIAL_CURRICULUM", "load_curriculum", "get_curriculum_hash"]
