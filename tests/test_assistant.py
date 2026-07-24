from waste_classifier.genai.assistant import _build_messages


def test_build_messages_defaults_to_english():
    messages = _build_messages("Can I recycle glass?", None, None)
    system = messages[0]["content"]
    assert "Respond in Urdu" not in system


def test_build_messages_adds_urdu_instruction_when_requested():
    messages = _build_messages("Can I recycle glass?", None, None, language="ur")
    system = messages[0]["content"]
    assert "Respond in Urdu" in system
    assert "اردو" in system


def test_build_messages_includes_classification_label():
    messages = _build_messages("How do I recycle this?", "plastic", None)
    system = messages[0]["content"]
    assert "plastic" in system


def test_build_messages_includes_history_and_question_in_order():
    history = [{"role": "user", "content": "hi"}, {"role": "assistant", "content": "hello"}]
    messages = _build_messages("follow up question", None, history)

    assert messages[0]["role"] == "system"
    assert messages[1] == history[0]
    assert messages[2] == history[1]
    assert messages[-1] == {"role": "user", "content": "follow up question"}
