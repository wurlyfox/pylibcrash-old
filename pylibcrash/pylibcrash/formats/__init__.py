from pylibcrash.formats.wgeo import *
from pylibcrash.formats.slst import *
from pylibcrash.formats.zdat import *

type_map = {
	'wgeo_header': WgeoHeader,
	'wgeo_polygon': WgeoPolygon,
	'wgeo_vertex': WgeoVertex,
	'wgeo_texinfo': WgeoTexinfo,
	'wgeo_palinfo': WgeoPalinfo,
	'slst': SlstItem,
	'slst_delta': SlstDelta,
	'poly_id': PolyId,
	'zone_header': ZoneHeader,
	'zone_dimensions': ZoneDimensions,
	'zone_path': ZonePath,
	'zone_entity': ZoneEntity,
	'zone_world': ZoneWorld,
	'zone_collisions': ZoneCollisions,
	'zone_neighbor_path': ZoneNeighborPath,
	'zone_path_point': ZonePathPoint,
	'zone_entity_path_point': ZoneEntityPathPoint,
	'zone_entity_null': ZoneEntityNull,
	'zone_bounds': ZoneBounds
}

__all__ = ['type_map'] + [ptype.__name__ for ptype in type_map.values()]
