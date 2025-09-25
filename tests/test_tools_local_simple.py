import pytest

from tools import local_simple


@pytest.mark.parametrize(
    "message,expected",
    [
        ("Hi", "Hey. I'm the Projector engine."),
        ("hello there", "Hey. I'm the Projector engine."),
        ("hey!", "Hey. I'm the Projector engine."),
    ],
)
def test_answer_casual_greetings(message, expected):
    assert local_simple.answer_casual(message).startswith(expected)


def test_answer_casual_how_are_you():
    assert "Functional" in local_simple.answer_casual("How are you today?")


def test_answer_casual_weather():
    response = local_simple.answer_casual("What's the weather in new york?")
    assert "New York" in response
    assert "22°C" in response


def test_answer_casual_default():
    assert "Casual path engaged" in local_simple.answer_casual("random question")
