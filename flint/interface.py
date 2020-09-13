"""
Copyright (C) 2016, 2017, 2020 biqqles.

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.

Interface-related functions, such as routines for translating RDL.
"""
import xml.etree.ElementTree as xml


def rdl_to_html(rdl: str) -> str:
    """Translate RDL to HTML. Currently this uses a crude lookup table. In future I want to replace this with
    proper interpretation of the XML."""
    result = rdl
    for rdl_tag, html_tag in RDL_TO_HTML.items():
        result = result.replace(rdl_tag, html_tag)
    return result


def rdl_to_plaintext(rdl: str) -> str:
    """Translate RDL to plaintext, stripping all tags and replacing <PARA/> with a newline."""
    rdl = rdl.replace('<PARA/>', '\n').replace('</PARA>', '')
    tree = xml.fromstring(rdl)
    return xml.tostring(tree, encoding='unicode', method='text')


def html_to_rdl(html: str) -> str:
    """Translate HTML to RDL. See the docstring for `rdl_to_html` for more information."""
    result = html
    for rdl_tag, html_tag in RDL_TO_HTML.items():
        result = result.replace(html_tag, rdl_tag)
    return result


# A lookup table mapping RDL (Render Display List) tags to HTML(4). Freelancer, to my eternal horror, uses these for
# formatting for strings inside these resource DLLs. Based on work by adoxa and cshake.
# More information can be found in this thread: <https://the-starport.net/modules/newbb/viewtopic.php?&topic_id=562>
RDL_TO_HTML = {
    '<TRA data="1" mask="1" def="-2"/>':           '<b>',  # bold
    '<TRA bold="true"/>':                          '<b>',  # rare bold
    '<TRA data="0" mask="1" def="-1"/>':           '</b>',  # un-bold
    '<TRA data="2" mask="3" def="-3"/>':           '<i>',  # italic 1
    '<TRA data="0" mask="3" def="-1"/>':           '</i>',  # un-italic 1
    '<TRA data="98" mask="-29" def="-3"/>':        '<i>',  # italic 2
    '<TRA data="96" mask="-29" def="-1"/>':        '</i>',  # un-italic 2
    '<TRA data="2" mask="2" def="-3"/>':           '<i>',  # italic 3
    '<TRA data="0" mask="2" def="-1"/>':           '</i>',  # un-italic 3
    '<TRA data="5" mask="5" def="-6"/>':           '<b><u>',  # (bold, underline) 1
    '<TRA data="0" mask="5" def="-1"/>':           '</b></u>',  # un-(bold, underline) 1
    '<TRA data="5" mask="7" def="-6"/>':           '<b><u>',  # (bold, underline) 2
    '<TRA data="0" mask="7" def="-1"/>':           '</b></u>',  # un-(bold, underline) 2
    '<TRA data="65280" mask="-32" def="31"/>':     '<font color="red">',  # red
    '<TRA data="96" mask="-32" def="-1"/>':        '</font>',  # un-colour
    '<TRA data="65281" mask="-31" def="30"/>':     '<b><font color="red">',  # (bold, red)
    '<TRA data="96" mask="-31" def="-1"/>':        '</b></font>',  # un-(bold, red)
    '<TRA data="-16777216" mask="-32" def="31"/>': '<font color="blue">',  # blue
    '<PARA/>':                                     '<p>',  # newline
    '</PARA>':                                     '</p>',
    '<JUST loc="left"/>':                          '<p align="left">',  # newline with left-aligned text
    '<JUST loc="center"/>':                        '<p align="center">',  # newline with centred text
    '\xa0':                                        '&nbsp;',  # non-breaking space, is often present after the title
    '<RDL>':                                       '',  # seemingly meaningless tags...
    '</RDL>':                                      '',
    '<TEXT>':                                      '',
    '</TEXT>':                                     '',
    '<PUSH/>':                                     '',
    '<POP/>':                                      '',
    '<?xml version="1.0" encoding="UTF-16"?>':     '',  # xml header; removed for neatness
}
