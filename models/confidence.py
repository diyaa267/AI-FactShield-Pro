def confidence_from_scores(fake_score, real_score):
    total = max(fake_score + real_score, 1)
    value = max(fake_score, real_score) / total
    return round(55 + value * 42, 2)
