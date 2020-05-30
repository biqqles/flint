"""
Copyright (C) 2016, 2017, 2020 biqqles.

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.

# todo: Equipment.
"""
from typing import Dict, List, Any, Tuple, Optional
import math

from . import Entity
from .. import paths
from ..formats import dll, utf


class Good(Entity):
    """A Good is anything that can be bought or sold. Commodities, equipment and ships are all examples of goods.
    (ABSTRACT.)"""
    item_icon: Optional[str]  # path to icon, relative to DATA
    price: int  # the default price for this good, pre market multiplier
    _market: Dict[bool, Tuple]

    def icon_path(self) -> str:
        """The absolute path to the .3db file containing this item's icon."""
        return paths.construct_path('DATA', self.item_icon or 'EQUIPMENT/MODELS/COMMODITIES/NN_ICONS/blank.3db')

    def icon(self) -> bytes:
        """This good's icon in TGA format."""
        return utf.extract(self.icon_path(), 'MIP0')

    def sold_at(self) -> Dict[str, int]:
        """A dict of bases that sell this good of the form {base_nickname: price}."""
        return dict(self._market[True])

    def bought_at(self) -> Dict[str, int]:
        """A dict of bases that buy this good of the form {base_nickname: price}."""
        return dict(self._market[False])


class Commodity(Good):
    """A Commodity is the representation of a good in tradeable/transportable form."""
    volume: float  # volume of one unit in ship's cargo bay


class Ship(Good):
    """A star ship with a cargo bay and possibly hardpoints for weapons."""
    ids_info1: int
    ids_info2: int
    ids_info3: int
    ship_class: int
    hit_pts: int
    hold_size: int
    nanobot_limit: int
    shield_battery_limit: int
    steering_torque: Tuple[float, float, float]
    angular_drag: Tuple[float, float, float]
    _hull: Dict[str, Any]
    _package: Dict[str, Any]

    def infocard(self, plain=False) -> str:
        """I have no idea why the order these are displayed in is not ascending, but anyway."""
        lookup = dll.lookup if plain else dll.lookup
        return '<p>'.join(map(lookup, (self.ids_info1, self.ids_info, self.ids_info2, self.ids_info3)))

    def type(self) -> str:
        """The name of the type (class) of this ship."""
        return self.TYPE_ID_TO_NAME.get(self.ship_class)

    def turn_rate(self) -> float:
        """Turn rate in degrees per second."""
        avg = lambda i: sum(i) / len(i)
        return math.degrees(avg(self.steering_torque) / (avg(self.angular_drag) or math.inf))

    def hardpoints(self) -> List[str]:
        """A list of this ship's hardpoints todo out of the box"""
        return self._package['addon']

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
