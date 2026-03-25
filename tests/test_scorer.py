"""Tests for core.scorer — scoring logic."""

from core.scorer import (
    Scorecard,
    compute_overall,
    is_graduated,
    grade_label,
    WEIGHTS,
)


class TestComputeOverall:
    def test_basic_computation(self):
        # 0.30*80 + 0.25*90 + 0.25*70 + 0.20*60
        # = 24 + 22.5 + 17.5 + 12 = 76
        assert compute_overall(80, 70, 90, 60) == 76

    def test_all_zeros(self):
        assert compute_overall(0, 0, 0, 0) == 0

    def test_all_100(self):
        assert compute_overall(100, 100, 100, 100) == 100

    def test_clamped_to_100(self):
        result = compute_overall(100, 100, 100, 100)
        assert result <= 100

    def test_weights_sum_to_one(self):
        assert abs(sum(WEIGHTS.values()) - 1.0) < 1e-10


class TestScorecard:
    def test_auto_compute_overall(self):
        sc = Scorecard(reliability=80, cost=70, safety=90, speed=60)
        assert sc.overall == 76

    def test_clamps_values(self):
        sc = Scorecard(reliability=150, cost=-10, safety=200, speed=50)
        assert sc.reliability == 100
        assert sc.cost == 0
        assert sc.safety == 100
        assert sc.speed == 50

    def test_to_dict(self):
        sc = Scorecard(reliability=80, cost=70, safety=90, speed=60)
        d = sc.to_dict()
        assert d["reliability"] == 80
        assert "overall" in d

    def test_from_dict(self):
        d = {"reliability": 80, "cost": 70, "safety": 90, "speed": 60, "overall": 76}
        sc = Scorecard.from_dict(d)
        assert sc.reliability == 80
        assert sc.overall == 76

    def test_from_dict_defaults(self):
        sc = Scorecard.from_dict({})
        assert sc.reliability == 0
        assert sc.overall == 0


class TestIsGraduated:
    def test_above_threshold(self):
        sc = Scorecard(reliability=90, cost=80, safety=85, speed=75)
        assert is_graduated(sc) is True

    def test_below_threshold(self):
        sc = Scorecard(reliability=50, cost=40, safety=60, speed=30)
        assert is_graduated(sc) is False

    def test_at_threshold(self):
        sc = Scorecard(reliability=75, cost=75, safety=75, speed=75)
        assert is_graduated(sc) is True

    def test_custom_threshold(self):
        sc = Scorecard(reliability=80, cost=80, safety=80, speed=80)
        assert is_graduated(sc, threshold=90) is False
        assert is_graduated(sc, threshold=70) is True


class TestGradeLabel:
    def test_grade_a_plus(self):
        sc = Scorecard(reliability=95, cost=90, safety=95, speed=90)
        assert grade_label(sc) == "A+"

    def test_grade_f(self):
        sc = Scorecard(reliability=10, cost=10, safety=10, speed=10)
        assert grade_label(sc) == "F"

    def test_grade_c(self):
        sc = Scorecard(reliability=55, cost=55, safety=55, speed=55)
        assert grade_label(sc) == "C"
