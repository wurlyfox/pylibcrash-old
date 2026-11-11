class GoolHeader(Packable):
	pass
	
class GoolStateMap(Packable):
	field_map = {
		'event_map': {
			'count': TODO (how do we get this),
			'pack': ('internal', 0)
		},
		'subtype_map': {
			'count': '$remainder',
			'pack': ('internal', 1)
		}
	}
	
class GoolState(Packable):
	pass
	
class GoolAnim(Packable):
	field_map = {
		'$subclass_id': 'type',
		'data': {
			'count': '$remainder',
			'pack': ('internal', 0)
		}
	}
	
class GoolVertexAnim(GoolAnim):
	subclass_id = 1
	field_map = {}
	
class GoolSpriteAnim(GoolAnim):
	subclass_id = 2
	field_map = {
		'clut_texinfos': {
			'count': (lambda c: c.length*2, 
					  lambda p,v: setattr(p, 'count', v//2))
			'pack': ('internal', 0)
		}
	}
	
class GoolFont(GoolAnim):
	subclass_id = 3
	field_map = {
		'glyphs': {
			'count': 'length',
			'pack': ('internal', 0)
		},
		'backdrop': {
			'type': 'gool_glyph',
			'pack': ('internal', 1)
		}
	}
	
class GoolText(GoolAnim):
	subclass_id = 4
	field_map = {
		'strings': {
			'count': 'length',
			'type': str, # TODO: new type
			'pack': ('internal', 0)
		}
	}
	
class GoolFragAnim(GoolAnim):
	subclass_id = 5
	field_map = {
		'rects': {
			'count': 'length',
			'pack': ('internal', 0)
		}
	}

class Gool(Entry):
	subclass_id = 11
	field_map = Entry.extend_field_map()
	field_map['item_data']['partitions'] = {
		'header': {
			'type': 'gool_header',
			'pack': ('internal', 0)
		},
		'code': {
			'type': {
			    'type': 'uint32_t',
				'count': '$remainder'
			},
			'pack': ('internal', 1)
		},
		'data': {
			'type': {
				'type': 'uint32_t',
				'count': '$remainder'
			}
			'pack': ('internal', 2)
		},
		'state_map': {
			'type': 'gool_state_map',
			'pack': ('internal', 3)
		},
		'states': {
			'type': {
				'type': 'gool_state',
				'count': '$remainder'
			},
			'pack': ('internal', 4)
		},
		'anims': {
			'type': {
				'type': 'gool_anim',
				'size': '$remainder'
			},
			'pack': ('internal', 5)
		}
	}
	
	def get_dependencies(self, nsf):
		valid_eids = [nsf.entry(pte.eid).eid 
					  for pte in nsf.dir.page_table]
		eids = []
		for anim in self.anims:
			if isinstance(anim, GoolVertexAnim):
				eid = anim.svtx
			elif isinstance(anim, GoolSpriteAnim) or \
			     isinstance(anim, GoolFragAnim) or \
			     isinstance(anim, GoolFont):
				eid = anim.tpage
			eids.append(eid)
		for value in self.data:
			if Eid(value) in valid_eids:
				eids.append(value)
				
		entries = [nsf.entry(eid) for eid in eids]
		for idx in range(len(entries)):
			entry = entries[idx]
			depends = entry.get_dependencies()
			entries.extend(depends)
		return entries		
