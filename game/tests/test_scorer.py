import pytest
from game.scorer import calculate_points


class TestCalculatePoints:
    def test_round_1_no_multiplier(self):
        assert calculate_points(100, 1) == 100

    def test_round_2_no_multiplier(self):
        assert calculate_points(300, 2) == 300

    def test_round_3_doubles(self):
        assert calculate_points(100, 3) == 200

    def test_round_3_doubles_all_tiers(self):
        for base in [100, 200, 300, 400, 500]:
            assert calculate_points(base, 3) == base * 2

    def test_zero_base_always_zero(self):
        for r in [1, 2, 3]:
            assert calculate_points(0, r) == 0
