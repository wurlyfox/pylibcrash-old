require "scripts.gte"
require "scripts.util"

require "scripts.crash.geom"

function getzpp()
	local curzone = readu32(game.curzone)
	local curpath = readu32(game.curpath)
	local header = readu32(curzone+16)
	local paths_idx = readu32(header+0x204)
	local path_count = readu32(header+0x208)
	local curpathidx = -1
	for i=0, path_count do
		local path = readu32(curzone+16+((paths_idx+i)*4))
		if path == curpath then
			curpathidx = i
			break
		end
	end
	local curprogress = readu32(game.curprogress)
	local curpt = curprogress >> 8
	local curzoneeid = readu32(curzone+4)
	local curzoneeidstr = eidtoname(curzoneeid)

	local zpp = { zone=curzone,
	              path=curpath,
	              progress=curprogress,
	              zoneeid=curzoneeid,
	              zoneeidstr=curzoneeidstr,
	              pathidx=curpathidx,
	              pt=curpt }
	return zpp
end
