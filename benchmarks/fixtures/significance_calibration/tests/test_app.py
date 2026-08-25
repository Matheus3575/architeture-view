import pytest
from app import application


def test_application_is_available():
    assert application is not None
