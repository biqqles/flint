"""
Copyright (C) 2016, 2017, 2020 biqqles.

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.

This file contains routines for parsing specific sets of information
from the game files. All exported functions return EntitySets.
"""
from typing import Dict, Union
from collections import defaultdict
import warnings

from . import paths
from . import cached
from .formats import ini
from .maps import PosVector

from .entities import EntitySet
from .entities import Good, EquipmentGood, CommodityGood, ShipHull, ShipPackage
from .entities import Commodity, Equipment, Armor, ShieldGenerator, Thruster, Gun, Engine, Power, ShieldBattery, \
    CounterMeasure, CounterMeasureDropper, Scanner, Tractor, CargoPod, CloakingDevice, RepairKit, Mine, MineDropper, \
    Munition, Explosion, Motor
from .entities import Ship
from .entities import Base, System, Faction
from .entities import Solar, Object, Jump, BaseSolar, Star, Planet, PlanetaryBase, TradeLaneRing, Wreck, Zone
from . import entities


@cached
def get_systems() -> EntitySet[System]:
    """All systems defined in the game files."""
    systems = ini.sections(paths.inis['universe'])['system']
    return EntitySet(System(**s, ids_name=s.pop('strid_name')) for s in systems if 'file' in s)


@cached
def get_bases() -> EntitySet[Base]:
    """All bases defined in the game files."""
    bases = ini.sections(paths.inis['universe'])['base']
    return EntitySet(Base(**b, ids_name=b['strid_name']) for b in bases if 'strid_name' in b)


@cached
def get_factions() -> EntitySet[Faction]:
    """All groups (i.e. factions) defined in the game files."""
    groups = ini.sections(paths.inis['initial_world'])['group']
    return EntitySet(Faction(**g) for g in groups)


@cached
def get_goods() -> EntitySet[Good]:
    """All goods defined in the game files."""
    goods = ini.sections(paths.inis['goods'])['good']
    result = []

    for g in goods:
        if g['category'] == 'ship':
            result.append(ShipPackage(**g))
        elif g['category'] == 'equipment':
            result.append(EquipmentGood(**g))
        elif g['category'] == 'commodity':
            result.append(CommodityGood(**g))
        elif g['category'] == 'shiphull':
            result.append(ShipHull(**g))
        else:
            result.append(Good(**g))
    return EntitySet(result)


@cached
def get_equipment() -> EntitySet[Equipment]:
    """All equipment defined in the game files."""
    section_name_to_type = {name.lower(): globals()[name] for name in dir(entities) if name in globals()}
    excluded_sections = {'light', 'tradelane', 'internalfx', 'attachedfx', 'shield', 'lod', 'lootcrate'}

    equipment = ini.parse(paths.inis['equipment'])

    def generate_entities():
        """Convert equipment sections to entities."""
        for section, contents in equipment:
            if section in excluded_sections:
                continue  # not really entities, see docstring for equipment.py
            if section in section_name_to_type:
                try:
                    yield section_name_to_type[section](**contents)
                except TypeError as e:
                    warnings.warn(f'Failed to initialise equipment of type {section!r} and nickname '
                                  f'{contents.get("nickname")!r}: {e.args[0]}')
            else:
                warnings.warn(f'Unknown equipment type {section!r} - ignoring')

    return EntitySet(generate_entities())


@cached
def get_commodities() -> EntitySet[Commodity]:
    """All commodities defined in the game files. Commodities are actually a type of equipment, so this function
    is for convenience's sake."""
    return get_equipment().of_type(Commodity)


@cached
def get_ships() -> EntitySet[Ship]:
    """All ships defined in the game files."""
    ships = ini.sections(paths.inis['ships'])['ship']
    result = []

    for s in ships:
        if 'ids_info3' in s:
            result.append(Ship(**s))

    return EntitySet(result)


@cached
def get_system_contents(system: System) -> EntitySet[Solar]:
    """All solars (objects and zones) in a given system."""
    result = []
    contents = ini.parse(system.definition_path())

    # categorise objects based on their keys
    for solar_type, attributes in contents:
        if 'ids_name' not in attributes:
            continue
        attributes['_system'] = system
        attributes['pos'] = PosVector(*attributes['pos'])

        if solar_type == 'object':
            o = attributes
            keys = o.keys()
            if {'base', 'reputation', 'space_costume'} <= keys:
                result.append(BaseSolar(**o))
            elif 'goto' in keys:
                result.append(Jump(**o))
            elif 'prev_ring' in keys or 'next_ring' in keys:
                result.append(TradeLaneRing(**o))
            elif 'loadout' in keys and 'reputation' not in keys:
                result.append(Wreck(**o))
            elif 'star' in keys:
                result.append(Star(**o))
            elif 'spin' in keys:
                result.append(PlanetaryBase(**o) if 'base' in keys else Planet(**o))
            else:
                result.append(Object(**o))

        elif solar_type == 'zone':
            z = attributes
            result.append(Zone(**z))

    return EntitySet(result)


@cached
def get_markets() -> Dict[Union[Base, Good], Dict[bool, Dict[Union[Good, Base], int]]]:
    """Market (i.e. economy) data for the universe. Result is of the form
    {base/good nickname -> {whether sold -> (good/base entity, price at base}}."""
    market = ini.sections(paths.inis['markets'], fold_values=False)['basegood']

    goods = get_goods()
    bases = get_bases()

    result = defaultdict(lambda: {True: {}, False: {}})
    for b in market:
        try:
            base = b['base'][0]
            base_entity = bases[base]
        except IndexError:
            warnings.warn('BaseGood has no base')
            continue

        for good, min_rank, min_rep, min_stock, max_stock, depreciate, multiplier, *_ in b['marketgood']:
            if not multiplier:
                continue

            try:
                good_entity = goods[good]
            except KeyError:
                warnings.warn(f'BaseGood for base {base!r} refers to undefined good: {good!r}')
                continue
            sold = not (min_stock == 0 or max_stock == 0)
            price_at_base = int(round(good_entity.price * multiplier))

            result[base_entity][sold][good_entity] = price_at_base
            result[good_entity][sold][base_entity] = price_at_base
    return result
