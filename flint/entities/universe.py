"""
Copyright (C) 2016, 2017, 2020 biqqles.
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""
from typing import Dict, List, Tuple, Optional
import os

from dataclassy import Internal

from ..formats import dll
from .. import paths, routines, missions
from . import Entity, EntitySet
from .solars import BaseSolar
from .equipment import Equipment, Commodity
from .ship import Ship
from .goods import EquipmentGood, CommodityGood, ShipPackage


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
        return self.contents().of_type(Zone)

    def objects(self) -> 'EntitySet[Object]':
        """All objects in this system."""
        return self.contents().of_type(Object)

    def bases(self) -> 'EntitySet[BaseSolar]':
        """All bases in this system."""
        return self.contents().of_type(BaseSolar)

    def planets(self) -> 'EntitySet[Planet]':
        """All planets in this system."""
        return self.contents().of_type(Planet)

    def stars(self) -> 'EntitySet[Star]':
        """All stars in this system."""
        return self.contents().of_type(Star)

    def connections(self) -> 'Dict[Jump, System]':
        """The connections this system has to other systems."""
        return {c: c.destination_system() for c in self.contents().of_type(Jump)}

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

    def region(self) -> str:
        """The name of the region this system is in, extracted from the infocard."""
        *_, rest = self.infocard('rdl').partition('<TRA data="1" mask="1" def="-2"/><TEXT>')
        region, *_ = rest.partition('</TEXT>')
        return region.title() if region else 'Unknown'


class Base(Entity):
    """A space station or colonised planet, operated by a Faction."""
    ids_info = None  # infocard is defined by the base's solar
    system: str

    def infocard(self, markup='html') -> str:
        """The infocard of this base's solar (Base sections do not define ids_info)."""
        return self.solar().infocard(markup)

    def system_(self) -> System:
        """The entity of the system this base resides in."""
        return routines.get_systems()[self.system]

    def solar(self) -> Optional['BaseSolar']:
        """Confusingly, Freelancer defines bases separately to their physical representation."""
        return self.system_().bases().unique(base=self.nickname)

    def has_solar(self) -> bool:
        """Whether this base has a physical solar."""
        return self.solar() is not None

    def mbase(self) -> Optional[missions.MBase]:
        """The mission base entry for this base."""
        return missions.get_mbases().get(self.nickname)

    def owner(self) -> 'Faction':
        """The faction which owns this base (its IFF)."""
        return self.solar().owner() if self.has_solar() \
            else routines.get_factions()[self.mbase().local_faction] if self.mbase() else None

    def sector(self) -> str:
        """The sector of this base's solar in its system."""
        return self.solar().sector()

    def market(self):
        return routines.get_markets()[self]

    def sells(self) -> Dict['Good', int]:
        """The goods this base sells, of the form {good -> price}."""
        return self.market()[True]

    def buys(self) -> Dict['Good', int]:
        """The goods this base buys, of the form {good -> price}"""
        return self.market()[False]

    def sells_commodities(self) -> Dict[Commodity, int]:
        """The commodities represented by the goods this base sells, mapped to their prices."""
        return {good.commodity(): price for good, price in self.sells().items() if isinstance(good, CommodityGood)}

    def buys_commodities(self) -> Dict[Commodity, int]:
        """The commodities represented by the goods this base buys, mapped to their prices."""
        return {good.commodity(): price for good, price in self.buys().items() if isinstance(good, CommodityGood)}

    def sells_equipment(self) -> Dict[Equipment, int]:
        """The equipment represented by the goods this base sells, mapped to their prices."""
        return {good.equipment_(): price for good, price in self.sells().items() if type(good) is EquipmentGood}

    def sells_ships(self) -> Dict[Ship, int]:
        """The ships represented by the goods this base sells, mapped to their cost."""
        return {good.ship(): good.cost() for good in self.sells() if isinstance(good, ShipPackage)}


class Faction(Entity):
    """A faction, also known as a group, is an organisation in the Freelancer universe, possibly owning bases or
    controlling territory."""
    ids_short_name: int  # resource id for short form name
    rep: Internal[List[Tuple[float, str]]]  # float is between 1 (adored) and -1 (reviled)

    def short_name(self) -> str:
        """The short form of this faction's name."""
        return dll.lookup(self.ids_short_name)

    def bases(self) -> EntitySet[Base]:
        """All bases owned by this faction."""
        return EntitySet(b for s in routines.get_systems() for b in s.bases().where(reputation=self.nickname))

    def rep_sheet(self) -> Dict['Faction', float]:
        """How this faction views other factions - its reputation sheet."""
        factions = routines.get_factions()
        return {factions[faction]: rep for rep, faction in self.rep if faction in factions}

    def can_dock_at(self, base: BaseSolar) -> bool:
        """Whether this faction can dock at the given base."""
        return self.rep_sheet()[base.owner()] > self.NODOCK_REP

    def props(self) -> missions.FactionProps:
        """The FactionProps entry for this faction."""
        return missions.get_faction_props()[self.nickname]

    def legality(self) -> str:
        """The legality of this faction as defined in its FactionProps entry (Lawful or Unlawful)."""
        return self.props().legality.capitalize()

    NODOCK_REP = -0.65


from .solars import Solar, BaseSolar, Jump, Planet, Star, Zone, Object, TradeLaneRing
