"""
Performance tests for Planet and Planet3D classes.
These tests are not strictly necessary for correctness, but they help ensure
that the vectorized implementations are substantially faster than the naive approach.
"""

import os
import sys
import time

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from distance import distance
from PlanetClasses import Planet, Planet3D


def _loop_planet2d(period, time_arr, Distance, eccentricity):
    """Pre-vectorization implementation of Planet.coordinates."""
    theta = (2 * np.pi * time_arr) / period
    x_coordinate = []
    y_coordinate = []
    for i in range(len(time_arr)):
        r = distance(Distance, theta[i], eccentricity)
        x_coordinate.append(r * np.cos(theta[i]))
        y_coordinate.append(r * np.sin(theta[i]))
    return x_coordinate, y_coordinate


def _loop_planet3d(period, time_arr, Distance, eccentricity, inclination):
    """Pre-vectorization implementation of Planet3D.coordinates."""
    theta = (2 * np.pi * time_arr) / period
    x_coordinate, y_coordinate, z_coordinate = [], [], []
    for i in range(len(time_arr)):
        r = distance(Distance, theta[i], eccentricity)
        x_coordinate.append(r * np.cos(theta[i]) * np.cos(inclination))
        y_coordinate.append(r * np.sin(theta[i]))
        z_coordinate.append(r * np.cos(theta[i]) * np.sin(inclination))
    return x_coordinate, y_coordinate, z_coordinate


def test_vectorized_2d_matches_loop_reference():
    time_arr = np.linspace(0, 5, 2000)
    x_loop, y_loop = _loop_planet2d(1.2, time_arr, 1.523, 0.0934)
    x_vec, y_vec = Planet(1.2, time_arr).coordinates(1.523, 0.0934)
    assert np.allclose(x_vec, x_loop)
    assert np.allclose(y_vec, y_loop)


def test_vectorized_3d_matches_loop_reference():
    time_arr = np.linspace(0, 5, 2000)
    x_loop, y_loop, z_loop = _loop_planet3d(
        1.2, time_arr, 1.523, 0.0934, np.radians(1.85)
    )
    x_vec, y_vec, z_vec = Planet3D(1.2, time_arr).coordinates(
        1.523, 0.0934, np.radians(1.85)
    )
    assert np.allclose(x_vec, x_loop)
    assert np.allclose(y_vec, y_loop)
    assert np.allclose(z_vec, z_loop)


def _time_it(fn, repeats=5):
    best = float("inf")
    for _ in range(repeats):
        start = time.perf_counter()
        fn()
        best = min(best, time.perf_counter() - start)
    return best


@pytest.mark.parametrize("n_points", [20_000])
def test_vectorization_speedup_is_substantial(n_points):
    """
    Quantifies the speedup from vectorization at a point count representative
    of the outer 3D view (the case called out as slow in commit b2192d5).
    Asserts a conservative 5x floor so the test stays robust across
    machines/CI runners while still proving the optimization is real.
    """
    time_arr = np.linspace(0, 50, n_points)

    loop_time = _time_it(
        lambda: _loop_planet3d(1.2, time_arr, 1.523, 0.0934, np.radians(1.85))
    )
    vector_time = _time_it(
        lambda: Planet3D(1.2, time_arr).coordinates(1.523, 0.0934, np.radians(1.85))
    )

    speedup = loop_time / vector_time
    print(f"\nvectorization speedup at n={n_points}: {speedup:.1f}x "
          f"(loop={loop_time * 1000:.2f}ms, vector={vector_time * 1000:.2f}ms)")

    assert speedup > 5.0


def test_planet_data_ranges_are_physically_valid():
    from planets import PLANETS

    for name, p in PLANETS.items():
        assert p["au"] > 0, f"{name}: semi-major axis must be positive"
        assert p["period"] > 0, f"{name}: orbital period must be positive"
        assert 0 <= p["ecc"] < 1, f"{name}: eccentricity must be in [0, 1)"
        assert 0 <= p["inc"] < 90, f"{name}: inclination (deg) out of range"


def test_planet_data_ordered_by_increasing_distance():
    from planets import PLANETS

    distances = [p["au"] for p in PLANETS.values()]
    assert distances == sorted(distances), (
        "PLANETS dict should list planets in increasing distance from the Sun"
    )
