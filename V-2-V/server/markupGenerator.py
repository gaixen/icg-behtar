# markup_generator.py
def generate_markup(phonemes, emotion):
    """Combine phonemes and emotion tag for TTS model."""
    markup = f"<emotion:{emotion}> <phoneme>{phonemes}</phoneme>"
    return markup
