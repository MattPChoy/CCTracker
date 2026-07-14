"""Unit tests for the ccusage normalization layer (pure, no DB needed)."""

from app.normalize import normalize_cost, normalize_model, normalize_tokens


def test_model_family_and_label():
    assert normalize_model("claude-opus-4-1-20250805") == ("opus", "Opus 4.1")
    assert normalize_model("claude-sonnet-4-5-20250929") == ("sonnet", "Sonnet 4.5")
    assert normalize_model("claude-3-5-haiku-20241022")[0] == "haiku"


def test_unknown_model_falls_back_to_raw():
    assert normalize_model("some-future-model") == ("some-future-model", "some-future-model")
    assert normalize_model("") == ("unknown", "unknown")


def test_cost_key_aliases():
    assert normalize_cost({"costUSD": 10.25}) == 10.25
    assert normalize_cost({"totalCost": 7.0}) == 7.0
    assert normalize_cost({"totalCostUSD": 3.5}) == 3.5
    assert normalize_cost({}) == 0.0


def test_tokens_alias_and_total_fallback():
    toks = normalize_tokens(
        {"inputTokens": 100, "outputTokens": 200, "cacheCreationTokens": 5, "cacheReadTokens": 7}
    )
    # No explicit totalTokens -> summed from components.
    assert toks["total_tokens"] == 312
    assert toks["output_tokens"] == 200


def test_explicit_total_is_respected():
    toks = normalize_tokens({"inputTokens": 1, "outputTokens": 1, "totalTokens": 999})
    assert toks["total_tokens"] == 999
