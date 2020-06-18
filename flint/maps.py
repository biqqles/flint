"""
Copyright (C) 2016, 2017, 2020 biqqles.

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.

Functions for working with Freelancer's system layouts and navmaps.
"""
from typing import Any, Dict
from collections import namedtuple
import math

from . import routines
from . import cached

PosVector = namedtuple('pos', 'x y z')
RotVector = namedtuple('rot', 'x y z')


def pos_to_sector(pos: PosVector, navmap_scale: float, divider='-', subdivider='/') -> str:
    """Convert a position vector (e.g. (-45000, 0, 75000)) into a navmap sector coordinate (e.g. 'D-5')."""
    sector_size = NAVMAP_SECTOR_SIZE / navmap_scale  # calculate size of each square
    system_size = sector_size * 8  # maximum possible x & z

    def quantise(dimension, labels):
        """Quantise a dimension `dimension` on an axis with labels `labels`."""
        magnitude = (dimension + system_size / 2) / sector_size  # "absolute magnitude" - a decimal between 0 and 7
        sector = math.floor(magnitude)
        subsector = magnitude - sector  # magnitude in the square the point rests in
        try:
            result = [labels[sector]]
        except IndexError:
            return 'Unknown'
        if subsector <= 0.2 and sector > 0:  # if it is close to the left/bottom of the square...
            result.append(labels[sector - 1])  # ...create something like B/C or 2/3
        elif subsector >= 0.8 and sector < 7:
            result.append(labels[sector + 1])
        return subdivider.join(result)

    # todo: maybe do something with pos.y < 500 >
    return divider.join(map(quantise, (pos.x, pos.z), (NAVMAP_X_LABELS, NAVMAP_Z_LABELS)))


def inter_system_route(from_system: 'System', to_system: 'System'):
    """Find the shortest route (in terms of the number of systems) between two systems."""
    return dijkstra(generate_universe_graph(), from_system, to_system)


def intra_system_route(from_solar: 'Solar', to_solar: 'Solar'):
    """Find the shortest route between two solars in the same system."""
    assert from_solar._system == to_solar._system
    raise NotImplementedError


@cached
def generate_universe_graph() -> Dict['System', Dict['System', int]]:
    """Generate a graph of all systems and their connections.
    Todo: calculate weight between system entrances and exits rather than using a simple placeholder."""
    return {s: {d: 1 for d in s.connections().values()} for s in routines.get_systems()}


def dijkstra(graph: Dict[Any, Dict[Any, int]], start: Any, end: Any):
    """An implementation of Dijkstra's algorithm using only builtin types.

    `graph` is represented by a dictionary of nodes mapped to dictionaries of their connections with the weights of
    those connections.

    Rather over-documented as I described this algorithm as part of the coursework I used this for.
    Currently pretty basic - weight (i.e. the time to travel between the input and exit points of a system) is currently
    not calculated."""
    distances, predecessors = {}, {}
    # the predecessors for a node are just the other nodes that lie on the shortest path from the starting point to that
    # node. Set all distances to zero, and all predecessors to
    for node in graph:
        distances[node] = math.inf
        predecessors[node] = None
    distances[start] = 0  # distance from the start node is 0
    to_check = list(graph)  # a list of nodes that need to be checked
    while to_check:  # While there are still nodes to check...
        closest = min(to_check, key=distances.get)  # find the closest node to the current node
        to_check.remove(closest)  # it's been checked, so can be removed
        for node, weight in graph[closest].items():
            new_distance = distances[closest] + weight
            if new_distance < distances.get(node, math.inf):
                distances[node] = new_distance
                predecessors[node] = closest
    path = [end]
    # now look through the predecessors to find the path
    while start not in path:
        path.append(predecessors[path[-1]])
    path.reverse()  # reverse dictionary (so the start is first and end is last)
    return path


NAVMAP_X_LABELS = tuple(chr(x) for x in range(ord('A'), ord('H') + 1))
NAVMAP_Z_LABELS = tuple(str(x) for x in range(1, 9))
NAVMAP_SECTOR_SIZE = 34000
DEFAULT_CRUISE_SPEED = 300
DEFAULT_LANE_SPEED = 1000
