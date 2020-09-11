"""
Copyright (C) 2016, 2017, 2020 biqqles.

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.

This file holds code and data class definitions for things peculiar
to the MISSIONS directory. These "things" aren't quite entities, as
they lack associated string resource fields and/or nicknames.
Instead they "belong to" a composite Entity, like a Base or Faction.
"""
from typing import Tuple, List, Dict, Optional

from dataclassy import dataclass

from .formats import ini
from . import cached, paths


@cached
def get_faction_props() -> Dict[str, 'FactionProps']:
    """Produce a dictionary of faction nicknames to their associated FactionProps object."""
    props = ini.sections(paths.construct_path('DATA/MISSIONS/faction_prop.ini'))
    return {p['affiliation']: FactionProps(**p) for p in props['factionprops']}


@cached
def get_mbases() -> Dict[str, 'MBase']:
    """Produce a dictionary of base nicknames to their associated MBase entry. Each MBase section's associated
    MVendor, BaseFaction and GF_NPC sections are folded into attributes of the resulting MBase object.

    Implementation note: because the ordering of these sections is guaranteed (breaking this rule will crash
    Freelancer), it is safe to assume that base is defined in subsequent code paths."""
    sections = ini.group(paths.construct_path('DATA/MISSIONS/mbases.ini'), fold_sections=False)

    bases = []

    for name, contents in sections:
        if name == 'mbase':
            base = MBase(**contents[0])
            bases.append(base)
        elif name == 'mvendor':
            # noinspection PyUnboundLocalVariable
            base.vendors.append(MVendor(**contents[0]))
        elif name == 'basefaction':
            base.factions.extend(BaseFaction(**faction) for faction in contents)
        elif name == 'gf_npc':
            base.npcs.extend(GF_NPC(**npc) for npc in contents if 'nickname' in npc)
        elif name == 'mroom':
            base.rooms.extend(MRoom(**room) for room in contents)

    return {b.nickname: b for b in bases}


@dataclass
class MBase:
    """A "mission base" section, found in mbases.ini. Provides additional attributes to the base that nickname refers
    to. The optional fields of this class, as with the following classes, are based on my observations of Discovery
    Freelancer. There are likely more fields which Freelancer does not strictly require."""
    nickname: str
    local_faction: str
    diff: int
    msg_id_prefix: Optional[str] = None

    vendors: List['MVendor'] = []
    factions: List['BaseFaction'] = []
    npcs: List['GF_NPC'] = []
    rooms: List['MRoom'] = []


@dataclass
class MVendor:
    """Found in mbases.ini, this section describes the preceding base's mission vendor, aka the "jobs board"."""
    num_offers: Tuple[int, int]


@dataclass
class BaseFaction:
    """Found in mbases.ini, this section describes an individual NPC present on the preceding base."""
    faction: str
    weight: int
    offers_missions: bool = False
    mission_type: Optional[Tuple[str, float, float, int]] = None
    npc: List[str] = []


# noinspection PyPep8Naming
@dataclass
class GF_NPC:
    """Found in mbases.ini, this section describes an individual NPC present on the preceding base."""
    nickname: str
    body: Optional[str] = None
    head: Optional[str] = None
    lefthand: Optional[str] = None
    righthand: Optional[str] = None
    individual_name: int
    affiliation: str
    voice: str
    misn: Tuple[str, float, float] = []
    room: Optional[str] = None
    bribe: List[Tuple[str, int, int]] = []
    rumor: List[Tuple[str, str, int, int]] = []
    know: Optional[Tuple[int, int, int, int]] = None
    knowdb: Optional[str] = None
    rumorknowdb: Optional[str] = None
    accessory: Optional[str] = None
    base_appr: Optional[str] = None
    rumor_type2: Optional[Tuple[str, str, int, int]] = None


@dataclass
class MRoom:
    """Found in mbases.ini, this section describes a particular room in the preceding base."""
    nickname: str
    character_density: int = 0
    fixture: List[Tuple[str, str, str, str]] = []


@dataclass
class FactionProps:
    """The FactionProps section, found in faction_prop.ini, defines much of the behaviour of a faction's NPCs in
    space."""
    affiliation: str
    legality: str
    nickname_plurality: str
    msg_id_prefix: str
    jump_preference: str
    npc_ship: List[str] = []
    voice: List[str] = []
    mc_costume: str
    space_costume: List[Tuple[str, str, str]] = []
    firstname_male: Optional[Tuple[int, int]] = None
    firstname_female: Optional[Tuple[int, int]] = None
    lastname: Tuple[int, int]
    rank_desig: Tuple[int, int, int, int, int]
    formation_desig: Tuple[int, int]
    large_ship_desig: Optional[int] = None
    large_ship_names: Tuple[int, int] = None
    scan_for_cargo: List[Tuple[str, int]] = []
    scan_announce: bool = False
    scan_chance: float = 0.0
    formation: List[Tuple[str, str]]
