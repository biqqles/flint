"""
Copyright (C) 2016, 2017, 2020 biqqles.

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""
from typing import Dict, List, Tuple, Optional, cast

from dataclassy import Internal

from . import Entity, EntitySet
from .. import paths
from ..formats import utf


class Good(Entity):
    """A Good is the physical (transferable) representation of something that can be bought or sold. A good maps the
    abstract definition of commodities, equipment and ships to something that is tradeable."""
    ids_info = None
    ids_name = None
    item_icon: Optional[str] = None  # path to icon, relative to DATA
    price: int  # the default price for this good, pre market multiplier

    def icon_path(self) -> str:
        """The absolute path to the .3db file containing this item's icon."""
        return paths.construct_path('DATA', self.item_icon or self.DEFAULT_ICON)

    def icon(self) -> bytes:
        """This good's icon in TGA format."""
        return utf.extract(self.icon_path(), 'MIP0')

    def market(self) -> Dict[bool, Dict['Base', int]]:
        """The market for this Good, i.e. the Bases it is bought and sold on and their prices."""
        return routines.get_markets()[self]

    def sold_at(self) -> Dict['Base', int]:
        """A dict of bases that sell this good of the form {base_nickname: price}."""
        return self.market()[True]

    def bought_at(self) -> Dict['Base', int]:
        """A dict of bases that buy this good of the form {base_nickname: price}."""
        return {**self.market()[False], **self.sold_at()}

    def price_at(self, base: 'Base') -> int:
        return self.bought_at()[base]

    DEFAULT_ICON = 'EQUIPMENT/MODELS/COMMODITIES/NN_ICONS/blank.3db'


class EquipmentGood(Good):
    """The good of a piece of equipment."""
    equipment: str  # nickname of the good this equipment represents.
    combinable: bool

    def equipment_(self) -> 'Equipment':
        """The Equipment entity this good refers to."""
        return routines.get_equipment().get(self.equipment)


class CommodityGood(EquipmentGood):
    """The good of a commodity. This is the place where the distinction between equipment and commodities is made."""
    good_sell_price: float
    bad_buy_price: float
    bad_sell_price: float
    good_buy_price: float
    shop_archetype: str

    def commodity(self) -> 'Commodity':
        """The Commodity entity this good refers to."""
        return cast(Commodity, self.equipment_())


class ShipHull(Good):
    """The hull of a ship, meaning a ship with no equipment mounted."""
    ship: str  # nickname of a Ship

    def ship_(self) -> 'Ship':
        """The Ship that uses this hull."""
        return routines.get_ships().get(self.ship)


class ShipPackage(Good):
    """A ship "package" is the form a ship is buyable in. As a kind of "composite" good, it does not have an inherent
    `price` attribute, unlike other goods. Its cost is the sum of the hull and all "addons", which are the equipment
    mounted on the ship when purchased."""
    price = 0
    hull: str  # nickname of a ShipHull
    addon: Internal[List[Tuple[str, str, int]]]  # tuple of the form (equipment nickname, hardpoint nickname, ?)

    def hull_(self) -> ShipHull:
        """The ShipHull entity of this package's hull."""
        return routines.get_goods()[self.hull]

    def ship(self) -> 'Ship':
        """The Ship this package represents."""
        return self.hull_().ship_()

    def cost(self) -> int:
        """The cost of this ship package when bought. Note that this is distinct from Good's _price_, which ShipPackage
        lacks. Instead a ship's cost at the vendor is the sum of the prices of its hull and default equipment
        ("addons")."""
        return self.hull_().price + sum(e.price() for e in self.equipment())

    def equipment(self) -> EntitySet['Equipment']:
        """The set of equipment included in this package."""
        equipment = routines.get_equipment()
        return EntitySet(equipment[n] for n, *_ in self.addon if n in equipment)


from .. import routines
from .equipment import Equipment, Commodity
