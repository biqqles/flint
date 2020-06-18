"""
Copyright (C) 2016, 2017, 2020 biqqles.

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.

This file contains routines for parsing specific sets of information
from the game files. All exported functions return EntitySets.
"""
from typing import Dict, List, Tuple, Union
from collections import defaultdict

from . import paths
from .dynamic import cached
from .formats import ini
from .entities import EntitySet
from .entities import Good, EquipmentGood, CommodityGood, ShipHull, ShipPackage
from .entities import Commodity, Equipment, Armor, ShieldGenerator, Thruster, ShipPackage, Gun
from .entities import Ship
from .entities import Base, System, Faction
from .entities import Solar, Object, Jump, BaseSolar, Star, Planet, PlanetaryBase, TradeLaneRing, Wreck, Zone
from .maps import PosVector


@cached
def get_systems() -> EntitySet[System]:
    """All systems defined in the game files."""
    systems = ini.parse(paths.inis['universe'])['system']
    return EntitySet(System(**s, ids_name=s.pop('strid_name')) for s in systems if 'file' in s)


@cached
def get_bases() -> EntitySet[Base]:
    """All bases defined in the game files."""
    bases = ini.parse(paths.inis['universe'])['base']
    return EntitySet(Base(**b, ids_name=b.pop('strid_name'), ids_info=None) for b in bases)


@cached
def get_commodities() -> EntitySet[Commodity]:
    """All commodities defined in the game files. Commodities are actually a type of equipment, so this function
    is for convenience's sake."""
    return get_equipment().of_type(Commodity)


@cached
def get_goods() -> EntitySet[Good]:
    """All goods defined in the game files."""
    goods = ini.parse(paths.inis['goods'])['good']
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
    equipment = ini.parse(paths.inis['equipment'])
    result = []

    print(sorted(list(equipment.keys())))

    for c in equipment['commodity']:
        result.append(Commodity(**c))
    for t in equipment['thruster']:
        result.append(Thruster(**t))
    for g in equipment['gun']:
        result.append(Gun(**g))
    return EntitySet(result)


@cached
def get_factions() -> EntitySet[Faction]:
    """All groups (i.e. factions) defined in the game files."""
    groups = ini.parse(paths.inis['initial_world'])['group']
    return EntitySet(Faction(**g) for g in groups)


@cached
def get_ships() -> EntitySet[Ship]:
    """All ships defined in the game files."""
    stats = ini.parse(paths.inis['ships'])['ship']
    result = []

    for s in stats:
        if 'ids_info3' in s:
            result.append(Ship(**s))

    return EntitySet(result)


@cached
def get_system_contents(system: System) -> EntitySet[Solar]:
    """All solars (objects and zones) in a given system."""
    result = []
    contents = ini.parse(system.definition_path())

    # categorise objects based on their keys
    def modify_solar(solar: Dict):
        """Common dict modifications for all solar types."""
        solar['_system'] = system
        solar['pos'] = PosVector(*o['pos'])
        solar.setdefault('ids_info', None)  # not everything that ought to have ids_info does...
        return solar

    for o in contents.get('object', []):
        if 'ids_name' not in o:
            continue
        o = modify_solar(o)
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

    for z in contents.get('zone', []):
        z = modify_solar(z)
        if 'ids_name' in z.keys():
            result.append(Zone(**z))

    return EntitySet(result)


@cached
def get_markets() -> Dict[Union[Base, Good], Dict[bool, Dict[Union[Good, Base], int]]]:
    """Market (i.e. economy) data for the universe. Result is of the form
    {base/good nickname -> {whether sold -> (good/base entity, price at base}}."""
    market = ini.parse(paths.inis['markets'], fold_values=False)['basegood']

    goods = get_goods()
    bases = get_bases()

    result = defaultdict(lambda: {True: {}, False: {}})
    for b in market:
        base_entity = bases[b['base'][0]]

        for good, min_rank, min_rep, min_stock, max_stock, depreciate, multiplier, *_ in b['marketgood']:
            if not multiplier:
                continue

            good_entity = goods[good]
            try:
                sold = not (min_stock == 0 or max_stock == 0)
                price_at_base = int(round(goods[good].price * multiplier))
            except KeyError:
                continue  # this is expected for ship packages, which do not appear in market sections

            result[base_entity][sold][good_entity] = price_at_base
            result[good_entity][sold][base_entity] = price_at_base
    return result
