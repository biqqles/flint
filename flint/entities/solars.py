"""
Copyright (C) 2016, 2017, 2020 biqqles.

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""
from typing import Tuple, Optional, Union

from .. import maps
from . import Entity
from ..formats import ini, dll


class Solar(Entity):
    """A solar is something fixed in space (this name comes from the DATA/SOLAR directory)."""
    pos: maps.PosVector
    rotate: maps.RotVector
    _system: 'System'  # the system this solar resides in

    def sector(self) -> str:
        """The human-readable navmap coordinate (the centre of) this solar resides in."""
        return maps.pos_to_sector(self.pos, self._system.navmapscale)


class Object(Solar):
    """Generic class for a celestial body - a solid object in space."""
    archetype: str


class Jump(Object):
    """A jump conduit is a wormhole - artificial or natural - between star systems."""
    goto: Tuple[str, str, str]

    def type(self):
        """Return a human readable name of this jump conduits's type."""
        if 'gate' in self.archetype: return 'Jump Gate'
        if 'jumphole' in self.archetype: return 'Jump Hole'
        if self.archetype == 'entrypoint': return 'Atmospheric Entry'
        return 'Unknown'

    def origin_system(self) -> 'System':
        """The system this wormhole starts in."""
        return self._system

    def destination_system(self) -> 'System':
        """The system this wormhole ends in."""
        return routines.get_systems()[self.goto[0]]


class TradeLaneRing(Object):
    """A trade lane ring is a component of a trade lane, a structure which provides "superluminal travel" within a
    system."""
    prev_ring: Optional[str]
    next_ring: Optional[str]

    def next_object(self):
        return self._system.contents()[self.next_ring]


class Wreck(Object):
    """A wreck (called "secrets" in the game files is a lootable, wrecked ship floating in space."""
    loadout: str  # loot that is dropped upon being shot


class BaseSolar(Object):
    """The physical representation of a Base."""
    reputation: str  # the faction this base belongs to
    base: str  # the base (in universe) this solar represents

    def base(self):
        return self._system.bases().get(self.nickname)

    def owner(self):
        return routines.get_groups()[self.reputation]

    def infocard(self, plain=False) -> str:
        """Base infocards are actually in two parts, with ids_info referring to the specs of a base and ids_info + 1
        storing the actual description"""
        lookup = dll.lookup if plain else dll.lookup_as_html

        specifications = lookup(self.ids_info)
        try:
            synopsis = lookup(self.ids_info + 1)
            return specifications + '<p>' + synopsis
        except KeyError:
            return specifications


class Spheroid(Object):
    """A star or planet. (Abstract.)"""
    atmosphere_range: int


class Star(Spheroid):
    """A star in a System."""
    star: str


class Planet(Spheroid):
    """A planet in a System."""
    spin: Tuple[float, float, float]


class PlanetaryBase(BaseSolar, Planet):
    """A base on the surface of a planet, typically accessible via a docking ring."""
    pass


from .universe import System

from .. import routines
