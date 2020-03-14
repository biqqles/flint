#  Copyright (C) 2016, 2017, 2020 biqqles.
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.
import dataclasses
import os
from typing import Dict, List, Tuple

from .. import paths
from .. import routines
from . import Entity, EntitySet


class System(Entity):
    """A star system."""
    file: str
    navmapscale: float = 1.0

    def contents(self) -> 'EntitySet[Solar]':
        """The contents of this system."""
        return routines.get_system_contents(self)

    def definition_path(self) -> str:
        """The absolute path to the file that defines this system's contents."""
        return paths.construct_path(os.path.dirname(paths.inis['universe'][0]), self.file)

    def bases(self) -> 'EntitySet[BaseSolar]':
        """The bases in this system."""
        return EntitySet(c for c in self.contents() if isinstance(c, BaseSolar))

    def planets(self):
        return EntitySet(c for c in self.contents() if isinstance(c, Planet))

    def suns(self):
        return EntitySet(c for c in self.contents() if isinstance(c, Star))

    def connections(self):
        """The systems this system has jumps to."""
        return {c: c.destination_system() for c in self.contents() if isinstance(c, Jump)}

    def graph(self):
        raise NotImplementedError


class Base(Entity):
    """A space station or colonised planet, operated by a Group."""
    system: str
    _market: Dict = dataclasses.field(repr=False)

    def infocard(self, plain=False) -> str:
        return self.solar().infocard(plain)

    def solar(self) -> 'BaseSolar':
        """Confusingly, Freelancer defines bases separately to their physical representation."""
        return routines.get_systems()[self.system].bases().where(base=self.nickname).arb

    def sector(self):
        return self.solar().sector()

    def sells(self) -> Dict[str, int]:
        """The goods this base sells, of the form {good -> price}."""
        return dict(self._market[True])

    def buys(self) -> Dict[str, int]:
        """The goods this base buys, of the form {good -> price}"""
        return dict(self._market[False])


class Group(Entity):
    """A Group, also known as a faction, is an organisation in the Freelancer universe."""
    rep: List[Tuple[float, str]] = dataclasses.field(repr=False)  # float is between 1 (adored) and -1 (reviled)

    def bases(self) -> EntitySet[Base]:
        """All bases owned by this group."""
        return EntitySet(b for s in routines.get_systems() for b in s.bases().where(reputation=self.nickname))

    def rep_sheet(self) -> Dict[str, float]:
        """How this faction views other factions - its "reputation sheet". float is between 1 (adored) and -1
        (reviled)"""
        return {f: r for r, f in self.rep}


from .solars import Solar, BaseSolar, Jump, Planet, Star
