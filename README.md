# flint

**flint** (*Freelancer Intel*) is a platform-independent parser and ORM for the data files of [*Freelancer*](https://en.wikipedia.org/wiki/Freelancer_%28video_game%29), a 2003 space sim  for Windows developed by Digital Anvil.

Freelancer is interesting in that the game world can be entirely defined in [INI files](https://en.wikipedia.org/wiki/INI_file), a format more usually used to hold simple configuration data. Additional content (e.g. text, icons and models) are stored in a variety of binary formats.

flint implements a parser for Freelancer-style INIs, as well as platform-independent reader implementations for every binary file format used by Freelancer - BINI, resource DLL, and UTF. All these implementations can be found in [`flint/formats`](flint/formats). Additionally, resource string handling incorporates RDL (Freelancer's markup language) to HTML translation and some of the maths surrounding Freelancer's navmap has been implemented.

Taken together, this yields a simple yet powerful API that can be used to explore the game world, dump data or act as a foundation for Freelancer-related applications.

flint explicitly supports vanilla Freelancer and [Discovery Freelancer](https://discoverygc.com), but in principle should (though it's not yet) be implemented robustly enough to work with any valid mod, no matter how esoteric.

## Installation
Install the latest stable version from [PyPI](https://pypi.org/project/fl-flint) with pip:

```sh
pip install fl-flint
```

Or install the latest development version straight from this repository:

```sh
pip install https://github.com/biqqles/flint/archive/master.zip -U
```

Built wheels are also available under [Releases](https://github.com/biqqles/flint/releases), as is a changelog.

flint requires Python >= 3.6.

## API documentation

The documentation has been moved to the [wiki](https://github.com/biqqles/flint/wiki).

## Ongoing work
- Entities
	- Comprehensive classification of `Zone` types
- Missions
	- Reading `mbases.ini`
- Interface
	- Reading `infocardmap.ini`
	- Bidirectionally transforming RDL from and to XHTML without using a crude lookup table
- Paths
	- Extracting paths from Freelancer.exe
- Formats
	- Writer implementations for formats

## Acknowledgements
Thanks to the admins, members and supporters of [The Starport](https://the-starport.net) for hosting an invaluable source of information about modding Freelancer.

In addition, particular thanks goes to:

- Bas Westerbaan for [documenting](https://drive.google.com/open?id=1JlQa19mEiuHzpnAc8B1d2wTcgnvdl_tH) the BINI format
- Treewyrm for [documenting](https://wiki.librelancer.net/utf:universal_tree_format) UTF
- adoxa and cshake for [deciphering](https://the-starport.net/modules/newbb/viewtopic.php?&topic_id=562) RDL
- cshake and Alex for providing a cross-platform DLL parser, which facilitated early development
- Syrus for support in the early stages of development
