from parity_check.compare.normalize import normalize_json


def test_normalize_sorts_object_keys_recursively():
    left = {"b": 1, "a": {"z": 1, "y": 2}}
    right = {"a": {"y": 2, "z": 1}, "b": 1}
    assert normalize_json(left) == normalize_json(right)


def test_normalize_preserves_array_order():
    left = [3, 1, 2]
    right = [1, 2, 3]
    assert normalize_json(left) != normalize_json(right)
