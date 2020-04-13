# flint

**flint** (*Freelancer Intel*) is a platform-independent parser and ORM for the data files of [*Freelancer*](https://en.wikipedia.org/wiki/Freelancer_%28video_game%29), a 2003 space sim  for Windows developed by Digital Anvil.

Freelancer is interesting in that the game world can be entirely defined in [INI files](https://en.wikipedia.org/wiki/INI_file), a format more usually used to hold simple configuration data. Additional content (e.g. text, icons and models) are stored in a variety of binary formats.

flint implements a parser for Freelancer-style INIs, as well as platform-independent reader implementations for every binary file format used by Freelancer - BINI, resource DLL, and UTF. All these implementations can be found in [`flint/formats`](flint/formats). Additionally, resource string handling incorporates RDL (Freelancer's markup language) to HTML translation and some of the maths surrounding Freelancer's navmap has been implemented.

Taken together, this yields a simple yet powerful API that can be used to explore the game world, dump data or act as a foundation for Freelancer-related applications.

flint specifically supports vanilla Freelancer and [Discovery Freelancer](https://discoverygc.com), but in principle should work with any mod.

## Installation
flint is on PyPI:

```
python -m pip install fl-flint
```

Alternatively you can install straight from this repository:

```sh
python -m pip install https://github.com/biqqles/flint/archive/master.zip
```

Built wheels are also available under [Releases](https://github.com/biqqles/flint/releases), as is a changelog.

flint requires Python >= 3.6 because it uses the `dataclasses` module which was added in that release.

## Interactive shell
flint incorporates an interactive mode that can be used for testing or exploration. It provides a Python interpreter where flint is imported `as fl` and ready to use. To use it, run `python -m flint.interactive <path_to_freelancer>`. This mode will be used in the following examples.

## API description
The API is unstable until v1.0. Minor details may change.

### Initialisation
Before doing anything you will want to set the path to the Freelancer directory to be inspected. This is accomplished with `flint.set_install_path()` or automatically with the interactive shell as shown above.

### Core functions
flint defines several "core functions":

|Name                     |Type                  |Notes                                    |
|:------------------------|:---------------------|:----------------------------------------|
|**`flint.get_bases()`**  |`EntitySet[Base]`     |All bases defined in the game files      |
|**`flint.get_systems()`**|`EntitySet[System]`   |All systems defined in the game files    |
|**`flint.get_commodities()`**|`EntitySet[Commodity]`|All commodities defined in the game files|
|**`flint.get_ships()`**  |`EntitySet[Ship]`     |All ships defined in the game files      |
|**`flint.get_groups()`** |`EntitySet[Group]`    |All groups defined in the game files     |

(If you are on Python 3.7 or above, these have handy shorthands of the form `flint.bases`, `flint.systems`, `flint.commodities` etc.)

Functions in flint often return an *entity*, represented by the `Entity` data class, or *sets* of entities, represented by the `EntitySet` container. An `Entity` represents a unique entity in Freelancer, distinguished by a unique nickname. Entities are constructed from the game's INI files and contain methods to calculate derived attributes. For example:

```Python
(flint as fl) >>> fl.get_systems()
{'li01': System(nickname='li01', ids_name=196609, ids_info=66106, file='systems\\li01\\li01.ini', navmapscale=1.0),
 'li02': System(nickname='li02', ids_name=196610, ids_info=66084, file='systems\\li02\\li02.ini', navmapscale=1.0),
 'li03': System(nickname='li03', ids_name=196611, ids_info=66087, file='systems\\li03\\li03.ini', navmapscale=1.0),
 ...
}
(flint as fl) >>> [s.name() for s in fl.get_systems()]
['New York', 'California', 'Colorado', 'Texas', 'Alaska', 'New London', ...]
```

Entity types are described in detail in the next section.

### Entities
"Entities" form the foundation of flint's object-relational mapping (ORM). Freelancer-style INIs can be considered to form a crude relational database, and broadly speaking an *entity* here refers to anything in the game uniquely identified by a string *nickname*.

[**Base classes**](flint/entities/__init__.py)
#### Entity
>The base data class for any entity defined within Freelancer, distinguished by a nickname.

|Attributes          |Type              |Notes                                                       |
|:-------------------|:-----------------|:-----------------------------------------------------------|
|`nickname`          |`str`             |A unique string identifier for this entity                  |
|`ids_name`          |`int`             |Resource id for name                                        |
|`ids_info`          |`int`             |Resource id for infocard                                    |
|**Methods**         |                  |                                                            |
|**`name()`**        |`str`             |The display name of this entity                             |
|**`infocard(plain=False)`**|`str`      |The infocard for this entity, formatted in HTML unless `plain` is specified|

An `Entity`'s nickname uniquely identifies it - this means it is hashable.

An `Entity` marked as Abstract means that no entities in the game are directly classified as it - in other words, it is never returned by flint but can be used for typing and inheritance.

As you would expect, all the usual rules of object inheritance apply, i.e. inherited classes retain all their previous methods and attributes, so `System(Entity)` listed below has all the fields and methods of `Entity` above. Similarly, `PlanetaryBase(BaseSolar, Planet)` has all the attributes and methods of `BaseSolar` _and_ `Planet`.

#### EntitySet
An `EntitySet` is a set of entities of a particular type. An `EntitySet` is constructed from an iterable producing `Entity` objects, and it stores these in a hash table based on the nicknames of these entities. An `EntitySet` is therefore indexable by nickname, for example `fl.get_systems()['br01']` returns the `Entity` for New London.

For arbitrarily complex filtering, Python's excellent conditional generator expressions are recommended, for example `EntitySet(s for s in fl.get_systems() if s.nickname.startswith('br'))` returns an `EntitySet` containing all the systems in the house of Bretonia. `EntitySet`s are nominally immutable but two `EntitySet`s can be merged to create a new `EntitySet` using `+` or `+=`.

---
[**Universe**](flint/entities/universe.py)
#### System(Entity)
>A star system, containing [Solars](#solarentity).
>
|Attributes          |Type                  |Notes                                                       |
|:-------------------|----------------------|------------------------------------------------------------|
|`file`              |`str`                 |                                                            |
|`navmapscale`       |`float`               |                                                            |
|**Methods**         |                      |                                                            |
|**`definition_path()`**|`str`              |The absolute path to the file that defines this system's contents|
|**`contents()`**    |`EntitySet[Solar]`    |All solars in this system                                   |
|**`zones()`**       |`EntitySet[Zone]`     |All zones in this system                                    |
|**`objects()`**     |`EntitySet[Object]`   |All objects in this system                                  |
|**`bases()`**       |`EntitySet[BaseSolar]`|All base solars in this system                              |
|**`planets()`**     |`EntitySet[Planet]`   |All planets in this system                                  |
|**`stars()`**       |`EntitySet[Star]`     |All stars in this system                                    |
|**`connections()`** |`Dict[Jump, str]`     |The connections this system has to other systems            |
|**`lanes()`**       |`List[List[TradeLaneRing]]`|A list of lists of rings, where each nested list represents a complete trade lane and contains each ring in that lane in order|

#### Base(Entity)
>A space station or colonised planet, operated by a [Group](#groupentity).
>
|Attributes          |Type                  |Notes                                                       |
|:-------------------|----------------------|------------------------------------------------------------|
|`system`            |`str`                 |                                                            |
|`_market`           |`Dict`                |                                                            |
|**Methods**         |                      |                                                            |
|**`solar()`**       |`BaseSolar`           |Confusingly, Freelancer defines bases separately to their physical representation|
|**`buys()`**        |`Dict[str, int]`      |The goods this base buys, of the form {good -> price}       |
|**`sells()`**       |`Dict[str, int]`      |The goods this base sells, of the form {good -> price}      |

#### Group(Entity)
>A Group, also known as a faction, is an organisation in the Freelancer universe.
>
|Attributes          |Type                  |Notes                                                       |
|:-------------------|----------------------|------------------------------------------------------------|
|`rep`               |`List[str]`           |                                                            |
|**Methods**         |                      |                                                            |
|**`bases()`**       |`EntitySet[BaseSolar]`|Bases owned by this group                                   |
|**`rep_sheet()`**   |`Dict[str, float]`    |The goods this base buys, of the form {good -> price}       |

---

[**Goods**](flint/entities/goods.py)
#### Good(Entity)
>A Good is anything that can be bought or sold. [Commodities](#commoditygood), equipment and [ships](#shipgood) are all examples of goods. (Abstract.)
>
|Attributes          |Type                  |Notes                                                       |
|:-------------------|----------------------|------------------------------------------------------------|
|`item_icon`         |`Optional[str]`       |Path to icon, relative to DATA                              |
|`price`             |`int`                 |The default price for this good, pre market multiplier      |
|`_market`           |`Dict[bool, Tuple]`   |                                                            |
|**Methods**         |                      |                                                            |
|**`icon_path()`**   |`str`                 |The absolute path to the .3db file containing this item's icon|
|**`icon()`**        |`bytes`               |This good's icon in [TGA](https://en.wikipedia.org/wiki/Truevision_TGA) format|
|**`sold_at()`**     |`Dict[str, int]`      |A dict of bases that sell this good of the form {base_nickname: price}|
|**`bought_at()`**   |`Dict[str, int]`      |A dict of bases that buy this good of the form {base_nickname: price}|

#### Ship(Good)
>A starship with a cargo bay and possibly hardpoints for weapons.
>
|Attributes          |Type                  |Notes                                                       |
|:-------------------|----------------------|------------------------------------------------------------|
|`ids_info1`         |`int`                 |Ship infocards are in *four* parts                          |
|`ids_info2`         |`int`                 |                                                            |
|`ids_info3`         |`int`                 |                                                            |
|`ship_class`        |`int`                 |                                                            |
|`hit_pts`           |`int`                 |                                                            |
|`hold_size`         |`int`                 |                                                            |
|`nanobot_limit`     |`int`                 |                                                            |
|`shield_battery_limit`|`int`               |                                                            |
|`steering_torque`   |`float`               |                                                            |
|`angular_drag`      |`float`               |                                                            |
|`_hull`             |`Dict[str, Any]`      |                                                            |
|`_package`          |`Dict[str, Any]`      |                                                            |
|**Methods**         |                      |                                                            |
|**`type()`**        |`str`                 |The name of the type (class) of this ship                   |
|**`turn_rate()`**   |`float`               |Turn rate in degrees per second                             |

#### Commodity(Good)
>A Commodity is the representation of a good in tradeable/transportable form.
>
|Attributes          |Type                  |Notes                                                       |
|:-------------------|----------------------|------------------------------------------------------------|
|`volume`            |`float`               |Volume of one unit in ship's cargo bay                      |

---

[**Solars**](flint/entities/solars.py)
#### Solar(Entity)
>A solar is something fixed in space (this name comes from the DATA/SOLAR directory). (Abstract.)
>
|Attributes          |Type                  |Notes                                                       |
|:-------------------|----------------------|------------------------------------------------------------|
|`pos`               |`PosVector`           |Position vector for this solar                              |
|`_system`           |`System`              |The system this solar resides in                            |
|**Methods**         |                      |                                                            |
|**`sector()`**      |`str`                 |The human-readable navmap coordinate (the centre of) this solar resides in|

#### Object(Solar)
>Generic class for a celestial body - a solid object in space. Objects are automatically classified into subclasses in `routines`.
>
|Attributes          |Type                  |Notes                                                       |
|:-------------------|----------------------|------------------------------------------------------------|
|`archetype`         |`str`                 |                                                            |

#### BaseSolar(Object)
>The physical representation of a [Base](#base-entity).
>
|Attributes          |Type                  |Notes                                                       |
|:-------------------|----------------------|------------------------------------------------------------|
|`reputation`        |`str`                 |                                                            |
|`reputation`        | str                  |The nickname of the group this base belongs to              |
|`base`              |`str`                 |Nickname for the base (in universe.ini) this solar represents|
|**Methods**         |                      |                                                            |
|**`owner`**         |`Group`               |The Group entity that operates this base                    |
|**`universe_base`** |`Base`                |The Base entity this solar represents                       |

#### Jump(Object)
>A jump conduit is a wormhole - natural or artificial - between [Systems](#systementity).
>
|Attributes          |Type                  |Notes                                                       |
|:-------------------|----------------------|------------------------------------------------------------|
|`goto`              |`str`                 |                                                            |
|**Methods**         |                      |                                                            |
|**`origin_system()`**|`System`             |The system this wormhole starts in                          |
|**`destination_system()`**|`str`           |The system this wormhole ends in                            |

#### TradeLaneRing(Object)
>A trade lane ring is a component of a trade lane, a structure which provides "superluminal travel" within a system.
>
|Attributes          |Type                  |Notes                                                       |
|:-------------------|----------------------|------------------------------------------------------------|
|`prev_ring`         |`Optional[str]`       |                                                            |
|`next_ring`         |`Optional[str]`       |                                                            |

#### Spheroid(Object)
>A star or planet. (Abstract.)
>
|Attributes          |Type                  |Notes                                                       |
|:-------------------|----------------------|------------------------------------------------------------|
|`atmosphere_range`  |`int`                 |                                                            |
|`burn_color`        |`Tuple[int, int, int]`|                                                            |

#### Star(Spheroid)
>A star in a System.
>
|Attributes          |Type                  |Notes                                                       |
|:-------------------|----------------------|------------------------------------------------------------|
|`star`              |`str`                 |                                                            |
|`ambient_color`     |`Tuple[int, int, int]`|                                                            |

#### Planet(Spheroid)
>A planet in a System.
>
|Attributes          |Type                  |Notes                                                       |
|:-------------------|----------------------|------------------------------------------------------------|
|`spin`              |`Tuple[float, float, float]`|                                                      |

#### PlanetaryBase(BaseSolar, Planet)
>A base on the surface of a planet, typically accessible via a docking ring.


#### Zone(Solar)
>A zone is a region of space, possibly with effects attached.
>
|Attributes          |Type                  |Notes                                                       |
|:-------------------|----------------------|------------------------------------------------------------|
|`size`              |`Union[int, Tuple[int, int], Tuple[int, int, int]]`|                               |
|`shape`             |`str`                 |One of: sphere, ring, box, ellipsoid                        |


---

### Formats
#### Common interface

#### INI
INI files are traditionally used to store brief configuration or initialisation files for programs, as the name suggests. However, Freelancer uses them essentially as crude relational databases. The simplicity of the format may be a factor in the growth of Freelancer's vibrant modding community. In the vanilla game, INI files are shipped in the compressed BINI format described below.

Python's standard library contains the module `configparser` which provides built-in INI file parsing. However, the INI files used by Freelancer do not conform to the standard it expects.

#### BINI
BINI (Binary INI) is the compressed format INIs are stored in in the vanilla game. Typically these are distributed in decompressed form by mods to enable the contents to be edited with a text editor. Technically, BINI is an elegant and simple format.

#### DLL
Windows resource DLLs are used to store names and infocards. DLLs are a subset of the PE format. Rich text is formatted in an XML-based markup language unique to Freelancer called RDL. flint's DLL implementation handles conversion of this to HTML.

#### UTF
Another of Digital Anvil's formats, UTF (Universal Tree Format), is used as a catch-all container for binary files (blobs), with the exception of audio files which use the WAV container. UTF files can have the file extensions `.3db` (icons and textures), `.txm` (effects and some textures) and `.cmp` (models).

## To be added
- Comprehensive parsing of zones
- Parsing of equipment
- Route planning
- Writer implementations for formats

## Acknowledgements
- Bas Westerbaan for [documenting](https://drive.google.com/open?id=1JlQa19mEiuHzpnAc8B1d2wTcgnvdl_tH) the BINI format
- Treewyrm for [documenting](https://wiki.librelancer.net/utf:universal_tree_format) UTF
- adoxa and cshake for [deciphering](https://the-starport.net/modules/newbb/viewtopic.php?&topic_id=562) RDL
- cshake and Alex for providing a cross-platform DLL parser, which facilitated early development
- Syrus for advice in the early stages of development
