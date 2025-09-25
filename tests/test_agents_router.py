import pytest

from agents import router


@pytest.mark.parametrize(
    "message,image_url,expected",
    [
        ("any text", "http://img", "PERSON_PHOTO"),
        ("Tell me about Ada", None, "PERSON_METADATA"),
        ("hello there", None, "CASUAL"),
        ("unhandled", None, "OUT_OF_SCOPE"),
    ],
)
def test_classify(message, image_url, expected):
    assert router.classify(message, image_url) == expected


@pytest.mark.parametrize(
    "message",
    [
        "  Who is Vitalik?",
        "Tell me about someone",
        "WHAT DO YOU THINK OF this legend",
    ],
)
def test_classify_meta_patterns(message):
    assert router.classify(message, None) == "PERSON_METADATA"


@pytest.mark.parametrize(
    "message",
    [
        "Hi there!",
        "HEY buddy",
        "How are you doing?",
        "what's the weather",
    ],
)
def test_classify_casual_patterns(message):
    assert router.classify(message, None) == "CASUAL"
