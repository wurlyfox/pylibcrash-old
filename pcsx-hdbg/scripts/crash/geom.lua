function vec_copy(vec)
	return { x=vec.x, y=vec.y, z=vec.z }
end

function rgb_copy(rgb)
	return { r=rgb.r, g=rgb.g, b=rgb.b }
end

function mat_copy(mat)
	res = {{},{},{}}
	res[1] = vec_copy(mat[1])
	res[2] = vec_copy(mat[2])
	res[3] = vec_copy(mat[3])
	return res
end

function vec_str(vec)
	return string.format("(%i, %i, %i)", vec.x, vec.y, vec.z)
end

function rgb_str(rgb)
	return string.format("(%i, %i, %i)", rgb.r, rgb.g, rgb.b)
end

function mat_str(mat)
	str = ""
	for i=1,3 do
		str = str .. string.format("[%i, %i, %i]\n", mat[i].x, mat[i].y, mat[i].z)
	end
	return str
end

function bound_str(bound)
	return vec_str(bound.p1) .. "-" .. vec_str(bound.p2)
end

function vec_csv_str(vec)
	if vec == nil or vec.x == nil then
		printf("nil value at line: %s", debug.getinfo(2).currentline)
	end
	return string.format("%i,%i,%i", vec.x, vec.y, vec.z)
end

function rgb_csv_str(rgb)
	if rgb == nil or rgb.r == nil then
		printf("nil value at line: %s", debug.getinfo(2).currentline)
	end
	return string.format("%i,%i,%i", rgb.r, rgb.g, rgb.b)
end

function mat_csv_str(mat)
	return vec_csv_str(mat[1]) .. "," .. vec_csv_str(mat[2]) .. "," .. vec_csv_str(mat[3])
end

function bound_csv_str(bound)
	return vec_csv_str(bound.p1) .. "," .. vec_csv_str(bound.p2)
end

-- for csv output
function vec_csv_cols(vec)
	return {vec..".x", vec..".y", vec..".z"}
end

function rgb_csv_cols(rgb)
	return {rgb..".r", rgb..".b", rgb..".b"}
end

function mat_csv_cols(mat)
	return {mat.."[0].x", mat.."[0].y", mat.."[0].z",
	        mat.."[1].x", mat.."[1].y", mat.."[1].z",
	        mat.."[2].x", mat.."[2].y", mat.."[2].z"}
end

function bound_csv_cols(bound)
	return {bound.."p1.x", bound.."p1.y", bound.."p1.z",
	        bound.."p2.x", bound.."p2.y", bound.."p2.z"}
end

function readvec(addr)
	local vec = {}
	vec.x = reads32(addr+0)
	vec.y = reads32(addr+4)
	vec.z = reads32(addr+8)
	return vec
end
	
function readvec16(addr)
	local vec = {}
	vec.x = reads16(addr+0)
	vec.y = reads16(addr+2)
	vec.z = reads16(addr+4)
	return vec
end

function readrgb(addr)
	local rgb = {}
	rgb.r = readu32(addr+0)
	rgb.g = readu32(addr+4)
	rgb.b = readu32(addr+8)
	return rgb
end

function readrgb16(addr)
	local rgb = {}
	rgb.r = readu16(addr+0)
	rgb.g = readu16(addr+2)
	rgb.b = readu16(addr+4)
	return rgb
end

function readrgb8(addr)
	local rgb = {}
	rgb.r = readu8(addr+0)
	rgb.g = readu8(addr+1)
	rgb.b = readu8(addr+2)
	return rgb
end

function readmat16(addr)
	local mat = {{},{},{}}
	for i=1,3 do
		mat[i] = readvec16(addr+((i-1)*6))
	end
	return mat
end

function readbound(addr)
	local bound = {}
	bound.p1 = readvec(addr+0)
	bound.p2 = readvec(addr+12)
	return bound
end

