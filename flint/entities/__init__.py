"""
Copyright (C) 2016, 2017, 2020 biqqles.

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.

This module contains definitions for entities in Freelancer.
"""
from typing import TypeVar, Iterable, Generic, Hashable, Type
from collections.abc import Mapping
import operator
import pprint

from dataclassy import dataclass

from ..formats import dll


@dataclass(kwargs=True, frozen=True)
class Entity:
    """
    The base data class for any entity defined within Freelancer, distinguished by a nickname.

    Attributes (fields) of Entity classes represent entries defined in the INI file section type which this class
    represents. This allows Entities to be automatically constructed from parsed INI files. Fields may have default
    values (defaults are inferred from the input Freelancer expects rather than being defined in the INI files).

    Methods represent derived fields. For example, the ids_name attribute stores the resource ID of an Entity's name as
    defined in the INI. The name() method looks up this resource ID in the resource table and returns the string it
    refers to.

    Attributes not present in the INIs but useful to be passed at construction time /can/ be defined, though this should
    be kept to a minimum. These attributes must have names beginning with _ to denote their internal status.

    If you want to extend these classes to cover non-standard fields (e.g. for an unsupported mod), you can use
    dataclassy.create_dataclass to dynamically define a dataclass and then use these classes as mixins.
    """
    nickname: str  # a unique string identifier for this entity
    ids_name: int  # resource id for name. note this is occasionally referred to as strid_name in the game files
    ids_info: int  # resource id for infocard

    def name(self) -> str:
        """The display name of this entity."""
        return dll.lookup(self.ids_name)

    def infocard(self, markup='html') -> str:
        """The infocard for this entity, formatted in the markup language (`rdl`, `html` or `plain`) specified."""
        if markup == 'html':
            lookup = dll.lookup_as_html
        elif markup == 'plain':
            lookup = dll.lookup_as_plain
        elif markup == 'rdl':
            lookup = dll.lookup
        else:
            raise ValueError
        return lookup(self.ids_info)

    def __hash__(self) -> int:
        return hash(self.nickname)

    def __eq__(self, other) -> bool:
        return self.nickname == other.nickname


T = TypeVar('T')


class EntitySet(Mapping, Generic[T]):
    """An immutable collection of entities, indexed by nickname."""
    def __init__(self, entities: Iterable[T]):
        self._map = {e.nickname: e for e in entities}

    def __repr__(self):
        pprint.sorted = lambda v, key=None: v  # override pprint's sorted implementation to print in insertion order
        return pprint.pformat(self._map)

    def __getitem__(self, key: str) -> T:
        return self._map[key]

    def __iter__(self):
        """Iteration is over values."""
        return iter(self._map.values())

    def __contains__(self, item):
        """Membership checking is as per hash table."""
        return isinstance(item, Hashable) and item in self._map

    def __len__(self):
        """Length is the size of the map."""
        return len(self._map)

    def __add__(self, other) -> 'EntitySet[T]':
        """Two EntitySets can be added together to create a new EntitySet."""
        if type(other) is not type(self):
            raise TypeError(f'Can only concatenate EntitySet (not {type(other)}) with EntitySet.')
        return EntitySet({e for e in self} | {e for e in other})

    def __iadd__(self, other) -> 'EntitySet[T]':
        """An EntitySet can be extended."""
        return self + other

    def of_type(self, type_: Type) -> 'EntitySet[T]':
        """Return a new, homogeneous EntitySet containing only Entities which are instances of the given type."""
        return EntitySet(filter(lambda e: isinstance(e, type_), self))

    def where(self, op=operator.eq, **kwargs) -> 'EntitySet[T]':
        """Return a new EntitySet containing only Entities for which the given field matches the given condition.
        Attributes and methods which do not take an argument can be used as fields.
        Usage example: `systems.where(name='New Berlin')`.

        The parameter `op` specifies the comparison operation to be performed on the field. It defaults to testing
        for equality.

        For more complicated queries, use Python's own conditional generator expressions:
        E.g. EntitySet(s for s in systems if s.nickname.startswith('rh'))"""
        assert len(kwargs) == 1
        field, value = next(iter(kwargs.items()))
        return EntitySet(e for e in self if op(vars(e).get(field) or getattr(e, field)(), value))

    @property
    def arb(self) -> T:
        """Another convenience function: return an arbitrary Entity in the set (actually the first now dicts are
        ordered!). For testing."""
        return next(iter(self), None)


# exported types
from .goods import Ship, Commodity
from .solars import Solar, Object, Jump, BaseSolar, Planet, Star, PlanetaryBase, TradeLaneRing, Wreck, Zone
from .universe import Base, System, Faction
