"""
Copyright (C) 2016, 2017, 2020 biqqles.

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""
from typing import Tuple, List, Optional, Dict
import os
import math

from dataclassy import dataclass

from . import Entity, EntitySet
from .goods import ShipHull, ShipPackage
from .equipment import Equipment, Power, Engine
from ..formats import dll
from .. import routines, cached, paths


LOG_OF_E = math.log10(math.e)  # used to approximate angular acceleration curve


class Ship(Entity):
    """A starship with a cargo bay and possibly hardpoints for weapons."""
    ids_info1: Optional[int] = None  # ship description (ids_info stores statistics)
    ids_info2: Optional[int] = None  # extra stat names list
    ids_info3: Optional[int] = None  # extra stat values list
    ship_class: int = 0
    mission_property: Optional[str] = None
    hit_pts: int
    hold_size: int
    mass: int
    linear_drag: int
    nanobot_limit: int = 0
    shield_battery_limit: int = 0
    steering_torque: Tuple[float, float, float]
    angular_drag: Tuple[float, float, float]
    rotation_inertia: Tuple[float, float, float]
    hp_type: List[Tuple[str, ...]] = []

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
            return self.package().cost()
        except AttributeError:
            return 0

    def icon(self) -> bytes:
        """This ship's icon."""
        return self.hull().icon()

    def infocard(self, markup='html') -> str:
        """I have no idea why the order these are displayed in is not ascending, but anyway."""
        lookup = self._markup_formats[markup]
        return '<p>'.join(map(lookup, (self.ids_info1, self.ids_info)))

    def type(self) -> str:
        """The name of the type (class) of this ship."""
        return self._ship_classes()[self.ship_class]

    def turn_rate(self) -> float:
        """The maximum turn rate (i.e. angular speed) of this ship, in rad/s."""
        return self.steering_torque[0] / self.angular_drag[0]

    def angular_distance_in_time(self, time=1) -> float:
        """The angular displacement in radians from rest to `time` (in seconds).
        TODO: Currently only an approximation."""
        return self.turn_rate() / self.response()

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

    def thrust_speed(self, thrust_force = 72000) -> float:
        """The maximum thrust speed of this ship, in m/s"""
        engine = self.engine()
        force = thrust_force + engine.max_force if engine else thrust_force
        linear_drag = self.linear_drag + engine.linear_drag if engine else self.linear_drag
        return force / linear_drag

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

    def hardpoints(self) -> Dict[str, List['Hardpoint']]:
        """A mapping of this ship's hardpoints of the form
        {hardpoint nickname -> union of weapon classes that can be mounted on this hardpoint}."""
        result = {}
        for hp_class, *hardpoints in self.hp_type:
            for hp in hardpoints:
                result.setdefault(hp, []).append(Hardpoint(hp_class))
        return result

    @staticmethod
    @cached
    def _ship_classes() -> List[str]:
        """Construct an array of ship type codes to their display names."""
        # vanilla classes: Light Fighter - VHF
        result = list(map(dll.lookup, range(923, 927)))

        # further classes can be provided by mods using adoxa's shipclass plugin
        ship_class = paths.construct_path('EXE/shipclass.dll')
        if os.path.exists(ship_class):
            result.extend(dll.parse(ship_class, 0).values())

        return result


@dataclass
class Hardpoint:
    """A ship hardpoint on which a piece of equipment can be mounted.
    Not an Entity and not exported."""
    nickname: str

    def name(self) -> str:
        """Hardpoint names are found in hardcoded ranges. TODO: engine classes provided by engclass.dll."""
        return dll.lookup(self.NAME_IDS.get(self.nickname)) or self.nickname

    def category(self) -> str:
        """The hardpoint's category is the tab the game displays it under.
        These rules are also hardcoded."""
        if any(n in self.nickname for n in ('gun', 'torpedo', 'mine', 'turret')):
            return 'weapons'
        if any(n in self.nickname for n in ('shield', 'thruster')):
            return 'external'
        return 'internal'

    # add singletons
    NAME_IDS = {
        'hp_gun': 948,
        'hpmine01': 1522,
        'hp_thruster': 1520,
        'hp_torpedo': 1521,  # CD
        'hp_torpedo_special_1': 1741,  # fighter torpedo
        'hp_torpedo_special_2': 1742,  # bomber torpedo
        'hp_mine_dropper': 1522,
        'hpcm01': 1523,
        'hp_countermeasure_dropper': 1523,
        'hp_fighter_shield_generator': 1517,
        'hp_elite_shield_generator': 1518,
    }

    # add ranges
    ten = list(range(10))
    NAME_IDS.update({f'hp_fighter_shield_special_{i + 1}': i + 1700 for i in ten})
    NAME_IDS.update({f'hp_elite_shield_special_{i + 1}': i + 1711 for i in ten})
    NAME_IDS.update({f'hp_freighter_shield_special_{i + 1}': i + 1721 for i in ten})
    NAME_IDS.update({f'hp_gun_special_{i + 1}': i + 946 for i in ten})
    NAME_IDS.update({f'hp_turret_special_{i + 1}': i + 1731 for i in ten})
    del ten
