"""
Copyright (C) 2016, 2017, 2020 biqqles.

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.

This file contains routines for parsing specific sets of information
from the game files. All exported functions return EntitySets.
"""

from collections import defaultdict
from typing import Dict, List, Tuple

from . import paths
from .dynamic import cached
from .formats import ini
from .entities import EntitySet
from .entities import Commodity, Ship
from .entities import Base, System, Group
from .entities import Solar, Object, Jump, BaseSolar, Star, Planet, PlanetaryBase, TradeLaneRing, Wreck
from .maps import PosVector, RotVector


@cached
def get_systems(meta=False) -> EntitySet[System]:
    """All systems defined in the game files."""
    systems = ini.fetch(paths.inis['universe'], 'system', {'nickname', 'strid_name', 'ids_info', 'navmapscale'},
                        target_key='file')

    return EntitySet(System(**s, ids_name=s.pop('strid_name')) for s in systems)


@cached
def get_bases() -> EntitySet[Base]:
    """All bases defined in the game files."""
    bases = ini.fetch(paths.inis['universe'], 'base', {'nickname', 'strid_name', 'system'})

    return EntitySet(Base(**b, ids_name=b.pop('strid_name'), ids_info=None, _market=_get_markets()[b['nickname']])
                     for b in bases)


@cached
def get_commodities() -> EntitySet[Commodity]:
    """All commodities defined in the game files."""
    path = paths.construct_path('DATA/EQUIPMENT/select_equip.ini')
    commodities = ini.fetch(path, 'commodity', {'nickname', 'ids_name', 'ids_info', 'volume'})

    result = []

    for c in commodities:
        good = _get_goods()[c['nickname']]
        market = _get_markets()[c['nickname']]
        result.append(Commodity(**c, item_icon=good.get('item_icon'), price=good['price'], _market=market))

    return EntitySet(result)


@cached
def get_groups() -> EntitySet[Group]:
    """All groups (i.e. factions) defined in the game files."""
    groups = ini.fetch(paths.inis['initial_world'], 'group', {'nickname', 'ids_name', 'ids_info'}, {'rep'})
    return EntitySet(Group(**g) for g in groups)


@cached
def get_ships() -> EntitySet[Ship]:
    """All ships defined in the game files."""
    stats = ini.fetch(paths.inis['ships'], 'ship',
                      {'nickname', 'ids_name', 'ids_info', 'nanobot_limit', 'shield_battery_limit', 'hold_size',
                       'hit_pts', 'ship_class', 'steering_torque', 'angular_drag', 'ids_info1', 'ids_info2',
                       'ids_info3'}, target_key='ids_info3')
    result: List[Ship] = []

    for s in stats:
        try:
            hull = _get_goods()[s['nickname']]
            package = _get_goods()[hull['nickname']]
            market = _get_markets()[package['nickname']]
        except KeyError:
            # ship not sold anywhere. todo: how should we handle this?
            continue
        ship = Ship(**s, _market=market, item_icon=hull['item_icon'], price=hull['price'], _hull=hull, _package=package)
        result.append(ship)

    return EntitySet(result)


@cached
def get_system_contents(system: System) -> EntitySet[Solar]:
    """All contents (objects and zones) of a system."""
    result = []
    contents = ini.parse(system.definition_path())

    rot0 = RotVector(0, 0, 0)

    # categorise objects based on their keys
    # from_keys and using get() for optional keys is a bit of a hack that has to be used until I release a replacement
    # for dataclasses
    for o in contents.get('object', []):
        if 'ids_name' not in o:
            continue
        o['_system'] = system
        o['pos'] = PosVector(*o['pos'])
        o.setdefault('rotate', rot0)
        o.setdefault('ids_info', None)  # not everything that ought to have ids_info does...

        keys = o.keys()
        if {'base', 'reputation', 'space_costume'} <= keys:
            result.append(BaseSolar.from_dict(o))
        elif 'goto' in keys:
            result.append(Jump.from_dict(o))
        elif 'prev_ring' in keys or 'next_ring' in keys:
            result.append(TradeLaneRing.from_dict(o, prev_ring=o.get('prev_ring'), next_ring=o.get('next_ring')))
        elif 'loadout' in keys and 'reputation' not in keys:
            result.append(Wreck.from_dict(o))
        elif 'star' in keys:
            result.append(Star.from_dict(o, atmosphere_range=o.get('atmosphere_range', 0)))
        elif 'spin' in keys:
            o.setdefault('atmosphere_range', 0)
            result.append(PlanetaryBase.from_dict(o) if 'base' in keys else Planet.from_dict(o))
        else:
            result.append(Object.from_dict(o))
    # todo: zones
    return EntitySet(result)


@cached
def _get_goods() -> Dict[str, Dict]:
    # This is an internal method. A good is anything that can be bought or sold.
    # get_commodities, get_ships and get_equipment link goods up to objects
    goods = ini.fetch(paths.inis['goods'],  # todo: equipment too
                      'good', {'nickname', 'price', 'item_icon', 'ship', 'price', 'hull', 'category'}, {'addon'})

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
    market = ini.fetch(paths.inis['markets'], 'basegood', {'base'}, {'marketgood'}, target_key='base')
    goods = _get_goods()
    result = defaultdict(lambda: {True: [], False: []})
    for b in market:
        base = b['base']
        base_market = b['marketgood']
        for good, min_rank, min_rep, min_stock, max_stock, depreciate, multiplier, *_ in base_market:
            try:
                sold = not (min_stock == 0 or max_stock == 0)
                price_at_base = goods[good]['price'] * multiplier
            except KeyError:
                continue

            result[base][sold].append((good, price_at_base))
            result[good][sold].append((base, price_at_base))
    return result
