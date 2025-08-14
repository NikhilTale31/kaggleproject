import pytest

from src.attacks.attack_generator import (
    load_templates,
    generate_single_turn_attacks,
    generate_multi_turn_attacks,
)


def test_load_templates_and_payloads():
    data = load_templates()
    assert "attack_templates" in data
    assert "payload_library" in data
    assert "context_injections" in data
    # Basic shape
    assert isinstance(data["attack_templates"], list)
    assert isinstance(data["payload_library"], list)
    assert isinstance(data["context_injections"], list)


def test_generate_single_turn_attacks_structure():
    items = generate_single_turn_attacks(limit=10)
    assert isinstance(items, list)
    assert len(items) > 0
    for it in items:
        assert "id" in it
        assert it.get("type") == "single"
        assert "prompt" in it
        assert "category" in it
        assert "metadata" in it


def test_generate_multi_turn_attacks_structure():
    items = generate_multi_turn_attacks(limit=5)
    assert isinstance(items, list)
    assert len(items) > 0
    for it in items:
        assert "id" in it
        assert it.get("type") == "multi"
        assert "messages" in it and isinstance(it["messages"], list)
        assert "category" in it
        assert "metadata" in it


@pytest.mark.parametrize("category", [
    None,
    "prompt_injection",
    "cot_leakage",
    "tool_orchestration",
    "steganography",
    "temporal_deception",
    "system_leakage",
])
def test_category_filtering(category):
    # Single-turn
    singles = generate_single_turn_attacks(category=category, limit=50)
    if category:
        # If filtering, ensure all items have matching category or tag
        for it in singles:
            cat = str(it.get("category", "")).lower()
            tags = [t.lower() for t in it.get("tags", [])]
            assert cat == category.lower() or category.lower() in tags

    # Multi-turn
    multis = generate_multi_turn_attacks(category=category, limit=20)
    if category:
        for it in multis:
            cat = str(it.get("category", "")).lower()
            tags = [t.lower() for t in it.get("tags", [])]
            assert cat == category.lower() or category.lower() in tags
