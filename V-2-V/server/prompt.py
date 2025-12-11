def build_llm_prompt(user_text, emotion):
    return f"""
            You are an expressive conversational AI.
            The user said (with {emotion} emotion): "{user_text}".
    Respond empathetically, preserving emotional context.
    Output your response in this JSON format:
{{
  "emotion": "<emotion label>",
  "phonetic_text": "<phonetic version of your response>",
  "text": "<natural text to speak>"
}}
"""
