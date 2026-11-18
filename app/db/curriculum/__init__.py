"""
Повна структурована навчальна програма з математики для 1–11 класів.
Складена за підручниками автора О. С. Істера та стандартами МОН України.
"""

from app.db.curriculum.p1_primary import (
    GRADE_1,
    GRADE_2,
    GRADE_3,
    GRADE_4,
)
from app.db.curriculum.p2_middle import (
    GRADE_5,
    GRADE_6,
)
from app.db.curriculum.p3_junior import (
    GRADE_7_ALGEBRA,
    GRADE_7_GEOMETRY,
    GRADE_8_ALGEBRA,
    GRADE_8_GEOMETRY,
)
from app.db.curriculum.p4_senior import (
    GRADE_9_ALGEBRA,
    GRADE_9_GEOMETRY,
    GRADE_10_ALGEBRA,
    GRADE_10_GEOMETRY,
    GRADE_11_ALGEBRA,
    GRADE_11_GEOMETRY,
)

INITIAL_CURRICULUM = (
    GRADE_1
    + GRADE_2
    + GRADE_3
    + GRADE_4
    + GRADE_5
    + GRADE_6
    + GRADE_7_ALGEBRA
    + GRADE_7_GEOMETRY
    + GRADE_8_ALGEBRA
    + GRADE_8_GEOMETRY
    + GRADE_9_ALGEBRA
    + GRADE_9_GEOMETRY
    + GRADE_10_ALGEBRA
    + GRADE_10_GEOMETRY
    + GRADE_11_ALGEBRA
    + GRADE_11_GEOMETRY
)

__all__ = ["INITIAL_CURRICULUM"]
