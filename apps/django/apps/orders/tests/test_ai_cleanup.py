from apps.orders.ai_cleanup import _build_prompt


def test_build_prompt_without_operator_or_specs():
    prompt = _build_prompt()
    assert 'Clean up this image' in prompt


def test_build_prompt_with_operator_and_specs():
    specs = {
        'width_mm': 240,
        'height_mm': 92,
        'dpi': 300,
        'background': 'white',
        'format': 'png',
    }
    prompt = _build_prompt('Make background blue', specs)
    assert 'Make background blue' in prompt
    assert '240x92 mm' in prompt
    assert '300 DPI' in prompt
