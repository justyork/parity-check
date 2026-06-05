from parity_check.compare.normalize import normalize_json, normalize_url_query


def test_normalize_url_query_sorts_parameters():
    left = (
        "https://d1asmjcgpzozfm.cloudfront.net:443/cmp/tcf-dialogs/63f64902-1d67-4a25-b893-77178a2841f2"
        "?gdprApplies=1&eeaApplies=1&name=HappyColor"
    )
    right = (
        "https://d1asmjcgpzozfm.cloudfront.net:443/cmp/tcf-dialogs/63f64902-1d67-4a25-b893-77178a2841f2"
        "?eeaApplies=1&gdprApplies=1&name=HappyColor"
    )
    assert normalize_url_query(left) == normalize_url_query(right)


def test_normalize_url_query_leaves_non_url_unchanged():
    assert normalize_url_query("not a url") == "not a url"
    assert normalize_url_query("/relative?b=2&a=1") == "/relative?b=2&a=1"


def test_normalize_json_treats_same_url_with_different_query_order_as_equal():
    left = {"dialogUri": "https://example.com/path?b=2&a=1"}
    right = {"dialogUri": "https://example.com/path?a=1&b=2"}
    assert normalize_json(left) == normalize_json(right)


def test_normalize_sorts_object_keys_recursively():
    left = {"b": 1, "a": {"z": 1, "y": 2}}
    right = {"a": {"y": 2, "z": 1}, "b": 1}
    assert normalize_json(left) == normalize_json(right)


def test_normalize_preserves_array_order():
    left = [3, 1, 2]
    right = [1, 2, 3]
    assert normalize_json(left) != normalize_json(right)
