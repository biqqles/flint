"""
Copyright (C) 2016, 2017, 2020 biqqles.

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""
from typing import Tuple, List
import math
from statistics import mean

from . import Entity
from .goods import ShipHull, ShipPackage
from ..formats import dll
from .. import routines


class Ship(Entity):
    """A starship with a cargo bay and possibly hardpoints for weapons."""
    ids_info1: int
    ids_info2: int
    ids_info3: int
    ship_class: int
    hit_pts: int
    hold_size: int
    nanobot_limit: int = 0
    shield_battery_limit: int = 0
    steering_torque: Tuple[float, float, float]
    angular_drag: Tuple[float, float, float]

    def hull(self) -> ShipHull:
        """This ship's hull entity."""
        return routines.get_goods().of_type(ShipHull).where(ship=self.nickname).first

    def package(self) -> ShipPackage:
        """This ship's package entity."""
        return routines.get_goods().of_type(ShipPackage).where(hull=self.hull().nickname).first

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
        return '<p>'.join(map(lookup, (self.ids_info1, self.ids_info, self.ids_info2, self.ids_info3)))

    def type(self) -> str:
        """The name of the type (class) of this ship."""
        return self.TYPE_ID_TO_NAME.get(self.ship_class)

    def turn_rate(self) -> float:
        """Turn rate in degrees per second."""
        return math.degrees(mean(self.steering_torque) / (mean(self.angular_drag) or math.inf))

    def hardpoints(self) -> List[str]:
        """A list of this ship's hardpoints todo out of the box"""
        return self.package().addon

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
