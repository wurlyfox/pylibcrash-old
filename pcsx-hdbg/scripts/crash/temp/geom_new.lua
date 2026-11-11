function Vec:new(v)
	v = v or {}
	setmetatable(v, self)
	self.__index = self
	return v
end

function Vec:copy(v)
	self.x = v.x
	self.y = v.y
	self.z = v.z
end

function Vec:__tostring(v)
	return string.format("(%i, %i, %i)", v.x, v.y, v.z)
end

function Vec:csv_str(v)
	if v == nil or v.x == nil then
		printf("nil value at line: %s", debug.getinfo(2).currentline)
	end
	return string.format("%i,%i,%i", v.x, v.y, v.z)
end

function Vec:csv_cols(v, name)
	return {name..".x", name..".y", name..".z"}
end

function Vec:read(addr)
	v = Vec:new({ x = reads32(addr+0), 
				  y = reads32(addr+4), 
				  z = reads32(addr+8) })
	return v
end

function Vec:read16(addr)
	v = Vec:new({ x = reads16(addr+0), 
				  y = reads16(addr+2), 
				  z = reads16(addr+4) })
	return v
end

function Mat:new(m)
	v = v or {}
	setmetatable(v, self)
	self.__index = self
	return v
end

function Mat:copy(m)
	self[1] = Vec:copy(m[1])
	self[2] = Vec:copy(m[2])
	self[3] = Vec:copy(m[3])
end
