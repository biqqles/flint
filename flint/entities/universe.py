"""
Copyright (C) 2016, 2017, 2020 biqqles.
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""
from typing import Dict, List, Tuple
import os

from dataclassy import Internal

from .. import paths
from .. import routines
from . import Entity, EntitySet


class System(Entity):
    """A star system."""
    file: str
    navmapscale: float = 1.0

    def definition_path(self) -> str:
        """The absolute path to the file that defines this system's contents."""
        return paths.construct_path(os.path.dirname(paths.inis['universe'][0]), self.file)

    def contents(self) -> 'EntitySet[Solar]':
        """All solars in this system."""
        return routines.get_system_contents(self)

    def zones(self) -> 'EntitySet[Zone]':
        """All zones in this system."""
        return EntitySet(c for c in self.contents() if isinstance(c, Zone))

    def objects(self) -> 'EntitySet[Object]':
        """All objects in this system."""
        return EntitySet(c for c in self.contents() if isinstance(c, Object))

    def bases(self) -> 'EntitySet[BaseSolar]':
        """All bases in this system."""
        return EntitySet(c for c in self.objects() if isinstance(c, BaseSolar))

    def planets(self) -> 'EntitySet[Planet]':
        """All planets in this system."""
        return EntitySet(c for c in self.objects() if isinstance(c, Planet))

    def stars(self) -> 'EntitySet[Star]':
        """All stars in this system."""
        return EntitySet(c for c in self.objects() if isinstance(c, Star))

    def connections(self) -> 'Dict[Jump, System]':
        """The connections this system has to other systems."""
        return {c: c.destination_system() for c in self.objects() if isinstance(c, Jump)}

    def lanes(self) -> 'List[List[TradeLaneRing]]':
        """Return a list of lists of rings, where each nested list represents a complete trade lane and contains each
        ring in that lane in order."""
        rings = EntitySet(c for c in self.contents() if isinstance(c, TradeLaneRing))
        lanes = {r: [] for r in rings if r.prev_ring is None}  # find rings which start a lane
        # group remaining rings into one of these
        for first_ring in lanes:
            current_ring = first_ring
            while current_ring:
                current_ring = rings.get(current_ring.next_ring)
                if current_ring:
                    lanes[first_ring].append(current_ring)
        return [[f, *r] for f, r in lanes.items()]  # flatten grouping dict into list of lists


class Base(Entity):
    """A space station or colonised planet, operated by a Group."""
    system: str
    _market: Dict

    def infocard(self, plain=False) -> str:
        return self.solar().infocard(plain)

    def system_(self) -> System:
        """The entity of the system this base resides in."""
        return routines.get_systems()[self.system]

    def solar(self) -> 'BaseSolar':
        """Confusingly, Freelancer defines bases separately to their physical representation."""
        return self.system_().bases().where(base=self.nickname).arb

    def sector(self):
        """The sector of this base's solar in its system."""
        return self.solar().sector()

    def sells(self) -> Dict[str, int]:
        """The goods this base sells, of the form {good -> price}."""
        return dict(self._market[True])

    def buys(self) -> Dict[str, int]:
        """The goods this base buys, of the form {good -> price}"""
        return dict(self._market[False])


class Group(Entity):
    """A Group, also known as a faction, is an organisation in the Freelancer universe."""
    rep: Internal[List[Tuple[float, str]]]  # float is between 1 (adored) and -1 (reviled)

    def bases(self) -> EntitySet[Base]:
        """All bases owned by this group."""
        return EntitySet(b for s in routines.get_systems() for b in s.bases().where(reputation=self.nickname))

    def rep_sheet(self) -> Dict[str, float]:
        """How this faction views other factions - its "reputation sheet". float is between 1 (adored) and -1
        (reviled)"""
        return {f: r for r, f in self.rep}


from .solars import Solar, BaseSolar, Jump, Planet, Star, Zone, Object, TradeLaneRing
