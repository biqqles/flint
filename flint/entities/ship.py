"""
Copyright (C) 2016, 2017, 2020 biqqles.

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""
from typing import Tuple, List, Optional
import math
from statistics import mean

from . import Entity, EntitySet
from .goods import ShipHull, ShipPackage
from .equipment import Equipment, Power, Engine
from ..formats import dll
from .. import routines


class Ship(Entity):
    """A starship with a cargo bay and possibly hardpoints for weapons."""
    ids_info1: int  # ship description (ids_info stores statistics)
    ids_info2: int  # extra stat names list
    ids_info3: int  # extra stat values list
    ship_class: int
    hit_pts: int
    hold_size: int
    mass: int
    linear_drag: int
    nanobot_limit: int = 0
    shield_battery_limit: int = 0
    steering_torque: Tuple[float, float, float]
    angular_drag: Tuple[float, float, float]
    rotation_inertia: Tuple[float, float, float]

    def hull(self) -> Optional[ShipHull]:
        """This ship's hull entity."""
        return routines.get_goods().of_type(ShipHull).unique(ship=self.nickname)

    def package(self) -> Optional[ShipPackage]:
        """This ship's package entity."""
        if not self.hull():
            return None
        return routines.get_goods().of_type(ShipPackage).unique(hull=self.hull().nickname)

    def sold_at(self) -> List['Base']:
        """A list of bases which sell this ship."""
        if not self.package():
            return []
        return list(self.package().sold_at().keys())

    def price(self) -> int:
        """The price of this ship's hull."""
        try:
            return self.hull().price
        except AttributeError:
            return 0

    def icon(self) -> bytes:
        """This ship's icon."""
        return self.hull().icon()

    def infocard(self, markup='html') -> str:
        """I have no idea why the order these are displayed in is not ascending, but anyway."""
        if markup == 'html':
            lookup = dll.lookup_as_html
        elif markup == 'plain':
            lookup = dll.lookup_as_plain
        elif markup == 'rdl':
            lookup = dll.lookup
        else:
            raise ValueError
        return '<p>'.join(map(lookup, (self.ids_info1, self.ids_info)))

    def type(self) -> str:
        """The name of the type (class) of this ship."""
        return self.TYPE_ID_TO_NAME.get(self.ship_class)

    def equipment(self) -> EntitySet[Equipment]:
        """The set of this ship package's equipment upon purchase."""
        package = self.package()
        return package.equipment() if package else EntitySet([])

    def power_core(self) -> Power:
        """The Power entity for this ship."""
        return self.equipment().of_type(Power).first

    def engine(self) -> Engine:
        """The Power entity for this ship."""
        return self.equipment().of_type(Engine).first

    def impulse_speed(self) -> float:
        """The maximum forward impulse (non-cruise) speed of this ship."""
        engine = self.engine()
        if not engine:
            return 0
        try:
            return engine.max_force / (engine.linear_drag + self.linear_drag)
        except TypeError:
            return 0

    def reverse_speed(self) -> float:
        """The maximum reverse speed of this ship."""
        engine = self.engine()
        return self.impulse_speed() * self.engine().reverse_fraction if engine else 0

    def cruise_charge_time(self):
        """The time taken to charge this ship's cruise engine."""
        engine = self.engine()
        return self.engine().cruise_charge_time if engine else 0

    TYPE_ID_TO_NAME = {0: 'Light Fighter',
                       1: 'Heavy Fighter',
                       2: 'Freighter',
                       # Discovery:
                       3: 'Very Heavy Fighter',
                       4: 'Super Heavy Fighter',
                       5: 'Bomber',
                       6: 'Transport',  # more specifically;
                       7: 'Transport',  # trains
                       8: 'Transport',  # battle-transports
                       9: 'Transport',
                       10: 'Transport',  # liners.
                       11: 'Gunboat',  # gunships
                       12: 'Gunboat',
                       13: 'Cruiser',  # destroyers
                       14: 'Cruiser',
                       15: 'Cruiser',  # battlecruisers
                       16: 'Battleship',
                       17: 'Battleship',  # carriers
                       18: 'Battleship',  # flagships
                       19: 'Freighter'}  # repair ships
