from __future__ import annotations

from api.infrastructure.db.rows import CategoryRuleRow


def test_maps_the_category_rules_table():
    assert CategoryRuleRow.__tablename__ == "category_rules"


def test_one_rule_per_pattern():
    assert CategoryRuleRow.__table__.c.merchant_pattern.unique
