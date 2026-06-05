from parity_check.compare.diff import _build_unified_style_diff, compare_responses
from parity_check.http.runner import HttpResponse


def _response(status: int, body: str) -> HttpResponse:
    return HttpResponse(status_code=status, body_text=body, headers={})


def test_compare_equal_json_same_url_different_query_param_order():
    left = _response(
        200,
        '{"dialogUri": "https://example.com/path?gdprApplies=1&eeaApplies=1&name=HappyColor"}',
    )
    right = _response(
        200,
        '{"dialogUri": "https://example.com/path?eeaApplies=1&gdprApplies=1&name=HappyColor"}',
    )
    result = compare_responses(left, right)
    assert result.equal
    assert result.body_equal


def test_compare_equal_json_different_key_order():
    left = _response(200, '{"b": 2, "a": 1}')
    right = _response(200, '{"a": 1, "b": 2}')
    result = compare_responses(left, right)
    assert result.equal
    assert result.status_equal
    assert result.body_equal


def test_compare_status_mismatch():
    left = _response(200, '{"ok": true}')
    right = _response(500, '{"ok": true}')
    result = compare_responses(left, right)
    assert not result.equal
    assert not result.status_equal
    assert result.body_equal


def test_compare_body_mismatch():
    left = _response(200, '{"value": 1}')
    right = _response(200, '{"value": 2}')
    result = compare_responses(left, right)
    assert not result.equal
    assert result.status_equal
    assert not result.body_equal
    assert result.body_diff_text
    assert "--- left\n+++ right\n" in result.body_diff_text


def test_unified_diff_has_line_breaks():
    diff = _build_unified_style_diff('{"a": 1}', '{"a": 2}')
    assert "--- left\n" in diff
    assert "+++ right\n" in diff


def test_compare_ignore_paths():
    left = _response(200, '{"id": 1, "generated_at": "a"}')
    right = _response(200, '{"id": 1, "generated_at": "b"}')
    result = compare_responses(left, right, ignore_paths=["$.generated_at"])
    assert result.equal


def test_compare_text_bodies():
    left = _response(200, "plain text")
    right = _response(200, "plain text")
    result = compare_responses(left, right)
    assert result.equal
