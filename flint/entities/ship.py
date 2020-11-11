"""
Copyright (C) 2016, 2017, 2020 biqqles.

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""
from typing import Tuple, List, Optional
import math

from . import Entity, EntitySet
from .goods import ShipHull, ShipPackage
from .equipment import Equipment, Power, Engine
from ..formats import dll
from .. import routines


LOG_OF_E = math.log10(math.e)  # used to approximate angular acceleration curve


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

    def type(self) -> Optional[str]:
        """The name of the type (class) of this ship."""
        return self.TYPE_ID_TO_NAME.get(self.ship_class)

    def turn_rate(self) -> float:
        """The maximum turn rate (i.e. angular speed) of this ship, in rad/s."""
        return self.steering_torque[0] / self.angular_drag[0]

    def angular_distance_in_time(self, time=1) -> float:
        """The angular displacement in radians from rest to `time` (in seconds).
        TODO: Currently only an approximation. I believe this formula is correct but there has to be a more accurate
               way to calculate acceleration."""
        return 0.5 * (self.turn_rate() / self.response()) * time**2

    def response(self) -> float:
        """The "response time" is defined as the time to reach 90% maximum angular speed (in seconds).
        Thanks to Haste for this formula."""
        return self.rotation_inertia[0] / (self.angular_drag[0] * LOG_OF_E)

    def equipment(self) -> EntitySet[Equipment]:
        """The set of this ship package's equipment upon purchase."""
        package = self.package()
        return package.equipment() if package else EntitySet([])

    def power_core(self) -> Optional[Power]:
        """The Power entity for this ship."""
        return self.equipment().of_type(Power).first

    def engine(self) -> Optional[Engine]:
        """The Power entity for this ship."""
        return self.equipment().of_type(Engine).first

    def impulse_speed(self) -> float:
        """The maximum forward impulse (non-cruise) speed of this ship (m/s)."""
        engine = self.engine()
        return self.linear_speed(engine.max_force) if engine else 0

    def reverse_speed(self) -> float:
        """The maximum reverse speed of this ship (m/s)."""
        engine = self.engine()
        return self.impulse_speed() * engine.reverse_fraction if engine else 0

    def linear_speed(self, force: float) -> float:
        """The maximum speed of this ship for a given force, in m/s."""
        return force / self.total_linear_drag()

    def total_linear_drag(self) -> float:
        """The total linear resistive force for this ship and engine, in N (?)."""
        engine = self.engine()
        try:
            return engine.linear_drag + self.linear_drag if engine else self.linear_drag
        except TypeError:
            return 1

    def cruise_charge_time(self):
        """The time taken to charge this ship's cruise engine, in seconds."""
        engine = self.engine()
        return engine.cruise_charge_time if engine else 0

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
