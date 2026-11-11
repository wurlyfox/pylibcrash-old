from libcrash import ffi
from pylibcrash.nsf import Nsf
from pylibcrash.nsd import Nsd, NsdPte, NsdLdat, Lid
from pylibcrash.page import Page, PageCompressed, Pgid, TexturePage
from pylibcrash.entry import Entry, Eid

from pylibcrash.formats import type_map as format_type_map

from ctypemap.base import config

type_map = {
	'nsd': Nsd,
	'nsf': Nsf,
	'page': Page,
	'page_compressed': PageCompressed,
	'entry': Entry,
	'eid_t': Eid,
	'pgid_t': Pgid,
	'tpage': TexturePage, # **must come after Entry
	'lid_t': Lid,
	'nsd_pte': NsdPte,
	'nsd_ldat': NsdLdat
}
__all__ = ['type_map'] + [ptype.__name__ for ptype in type_map.values()]

type_map = {**type_map, **format_type_map}
config(ffi, type_map)
