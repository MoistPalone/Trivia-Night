ROUND_MULTIPLIERS: dict[int, int] = {1: 1, 2: 1, 3: 2}


def calculate_points(base_points: int, round_number: int) -> int:
    return base_points * ROUND_MULTIPLIERS[round_number]
