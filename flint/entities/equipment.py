"""
Copyright (C) 2016, 2017, 2020 biqqles.

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.

This file defines entities for equipment. 'Equipment' includes anything
which can be mounted on a ship or carried in its hold.

There are also several non-entity section types that appear in equipment
files. These include Lod, TradeLane, InternalFX, AttachedFX, Explosion,
Light, Motor, LootCrate, Munition and Shield. Currently these are excluded
as they do not exactly fit flint's entity model, and partly for the sake
of simplicity in the first incarnation of equipment parsing.
"""
from typing import Dict

from . import Entity
from .goods import Good, EquipmentGood
from .. import routines


class Equipment(Entity):
    """Something which can be mounted on a ship or carried in its hold."""
    lootable: bool = False

    def icon(self) -> bytes:
        """This equipment's icon in TGA format."""
        return self.good().icon()

    def good(self) -> Good:
        """The good entity for this piece of equipment."""
        return routines.get_goods().of_type(EquipmentGood).where(equipment=self.nickname).first

    def sold_at(self) -> Dict['Base', int]:
        """A dict of bases that sell this good of the form {base: price}. All bases buy equipment."""
        return self.good().sold_at()

    def price(self) -> int:
        """The default price of this equipment."""
        return self.good().price


class Mountable(Equipment):
    """Abstract class for a piece of equipment that is mountable."""
    volume: int = 0  # volume of one unit in ship's cargo bay


class External(Mountable):
    """Abstract class for a piece of mountable equipment that is externally mounted, and therefore typically
    destructible."""
    hit_pts: int


# equipment typically defined in weapon_equip.ini
class Weapon(External):
    """Abstract class for a piece of external equipment that is a weapon."""


class Gun(Weapon):
    """A gun that goes 'pew'. Not much to be said."""
    power_usage: float
    muzzle_velocity: int
    refire_delay: float


class Mine(Equipment):
    """A mine that can be dropped into space."""


class MineDropper(Weapon):
    """A dispenser for mines."""


class CloakingDevice(Weapon):
    """A cloaking device. Used in cutscenes in the campaign as well as on servers with cloaking devices enabled through
    FLHook."""


# equipment typically defined in st_equip.ini
class Thruster(External):
    """A thruster that provides supplementary acceleration and velocity to the main engine."""
    power_usage: float


class ShieldGenerator(External):
    """A piece of equipment that generates a shield bubble around a ship which absorbs damage from weapon fire."""
    power_usage: float
    shield_type: str
    max_capacity: float
    explosion_resistance: float


# equipment typically defined in misc_equip.ini
class Power(Mountable):
    """A ship's power plant."""
    capacity: int
    charge_rate: int


class Tractor(Mountable):
    """A tractor beam generator."""
    max_length: int  # range of beam in M


class Scanner(Mountable):
    """A scanner, akin to a radar transmitter/receiver."""
    range: int  # maximum contact acquisition range in M
    cargo_scan_range: int  # maximum cargo scan range in M


class CounterMeasure(Equipment):
    """A countermeasure that can be deployed against seeking missiles."""
    lifetime: float


class CounterMeasureDropper(Weapon):
    """A countermeasure dispenser."""


class RepairKit(Equipment):
    """A nanobot that can be used to repair hull damage."""


class ShieldBattery(Equipment):
    """A shield battery, used to recharge shields instantaneously."""


# equipment typically defined in engine_equip.ini
class Engine(Mountable):
    """A reaction engine that must be mounted to a ship to provide propulsion."""


# equipment typically defined in select_equip.ini
class Armor(Mountable):
    """An armour upgrade."""
    hit_pts_scale: float  # multiplier applied to ship hull hit points when mounted


class CargoPod(Mountable):
    """A cargo pod. These can absorb damage but this is their only function in the final game."""


class Commodity(Equipment):
    """A Commodity is a tradeable piece of "equipment". Unlike other forms of equipment, commodities can typically
    be bought and sold for variable amounts on different bases."""
    decay_per_second: int
    volume: int  # volume of one unit in ship's cargo bay

    def price_at(self):
        pass

    def highest_price(self):
        return

    def sold_at(self) -> Dict['Base', int]:
        """A dict of bases that sell this commodity of the form {base: price}."""
        return self.good().bought_at()
