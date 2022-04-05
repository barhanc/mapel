import unittest
import uuid
from collections import defaultdict
from typing import List

import numpy as np

from mapel.main.features.common import extract_calculated_distances, extract_selected_distances, \
    extract_selected_coordinates
from mapel.main.objects.Experiment import Experiment


def _remove_diagonal(A):
    return A[~np.eye(A.shape[0], dtype=bool)].reshape(A.shape[0], -1)


def calculate_monotonicity(experiment: Experiment, election_ids: List[str] = None, max_distance_percentage=1.0,
                           error_tolerance=0.01):
    if election_ids is None:
        election_ids = list(experiment.distances.keys())

    coordinates = extract_selected_coordinates(experiment, election_ids)

    desired_distances = extract_selected_distances(experiment, election_ids)
    calculated_distances = np.linalg.norm(coordinates[:, np.newaxis] - coordinates[np.newaxis, :], axis=2)

    max_distance = np.max(desired_distances)

    good_distances_mask = desired_distances <= max_distance * max_distance_percentage
    good_distances_mask = _remove_diagonal(good_distances_mask)
    good_distances_mask = good_distances_mask[:, :, np.newaxis] * good_distances_mask[:, np.newaxis, :]

    calculated_triangles_diff, _ = _get_triangles_differences(calculated_distances, good_distances_mask)
    desired_triangles_diff, desired_mask = _get_triangles_differences(desired_distances, good_distances_mask)

    mul = calculated_triangles_diff * desired_triangles_diff

    good_triangles = mul > 0
    good_triangles |= (mul < 0) & (np.abs(calculated_triangles_diff) < error_tolerance * max_distance)

    triangles_sums = good_triangles.sum(axis=1) / (good_triangles.shape[1] - (~desired_mask).sum(axis=1))

    return {
        election: triangles_sums[i] for i, election in enumerate(election_ids)
    }


def _get_triangles_differences(distances, good_distances_mask):
    n = distances.shape[0]
    coordinates_delta = _remove_diagonal(distances)

    coordinates_delta = coordinates_delta[:, :, np.newaxis] - coordinates_delta[:, np.newaxis, :]

    iu1 = np.triu_indices(n - 1, k=1)
    fill = np.zeros(shape=(n - 1, n - 1), dtype=bool)
    fill[iu1] = True
    coordinates_delta[~good_distances_mask] = 0

    return coordinates_delta[:, fill], good_distances_mask[:, fill]


def calculate_monotonicity_naive(experiment: Experiment, election_ids: List[str] = None, max_distance_percentage=1.0,
                                 error_tolerance=0.01):
    coordinates = extract_selected_coordinates(experiment, election_ids)

    desired_distances = extract_selected_distances(experiment, election_ids)
    calculated_distances = np.linalg.norm(coordinates[:, np.newaxis] - coordinates[np.newaxis, :], axis=2)

    max_distance = np.max(desired_distances)

    allowed_distance = max_distance * max_distance_percentage

    n = desired_distances.shape[0]

    good_distances = defaultdict(int)
    all_distances = defaultdict(int)

    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            for k in range(n):
                if k == i or k == j:
                    continue

                if desired_distances[i, j] <= allowed_distance and desired_distances[i, k] <= allowed_distance:
                    calc = calculated_distances[i, j] - calculated_distances[i, k]
                    des = desired_distances[i, j] - desired_distances[i, k]

                    is_good = (calc * des > 0) or (abs(calc) < error_tolerance * max_distance)

                    all_distances[i] += 1
                    if is_good:
                        good_distances[i] += 1

    return {
        election: good_distances[i] / all_distances[i] for i, election in enumerate(election_ids)
    }


class TestMonotonicity(unittest.TestCase):
    def test_calculate_monotonicity(self):
        n = 200
        election_ids = [str(uuid.uuid4()) for _ in range(n)]

        class MockExperiment:
            def __init__(self):
                self.coordinates = {
                    e: np.random.uniform(-10, 10, size=(2,)) for e in election_ids
                }

                self.distances = {
                    e1: {e2: np.random.uniform(-10, 10) for e2 in election_ids}
                    for e1 in election_ids
                }

        experiment = MockExperiment()

        m1 = calculate_monotonicity(experiment, election_ids, 0.95)
        print("m1 done")
        m2 = calculate_monotonicity_naive(experiment, election_ids, 0.95)
        print("m2 done")

        self.assertEqual(m1, m2)
