#!/usr/bin/env python

from mapel.voting.elections.group_separable import get_gs_caterpillar_matrix
from mapel.voting.elections.single_peaked import get_walsh_matrix, get_conitzer_matrix
from mapel.voting.elections.single_crossing import get_single_crossing_matrix
from . import _elections as el

from .objects.Election import Election, get_fake_vectors_single, get_fake_convex
from .objects.Experiment import Experiment

import os
import csv


def prepare_matrices(experiment_id):
    """ compute positionwise matrices and store them in the /matrices folder """
    experiment = Experiment(experiment_id)

    path = os.path.join(os.getcwd(), "experiments", experiment_id, "matrices")
    for file_name in os.listdir(path):
        os.remove(os.path.join(path, file_name))

    for election_id in experiment.elections:
        matrix = experiment.elections[election_id].votes_to_positionwise_matrix()
        path = os.path.join(os.getcwd(), "experiments", experiment_id,
                            "matrices", str(election_id) + ".csv")
        with open(path, 'w', newline='') as csv_file:
            writer = csv.writer(csv_file, delimiter=',')
            for row in matrix:
                writer.writerow(row)


def generate_positionwise_matrix(election_model=None, num_candidates=None, num_voters=100, param_1=None, param_2=None):
    # todo: there is a repetition of this code in Election file

    # EXACT -- STATISTICAL CULTURES
    if election_model == 'conitzer':
        return get_conitzer_matrix(num_candidates)
    elif election_model == 'walsh':
        return get_walsh_matrix(num_candidates)
    elif election_model == 'single-crossing':
        return get_single_crossing_matrix(num_candidates)
    elif election_model == 'gs_caterpillar':
        return get_gs_caterpillar_matrix(num_candidates)
    # EXACT -- PATHS
    elif election_model in {'identity', 'uniformity', 'antagonism', 'stratification',
                            'walsh_fake', 'conitzer_fake'}:
        return get_fake_vectors_single(election_model, num_candidates, num_voters)
    elif election_model in {'unid', 'anid', 'stid', 'anun', 'stun', 'stan'}:
        return get_fake_convex(election_model, num_candidates, num_voters, param_1, get_fake_vectors_single)
    # APPROXIMATION
    else:
        votes = el.generate_votes(election_model=election_model, num_candidates=num_candidates,
                                  num_voters=num_voters, param_1=param_1, param_2=param_2)
        return get_positionwise_matrix(votes)


def get_positionwise_matrix(votes):
    election = Election("virtual", "virtual", votes=votes)
    return election.votes_to_positionwise_matrix()
