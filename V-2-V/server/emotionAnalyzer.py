def classify_emotion(features):
    f0 = features["f0_mean"]
    energy = features["energy"]
    # simple heuristics
    if f0 > 200 and energy > 0.05:
        return "happy"
    elif f0 < 120 and energy < 0.03:
        return "sad"
    elif energy > 0.08:
        return "angry"
    else:
        return "neutral"
