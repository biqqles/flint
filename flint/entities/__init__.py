"""
Copyright (C) 2016, 2017, 2020 biqqles.

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.

This namespace contains definitions for entities found within
Freelancer.
"""
from typing import TypeVar, Iterable, Generic, Type, Optional, Dict, Union
from collections.abc import Mapping, KeysView, ItemsView
from functools import lru_cache
import operator
import pprint

from dataclassy import dataclass

from ..formats import dll


@dataclass(kwargs=True, slots=True)
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
    ids_name: Optional[int] = None  # resource id for name. newcharacter and universe.ini call this strid_name instead
    ids_info: Optional[int] = None  # resource id for infocard

    def name(self) -> str:
        """The display name of this entity."""
        return dll.lookup(self.ids_name)

    def infocard(self, markup='html') -> str:
        """The infocard for this entity, formatted in the markup language (`rdl`, `html` or `plain`) specified."""
        lookup = self._markup_formats[markup]
        return lookup(self.ids_info)

    def __hash__(self) -> int:
        return hash(self.nickname)

    def __eq__(self, other) -> bool:
        return self.nickname == other.nickname

    _markup_formats = dict(html=dll.lookup_as_html, plain=dll.lookup_as_plain, rdl=dll.lookup)


T = TypeVar('T')
F = TypeVar('F')


class EntitySet(Mapping, Generic[T]):
    """An immutable collection of entities, indexed by nickname."""
    pprint.sorted = lambda v, key=None: v  # patch pprint's sorted implementation to print in insertion order

    def __init__(self, entities: Union[Iterable[T], Dict[str, T]]):
        if type(entities) is dict:
            self._map = entities
        else:
            self._map = {e.nickname: e for e in entities}

    def __repr__(self):
        return f'EntitySet({pprint.pformat(self._map)})'

    def __getitem__(self, key: str) -> T:
        if type(key) is not str:
            raise TypeError(f'Only strings may be used as indices, not {type(key)!r}')
        assert type(key) is str, repr(type(key))
        return self._map[key]

    def __iter__(self):
        """Iteration is over values."""
        return iter(self._map.values())

    def __contains__(self, item):
        """Membership checking is as per hash table."""
        return type(item) is str and item in self._map

    def __len__(self):
        """Length is the size of the map."""
        return len(self._map)

    def __eq__(self, other: 'EntitySet'):
        """EntitySets may be compared by comparing their maps."""
        if not isinstance(other, EntitySet):
            raise TypeError(f'Cannot compare EntitySet with {type(other)!r}')
        return self._map == other._map

    def __hash__(self):
        """The set of keys is constant for an EntitySet and allows it to be hashed."""
        return hash(frozenset(self._map))

    def __add__(self, other) -> 'EntitySet[T]':
        """Two EntitySets can be added together to create a new EntitySet."""
        if type(other) is not type(self):
            raise TypeError(f'Can only concatenate EntitySet (not {type(other)}) with EntitySet.')
        return EntitySet({e for e in self} | {e for e in other})

    def __iadd__(self, other) -> 'EntitySet[T]':
        """An EntitySet can be extended."""
        return self + other

    def keys(self) -> KeysView:
        """The nicknames of all entities in this set."""
        return self._map.keys()

    def items(self) -> ItemsView:
        """All entities in this set."""
        return self._map.items()

    @lru_cache(maxsize=256)
    def of_type(self, type_: Type[F]) -> 'EntitySet[F]':
        """Return a new, homogeneous EntitySet containing only Entities which are instances of the given type."""
        return EntitySet(filter(lambda e: isinstance(e, type_), self))

    @lru_cache(maxsize=256)
    def reindex(self, on: str) -> 'EntitySet[T]':
        """Reindex this EntitySet on the field with name `on`."""
        return EntitySet({getattr(entity, on): entity for entity in self})

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
        if not callable(getattr(self.first, field, None)):
            return self.reindex(field)
        return EntitySet(e for e in self if op(vars(e).get(field) or getattr(e, field)(), value))

    def unique(self, **kwargs) -> Optional[T]:
        """Analogous to `where` but returns the Entity which is guaranteed to uniquely match the specified field/value
        combination. If no such Entity is present, return None."""
        assert len(kwargs) == 1
        field, value = next(iter(kwargs.items()))
        return self.reindex(field).get(value)

    @property
    def first(self) -> Optional[T]:
        """Return the first entity in the set, or None if it is empty. This is useful both for testing. If a query is
        expected to return exactly one result, you likely want to use unique() instead of this property."""
        return next(iter(self), None)


# exported types
from .equipment import *
from .goods import *
from .ship import *
from .solars import *
from .universe import *
