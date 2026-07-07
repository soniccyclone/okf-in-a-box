from src.foo import foo


def test_foo() -> None:
    assert foo() == 42
