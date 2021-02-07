"""
Copyright (C) 2016, 2017, 2020 biqqles.

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.

This file defines entities for equipment. 'Equipment' includes anything
which can be mounted on a ship or carried in its hold.

There are also several non-entity section types that appear in equipment
files. These include Lod, TradeLane, InternalFX, AttachedFX, Explosion,
Light, Motor, LootCrate, and Shield. Currently these are excluded as
they do not exactly fit flint's entity model, and partly for the sake
of simplicity in the first incarnation of equipment parsing.

Because of the sheer number of classes in this file, apart from abstract
classes they currently have a 1-1 mapping with INI section types to
simplify and optimise instantiation logic. So, for example, subtypes of
Gun could be Missile and Turret, but instead you should determine if a
Gun instance is one of these by checking its attributes.
"""
from typing import Dict, Optional, Tuple, cast
import math

from . import Entity
from .. import routines


class Equipment(Entity):
    """Abstract class for something which can be mounted on a ship or carried in its hold."""
    lootable: bool = False

    def icon(self) -> bytes:
        """This equipment's icon in TGA format."""
        return self.good().icon()

    def good(self) -> Optional['Good']:
        """The good entity for this piece of equipment."""
        return routines.get_goods().of_type(EquipmentGood).unique(equipment=self.nickname)

    def sold_at(self) -> Dict['Base', int]:
        """A dict of bases that sell this good of the form {base: price}. All bases buy equipment."""
        return self.good().sold_at() if self.good() else {}

    def price(self) -> int:
        """The default price of this equipment."""
        return self.good().price if self.good() else 0

    def is_valid(self) -> bool:
        """Whether the equipment is valid, i.e. it defines a good. Note that some specialised equipment subtypes
        do not have goods, rendering this method meaningless for them."""
        return self.good() is not None


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
    refire_delay: float
    projectile_archetype: str

    def refire(self) -> float:
        """The refire value as displayed in-game, which is the reciprocal of refire_delay."""
        return 1 / self.refire_delay

    def hull_damage(self) -> float:
        """Hull damage dealt per shot."""
        raise NotImplementedError

    def shield_damage(self) -> float:
        """Shield damage dealt per shot."""
        raise NotImplementedError

    def projectile(self) -> 'Projectile':
        """The Projectile fired or dropped by this weapon."""
        return routines.get_equipment().get(self.projectile_archetype)


class Gun(Weapon):
    """A gun that goes 'pew'. Not much to be said."""
    power_usage: float
    muzzle_velocity: int
    projectile_archetype: str
    hp_gun_type: Optional[str] = None  # NPC guns lack this field
    dispersion_angle: float = 0.0
    dry_fire_sound: Optional[str] = None  # only missiles (and mine droppers, but they're a different class) have this
    auto_turret: bool  # only turrets have this

    def munition(self) -> Optional['Munition']:
        """The Munition fired by this weapon."""
        return cast(Munition, self.projectile())

    def hull_damage(self) -> float:
        """Hull damage dealt per shot."""
        return self.munition().hull_damage_()

    def shield_damage(self) -> float:
        """Shield damage dealt per shot."""
        return self.munition().energy_damage_()

    def hull_dps(self) -> float:
        """Hull damage dealt per second."""
        return self.refire() * self.munition().hull_damage

    def shield_dps(self) -> float:
        """Shield damage dealt per second."""
        return self.refire() * self.munition().energy_damage

    def energy_per_second(self) -> float:
        """Energy consumption per second (i.e. power).."""
        return self.refire() * self.power_usage

    def efficiency(self) -> float:
        """Energy consumption per second (i.e. power).."""
        return ((self.hull_damage() + self.shield_damage()) / self.power_usage) if self.power_usage else 0.0

    def technology(self) -> Optional[str]:
        """The technology of this gun. Null for non-energy (e.g. kinetic) guns."""
        return self.munition().weapon_type

    def range(self) -> int:
        """The range this weapon can shoot to."""
        return int(self.muzzle_velocity * self.munition().lifetime)

    def is_valid(self) -> bool:
        """Whether the gun is valid, i.e. it defines a good and a munition."""
        return super().is_valid() and (self.munition() is not None)

    def is_missile(self) -> bool:
        """Whether the gun is a missile/torpedo launcher. Another, much slower, way to test this would be to check
        if the gun's munition has a "motor" field."""
        return bool(self.dry_fire_sound) or self.munition().cruise_disruptor is not None or 'Torpedo' in self.name()

    def is_turret(self) -> bool:
        """Whether the gun is a turret."""
        return self.auto_turret or (self.hp_gun_type and 'turret' in self.hp_gun_type) or 'Turret' in self.name()


class MineDropper(Weapon):
    """A dispenser for mines."""

    def mine(self) -> Optional['Mine']:
        """The Mine dropped by this weapon."""
        return cast(Mine, self.projectile())

    def hull_damage(self) -> float:
        """The hull damage inflicted on contact with this dropper's mine."""
        return self.mine().explosion().hull_damage

    def shield_damage(self) -> float:
        """The shield damage inflicted on contact with this dropper's mine."""
        return self.mine().explosion().energy_damage


class CloakingDevice(External):
    """A cloaking device. Used in cutscenes in the campaign as well as on servers with cloaking devices enabled through
    FLHook."""


class Projectile(Equipment):
    """Abstract. A projectile fired or dropped by a Weapon."""
    lifetime: float  # time in seconds that the projectile lingers in space before despawning


class Mine(Projectile):
    """An explosive mine that can be dropped into space."""
    explosion_arch: str  # nickname of Explosion
    seek_dist: int
    top_speed: int
    acceleration: int
    ammo_limit: int

    def explosion(self) -> Optional['Explosion']:
        """The Explosion triggered by this mine."""
        return routines.get_equipment().get(self.explosion_arch)


class Munition(Projectile):
    """A projectile fired by a Weapon."""
    hp_type: str
    hull_damage: int = 0
    energy_damage: int = 0
    requires_ammo: bool = True  # todo: not sure about this default
    weapon_type: Optional[str] = None  # present only for energy weapons
    ammo_limit: int = math.inf
    explosion_arch: Optional[str] = None  # nickname of Explosion
    cruise_disruptor: Optional[bool] = None  # only set for missiles
    motor: Optional[str] = None  # only set for missiles
    seeker: Optional[str] = None

    def explosion(self) -> Optional['Explosion']:
        """The Explosion triggered by this munition."""
        return routines.get_equipment().get(self.explosion_arch) if self.explosion_arch else None

    def hull_damage_(self) -> int:
        """The hull damage inflicted by this munition, taking into consideration its explosion."""
        try:
            return self.hull_damage or self.explosion().hull_damage
        except AttributeError:
            return 0

    def energy_damage_(self) -> int:
        """The shield damage inflicted by this munition, taking into consideration its explosion."""
        try:
            return self.energy_damage or self.explosion().energy_damage
        except AttributeError:
            return 0

    def motor_(self) -> Optional['Motor']:
        """This Munition's Motor."""
        return routines.get_equipment().get(self.motor) if self.motor else None


class Motor(Projectile):
    """A missile motor."""
    accel: int
    delay: int


class Explosion(Projectile):
    """A very strange thing to call equipment, whatever way you look at it, yet defined in weapon_equip."""
    lifetime: Tuple[int, int]
    radius: int
    hull_damage: int
    energy_damage: int
    strength: int


# equipment typically defined in st_equip.ini
class Thruster(External):
    """A thruster that provides supplementary acceleration and velocity to the main engine."""
    power_usage: float


class ShieldGenerator(External):
    """A piece of equipment that generates a shield bubble around a ship which absorbs damage from weapon fire."""
    shield_type: str = ''  # the shield's technology type
    max_capacity: float
    explosion_resistance: float = 0.0


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
    range: int
    diversion_pctg: float
    ammo_limit: int = math.inf  # typically only NPC CMs have unlimited ammo

    def effectiveness(self) -> float:
        """The probability this countermeasure will defeat an incoming missile."""
        return self.diversion_pctg / 100


class CounterMeasureDropper(Weapon):
    """A countermeasure dispenser."""

    def countermeasure(self) -> Optional['CounterMeasure']:
        """The CounterMeasure launched by this dropper."""
        return routines.get_equipment().get(self.projectile_archetype)


class RepairKit(Equipment):
    """A nanobot that can be used to repair hull damage."""


class ShieldBattery(Equipment):
    """A shield battery, used to recharge shields instantaneously."""


# equipment typically defined in engine_equip.ini
class Engine(Mountable):
    """A reaction engine that must be mounted to a ship to provide propulsion."""
    cruise_charge_time: int
    reverse_fraction: float
    linear_drag: float
    max_force: float
    

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

    def bought_at(self) -> Dict['Base', int]:
        """A dict of bases that buy this commodity of the form {base: price}."""
        return self.good().bought_at()


from .goods import Good, EquipmentGood
