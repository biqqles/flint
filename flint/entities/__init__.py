"""
Copyright (C) 2016, 2017, 2020 biqqles.

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.

This module contains definitions for entities in Freelancer.
"""
from typing import TypeVar, Iterable, Generic, Hashable
import collections.abc
import operator
import pprint

from dataclassy import dataclass

from ..formats import dll


@dataclass(kwargs=True, frozen=True)
class Entity:
    """The base data class for any entity defined within Freelancer, distinguished by its nickname.

    Attributes (fields) of subclasses should only be used for the "primitive" attributes that define an entity in the
    inis. These should reproduce the names exactly as they appear in the inis to enable Entities to be automatically
    initialised from said files. Fields with clear default values (e.g. navmapscale in universe.ini, which defaults to
    1.0), dataclasses permitting (only fields at the end of the can have default values). Otherwise, all fields must be
    provided.

    Any attributes not present in the game files should have names beginning with _ to denote their.
    If you need to extend these classes to include non-standard fields (e.g. mods), you can take the output of ini.parse
    use dataclasses.from_dict to dynamically define a dataclass and inherit from these classes to get their methods.

    Derived attributes are represented as methods (ideally these would be properties, but this allows them to be
    distinguished from primitive attributes).

    All fields must be set, or have a default value, in which case that value will be used."""
    nickname: str  # a unique string identifier for this entity
    ids_name: int  # resource id for name. note this is occasionally referred to as strid_name in the game files
    ids_info: int  # resource id for infocard

    def name(self) -> str:
        """The display name of this entity."""
        return dll.lookup(self.ids_name)

    def infocard(self, plain=False) -> str:
        """The infocard for this entity, formatted in HTML unless `plain` is specified."""
        lookup = dll.lookup if plain else dll.lookup_as_html
        return lookup(self.ids_info)

    def __hash__(self) -> int:
        return hash(self.nickname)

    def __eq__(self, other) -> bool:
        return self.nickname == other.nickname


T = TypeVar('T')


class EntitySet(collections.abc.Mapping, Generic[T]):
    """A collection of entities, indexable by nickname."""
    def __init__(self, entities: Iterable[T]):
        self._map = {e.nickname: e for e in entities}

    def __repr__(self):
        pprint.sorted = lambda v, key=None: v  # override pprint's sorted implementation to print in insertion order
        return pprint.pformat(self._map)

    def __getitem__(self, key: str) -> T:
        return self._map[key]

    def __iter__(self):
        """Iteration is over values"""
        return iter(self._map.values())

    def __contains__(self, item):
        """Membership checking is as per hash table."""
        return isinstance(item, Hashable) and item in self._map

    def __len__(self):
        return len(self._map)

    def __add__(self, other):
        """Two EntitySets can be added together."""
        if type(other) is not type(self):
            raise TypeError(f'Can only concatenate EntitySet (not {type(other)}) with EntitySet.')
        return EntitySet({e for e in self} | {e for e in other})

    def __iadd__(self, other):
        """An EntitySet can be extended."""
        return self + other

    def where(self, op=operator.eq, **kwargs) -> 'EntitySet[T]':
        """Return elements of this EntitySet for which _all_ specified fields match their specified conditions.
        (Like a very rudimentary ORM.)
        E.g. `systems.where(name='New Berlin')`.
        For more complicated queries, use Python's own conditional generator expressions:
        E.g. (s for s in systems if s.nickname.startswith('rh'))"""
        return EntitySet(e for e in self if (all(op(getattr(e, f), c) for f, c in kwargs.items())))

    @property
    def arb(self) -> T:
        """Another convenience function: return an arbitrary Entity in the set (actually the first now dicts are
        ordered!). For testing."""
        return next(iter(self), None)


# exported types
from .goods import Ship, Commodity
from .solars import Solar, Object, Jump, BaseSolar, Planet, Star, PlanetaryBase, TradeLaneRing, Wreck, Zone
from .universe import Base, System, Faction
