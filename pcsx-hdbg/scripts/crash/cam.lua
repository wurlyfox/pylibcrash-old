math = require('math')
here = 0

function cam_get_loc()
	local curpath = readu32(game.curpath)
	local curpointidx = readu32(game.curpoint) >> 8
	local curpoint = curpath + 0x32 + (curpointidx*12)
	return { x=reads16(curpoint+0), y=reads16(curpoint+2), z=reads16(curpoint+4) }	
end

function cam_get_dir()
	local curzone = readu32(game.curzone)
	local curpath = readu32(game.curpath)
	local curpointidx = readu32(game.curpoint) >> 8
	local curpathlen = readu16(curpath+0x1E)
	local nextzone = nil
	local nextpath = nil
	local curheader = readu32(curzone+0x10)
	local curpaths_idx = readu32(curheader+0x204)
	local neighborpathcount = readu32(curpath+8)
	for i=0,neighborpathcount-1 do
		local relation = readu8(curpath+0xC+(i*4))
		local zone_idx = readu8(curpath+0xD+(i*4))
		local path_idx = readu8(curpath+0xE+(i*4))
		local goal = readu8(curpath+0xF+(i*4))
		if relation == 2 and goal == 1 then
			local nextzoneeidptr = curheader+0x214+(zone_idx*4)
			nextzone = readu32(nextzoneeidptr)
			nextzone = readu32(nextzone)
			if (nextzone & 1) == 1 then
				printf("eid")
				nextzone = jal(0x80015A98, nextzoneeidptr)
			end
			local nextheader = readu32(nextzone+16)
			local nextpaths_idx = readu32(nextheader+0x204)
			
			printf(string.format("%i", path_idx))
			printf(string.format("%08X", readu32(nextzone+0x0)))
			nextpath = readu32(nextzone+0x10+((nextpaths_idx+path_idx)*4))
			printf(string.format("%08X", nextpath))
			break
		end
	end
		
	printf(string.format("curpathlen: %i", curpathlen))
	local curpoint = curpath + 0x32 + (curpointidx*12)
	local nextpoint = curpath + 0x32 + ((curpointidx+1)*12)
	if curpointidx+1 >= curpathlen-1 and not (nextpath == nil) then
		printf("at last")
		nextpoint = nextpath + 0x32
	end

	
	local dir = { x = reads16(nextpoint+0) - reads16(curpoint+0), 
	              y = reads16(nextpoint+2) - reads16(curpoint+2),
	              z = reads16(nextpoint+4) - reads16(curpoint+4) }

	nextzoneeid = readu32(nextzone+0x4)
	printf(string.format("next zone eid: %s", eidtoname(nextzoneeid)))
	
	if (not (curzone == nextzone)) and curpointidx+1 >= curpathlen-1 and not (nextpath == nil) then
		printf("change zone")
		curdim = readu32(curzone+0x14)
		nextdim = readu32(nextzone+0x14)
		curloc = { x=reads32(curdim+0), y=reads32(curdim+0x4), z=reads32(curdim+0x8) }
		nextloc = { x=reads32(nextdim+0), y=reads32(nextdim+0x4), z=reads32(nextdim+0x8) }
		dir.x = dir.x + nextloc.x - curloc.x
		dir.y = dir.y + nextloc.y - curloc.y
		dir.z = dir.z + nextloc.z - curloc.z
	end
	
	return dir
end

function cam_get_dir_rot(dir)
	local rot = { x = 0,
		      y = math.floor((math.atan(dir.x, dir.z)+math.pi)*2048/math.pi),
		      z = 0 }
	return rot
	
end
