"""
Copyright (C) 2016, 2017, 2020 biqqles.

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""
from typing import Dict

from . import Entity
from .goods import Good, EquipmentGood
from .. import routines


class Equipment(Entity):
    # volume: float  # volume of one unit in ship's cargo bay

    def icon(self) -> bytes:
        """This equipment's icon in TGA format."""
        return self.good().icon()

    def good(self) -> Good:
        return routines.get_goods().of_type(EquipmentGood).where(equipment=self.nickname).arb

    def sold_at(self) -> Dict['Base', int]:
        """A dict of bases that sell this good of the form {base_nickname: price}. All bases buy equipment."""
        return self.good().sold_at()

    def price(self):
        return self.good().price


class Commodity(Equipment):
    """A Commodity is a tradeable piece of "equipment". Unlike other forms of Equipment, commodities can typically
    be bought and sold for variable amounts on different bases."""
    decay_per_second: int
    volume: int  # volume of one unit in ship's cargo bay

    def price_at(self):
        pass

    def highest_price(self):
        return

    def bought_at(self) -> Dict['Base', int]:
        """A dict of bases that sell this good of the form {base_nickname: price}. All bases buy equipment."""
        return self.good().bought_at()


class Mountable(Equipment):
    mass: int


class ExternalMountable(Mountable):
    hit_pts: int


class ShieldGenerator(Mountable):
    pass


class Armor(Mountable):
    """An armour upgrade."""
    hit_pts_scale: float


class Power(Mountable):
    capacity: int
    charge_rate: int
    thrust_capacity: int
    thrust_charge_rate: int


class Gun(Equipment):
    hit_pts: int
    mass: int
    power_usage: int
    muzzle_velocity: int


class Engine(Equipment):
    pass


class Thruster(Mountable):  # parent_impulse, child_impulse, volume, power_usage
    pass


class Munition(Equipment):
    pass


class RepairKit(Equipment):
    """A nano bot."""


class ShieldBattery(Equipment):
    """A shield battery."""
