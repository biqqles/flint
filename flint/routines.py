"""
Copyright (C) 2016, 2017, 2020 biqqles.

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.

This file contains routines for parsing specific sets of information
from the game files. All exported functions return EntitySets.
"""
from typing import Dict, List, Tuple
from collections import defaultdict

from . import paths
from .dynamic import cached
from .formats import ini
from .entities import EntitySet
from .entities import Commodity, Ship
from .entities import Base, System, Faction
from .entities import Solar, Object, Jump, BaseSolar, Star, Planet, PlanetaryBase, TradeLaneRing, Wreck, Zone
from .maps import PosVector, RotVector


@cached
def get_systems() -> EntitySet[System]:
    """All systems defined in the game files."""
    systems = ini.parse(paths.inis['universe'])['system']

    return EntitySet(System(**s, ids_name=s.pop('strid_name')) for s in systems if 'file' in s)


@cached
def get_bases() -> EntitySet[Base]:
    """All bases defined in the game files."""
    bases = ini.parse(paths.inis['universe'])['base']

    return EntitySet(Base(**b, ids_name=b.pop('strid_name'), ids_info=None, _market=_get_markets()[b['nickname']])
                     for b in bases)


@cached
def get_commodities() -> EntitySet[Commodity]:
    """All commodities defined in the game files."""
    path = paths.construct_path('DATA/EQUIPMENT/select_equip.ini')
    commodities = ini.parse(path)['commodity']

    result = []

    for c in commodities:
        good = _get_goods()[c['nickname']]
        market = _get_markets()[c['nickname']]
        result.append(Commodity(**c, item_icon=good.get('item_icon'), price=good['price'], _market=market))

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
    result: List[Ship] = []

    for s in stats:
        try:
            hull = _get_goods()[s['nickname']]
            package = _get_goods()[hull['nickname']]
            market = _get_markets()[package['nickname']]
            ship = Ship(**s, item_icon=hull['item_icon'], price=hull['price'], _market=market, _hull=hull,
                        _package=package)
        except (KeyError, TypeError):
            # ship not sold anywhere or lacking infocards todo: how should we handle this?
            continue
        result.append(ship)

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
def _get_goods() -> Dict[str, Dict]:
    # This is an internal method. A good is anything that can be bought or sold.
    # get_commodities, get_ships and get_equipment link goods up to objects
    goods = ini.parse(paths.inis['goods'])['good']  # todo: equipment too

    result = {}
    for g in goods:
        # fold ship components into each other (this makes loading ships easier)
        if g['category'] == 'shiphull':
            key = 'ship'
        elif g['category'] == 'ship':
            key = 'hull'
        else:
            key = 'nickname'
        result[g[key]] = g
    return result


@cached
def _get_markets() -> Dict[str, Dict[bool, List[Tuple[str, int]]]]:
    """Result is of the form base/good nickname -> {sold -> (good/base nickname, price at base}}"""
    market = ini.parse(paths.inis['markets'], fold_values=False)['basegood']
    goods = _get_goods()
    result = defaultdict(lambda: {True: [], False: []})
    for b in market:
        base = b['base'][0]
        base_market = b['marketgood']
        for good, min_rank, min_rep, min_stock, max_stock, depreciate, multiplier, *_ in base_market:
            if not multiplier:
                continue
            try:
                sold = not (min_stock == 0 or max_stock == 0)
                price_at_base = int(round(goods[good]['price'] * multiplier))
            except KeyError:
                continue  # this is expected for ship packages, which do not appear in market sections

            result[base][sold].append((good, price_at_base))
            result[good][sold].append((base, price_at_base))
    return result
