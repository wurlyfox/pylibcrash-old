
local poly_z2 = 0

local m_cam_rot = {{},{},{}}
local ms_cam_rot = {{},{},{}}
local u_viewmodel = {}
local r_viewmodel = {}
local u_poly = {{},{},{}}
local v_poly = {{},{},{}}
local r_poly = {{},{},{}}
local s_poly = {{},{},{}}

require "scripts.gte"
require "scripts.util"
require "scripts.gui"

require "scripts.crash.geom"
require "scripts.crash.zone"

local do_menus = false
local do_wgeo_log = false
local do_tgeo_log = false
local do_poly_id_log = false
local do_cvtx_log = true

function idiv(idx,val)
	return ((idx-1)//val)+1
end
function imod(idx,val)
	return ((idx-1)%val)+1
end


if do_wgeo_log then

local poly_id = -1
local poly_map = {}
local mat_map = {}

trapexec(0x80017AB0, function()
	zpp = getzpp()
	mat = readmat16(0x800577C4)
	path_set(mat_map, mat, zpp.zoneeidstr, zpp.pathidx, zpp.pt, 1)
end)

trapexec(0x80017B04, function()
	zpp = getzpp()
	mat = readmat16(0x800577C4)
	path_set(mat_map, mat, zpp.zoneeidstr, zpp.pathidx, zpp.pt, 2)
end)

trapexec(0x80017B60, function()
	zpp = getzpp()
	mat = readmat16(0x800577C4)
	path_set(mat_map, mat, zpp.zoneeidstr, zpp.pathidx, zpp.pt, 3)
end)

trapexec(0x80017C8C, function()
	zpp = getzpp()
	mat = readmat16(0x800577E4)
	path_set(mat_map, mat, zpp.zoneeidstr, zpp.pathidx, zpp.pt, 4)
end)


trapexec(0x800354CC, function()
	poly_id = at & 0xFFFF
end)

trapexec(0x800354F4, function()
	u_viewmodel.x = readu32(v0+4)
	u_viewmodel.y = readu32(v0+8)
	u_viewmodel.z = readu32(v0+12)
end)

trapexec(0x8003557C, function()
	u_poly[1].xy = sp
	u_poly[2].xy = s1 & at
	u_poly[3].xy = ra
end)

trapexec(0x800355F4, function()
	u_poly[1].z = sp
	u_poly[2].z = 0   -- for now
	u_poly[3].z = ra
end)

trapexec(0x80035748, function()
	s_poly[1].z = sp
end)

function parse_gte_rtpt_log()
	i = 1
	verts = {}
	regs = {'MAC1','MAC2','MAC3','IR1','IR2','IR3','SZ0','SZ1','SZ2','SZ3','h_over_sz3','SXY0','SXY1','SX2','SY2'}
	lines = {}
	for line in io.lines("gte_rtpt.txt") do
		lines[i] = line
		i = i + 1
	end
	for i=1,3 do
		verts[i] = {}
		line = lines[i]
		values = split(line, ",")
		for j=1,15 do
			verts[i][regs[j]] = tonumber(values[j])
		end
	end
	return verts
end

trapexec(0x8003574C, function()
	printf("%i,%i", gte_reg("OFX"), gte_reg("OFY"))

	r_viewmodel.x = gte_reg("TRX")
	r_viewmodel.y = gte_reg("TRY")
	r_viewmodel.z = gte_reg("TRZ")

	verts = parse_gte_rtpt_log()
	for i=1,3 do
		v_poly[i].x = verts[i]['MAC1']
		v_poly[i].y = verts[i]['MAC2']
		v_poly[i].z = verts[i]['MAC3']

		r_poly[i].x = v_poly[i].x - (r_viewmodel.x << 12)
		r_poly[i].y = v_poly[i].y - (r_viewmodel.y << 12)
		r_poly[i].z = v_poly[i].z - (r_viewmodel.z << 12)
	end

	cam_trans = readvec(game.cam+0)
	cam_rot = readvec(game.cam+12)
	-- ms_cam_rot[1].x = gte_reg("R11")
	-- ms_cam_rot[1].y = gte_reg("R12")
	-- ms_cam_rot[2].x = gte_reg("R21")
	-- ms_cam_rot[1].z = gte_reg("R13")
	-- ms_cam_rot[2].y = gte_reg("R22")
	-- ms_cam_rot[2].z = gte_reg("R23")
	-- ms_cam_rot[3].x = gte_reg("R31")
	-- ms_cam_rot[3].y = gte_reg("R32")
	-- ms_cam_rot[3].z = gte_reg("R33")

	local prim = t3
	s_poly[1].xy = readu32(prim + 0x8)
	s_poly[2].xy = readu32(prim + 0x14)
	s_poly[3].xy = readu32(prim + 0x20)

	s_poly[1].z = s_poly[1].z
	s_poly[2].z = sp - s_poly[1].z
	s_poly[3].z = ra

	zpp = getzpp()
	poly = path_set(poly_map, {{},{},{}}, zpp.zoneeidstr, zpp.pathidx, zpp.pt, poly_id)
	for i=1,3 do
		s_poly[i].x = s_poly[i].xy & 0xFFFF
		s_poly[i].y = (s_poly[i].xy & 0xFFFF0000) >> 16

		u_poly[i].x = u_poly[i].xy & 0xFFFF
		u_poly[i].y = (u_poly[i].xy & 0xFFFF0000) >> 16

		poly[i].ct = vec_copy(cam_trans)
		poly[i].cr = vec_copy(cam_rot)
		poly[i].mscr = mat_copy(ms_cam_rot)
		poly[i].uvm = vec_copy(u_viewmodel)
		poly[i].rvm = vec_copy(r_viewmodel)
		poly[i].u = vec_copy(u_poly[i])
		poly[i].r = vec_copy(r_poly[i])
		poly[i].v = vec_copy(v_poly[i])
		poly[i].s = vec_copy(s_poly[i])
	end
end)

local function write_wgeo(menu_idx, item_idx)
	pathidx = -1
	file = io.open("output.csv", "w")
	key_cols = {"zone","path","path_pt","poly_id","vert_idx"}
	vec_cols = add_tables(--vec_csv_cols("cam_trans"), vec_csv_cols("cam_rot"),
			      --mat_csv_cols("m_cam_rot"), mat_csv_cols("ms_cam_rot"),
			      vec_csv_cols("u_viewmodel"), vec_csv_cols("r_viewmodel"))
	vert_cols = add_tables(vec_csv_cols("w_vert"), vec_csv_cols("u_vert"),
			      vec_csv_cols("r_vert"), vec_csv_cols("v_vert"),
			      vec_csv_cols("s_vert"))
	all_cols = add_tables(key_cols, vec_cols, vert_cols)
	cols = table.concat(all_cols, ",")

	file:write(cols.."\n")

	local zero_pt = {x=0,y=0,z=0}
	local zero_mat = {zero_pt,zero_pt,zero_pt}
	for zoneeidstr, poly_zone_map in pairs(poly_map) do
		for path, poly_path_map in pairs(poly_zone_map) do
			for pt, poly_pt_map in pairs(poly_path_map) do
				for poly_id, poly in pairs(poly_pt_map) do
					tag = string.format("%s,%i,%i,%04X", zoneeidstr, path, pt, poly_id)
					for i=1,3 do
						vert_tag = string.format("%s,%i", tag, i)
						-- cam_trans_str = vec_csv_str(poly[i].ct)
						-- cam_rot_str = vec_csv_str(poly[i].cr)
						-- m_cam_rot_str = mat_csv_str(zero_mat)
						-- ms_cam_rot_str = mat_csv_str(poly[i].mscr)
						u_viewmodel_str = vec_csv_str(poly[i].uvm)
						r_viewmodel_str = vec_csv_str(poly[i].rvm)
						w_vert_str = vec_csv_str(zero_pt)
						u_vert_str = vec_csv_str(poly[i].u)
						r_vert_str = vec_csv_str(poly[i].r)
						v_vert_str = vec_csv_str(poly[i].v)
						s_vert_str = vec_csv_str(poly[i].s)
						vecs_str = string.format("%s,%s,%s,%s,%s,%s", cam_trans_str,
							cam_rot_str, m_cam_rot_str, ms_cam_rot_str, u_viewmodel_str,
							r_viewmodel_str)
						verts_str = string.format("%s,%s,%s,%s,%s", w_vert_str, u_vert_str,
							r_vert_str, v_vert_str, s_vert_str)
						line = string.format("%s,%s,%s", vert_tag, vecs_str, verts_str)
						file:write(line.."\n")
					end
				end
			end
		end
	end
	file:close()

	file = io.open("output_mat.csv", "w")
	key_cols = {"zone", "path", "path_pt, mat_idx"}
	all_cols = add_tables(key_cols, mat_csv_cols("mat"))
	cols = table.concat(all_cols, ",")
	file:write(cols.."\n")
	for zoneeidstr, mat_zone_map in pairs(mat_map) do
		for path, mat_path_map in pairs(mat_zone_map) do
			for pt, mat_vec_map in pairs(mat_path_map) do
				for mat_idx, mat in pairs(mat_vec_map) do
					tag = string.format("%s,%i,%i,%i", zoneeidstr, path, pt, mat_idx)
					line = string.format("%s,%s", tag, mat_csv_str(mat))
					file:write(line.."\n")
				end
			end
		end
	end
	file:close()
end
end -- do_wgeo_log

if do_tgeo_log then

local frame_map = {}

local function is_crash(obj)
	ptr = readu32(obj+0x20)
	global = readentry(ptr)
	if global.name == 'WillC' then
		return true
	end
	return false
end

local crash_trans_once = false
local crash_transpull_once = false
local tr = {}
local pidx = -1
trapexec(0x8001AD5C, function()
	tr = readvec16(a0)
	pidx = s0
end)
trapexec(0x8001ADA4, function()
	if crash_trans_once == true then
		return
	end
	obj = s2
	if not is_crash(obj) then
		return
	end
	trans = readvec(s3)
	global = readentry(obj)

	printf("setting crash init trans to %s", vec_str(trans))
	printf("from init path pt %s", vec_str(tr))
	printf("and progress index %i", pidx)
	crash_trans_once = true
end)

trapexec(0x8002C2C4, function()
	if crash_transpull_once == true then
		return
	end
	obj = s3
	if not is_crash(obj) then
		return
	end
	velocity = readvec(s0)

	printf("TransPullStopAtSolid velocity: %s", vec_str(velocity))
end)

trapexec(0x8002C328, function()
	if crash_transpull_once == true then
		return
	end
	obj = s3
	if not is_crash(obj) then
		return
	end
	crash_transpull_once = true
	delta_trans = readvec(sp+0x18)
	printf("TransPullStopAtSolid delta_trans: %s", vec_str(delta_trans))
end)

trapexec(0x80037E38, function()
	printf("results: %i\n", v0)
end)

trapexec(0x80038450, function()
	nrectdim = { x=s0, y=s1, z=s2 }
	printf("nrect.dim: %s\n", vec_str(nrectdim))
	printf("comparing mid.x: %i < 0, result: %i", at, v0)
    printf("comparing nodes_dim.x < mid.x: %i < %i", t2, at)
end)

trapexec(0x80038460, function()
	printf("result: %i", at)
end)

trapexec(0x80038474, function()
	printf("comparing mid.y: %i < 0, result: %i", at, v0)
    printf("comparing nodes_dim.y < mid.y: %i < %i", t3, at)
end)

trapexec(0x80038484, function()
	printf("result: %i", at)
end)

trapexec(0x80038498, function()
	printf("comparing mid.z: %i < 0, result: %i", at, v0)
    printf("comparing nodes_dim.z < mid.z: %i < %i", t4, at)
end)

trapexec(0x800384A8, function()
	printf("result: %i", at)
end)

trapexec(0x800384B8, function()
	printf("flags: %08X\n", ra)
end)

trapexec(0x80029540, function()
	bound = readbound(s0+0x1008)
	printf("querying octrees\n")
	printf("using bound: %s\n", bound_str(bound))
	vec = readvec(a0)
	printf("and vec: %s\n", vec_str(vec))
end)

trapexec(0x80018194, function()
	obj = a2
	if not is_crash(obj) then
		return
	end
	velocity = readvec(obj+0xA4)
	u_trans = readvec16(sp+0x10)
	r_trans = readvec(sp+0x2C)
	draw_count = readu32(0x80057960)

	path_set(frame_map, u_trans, draw_count, "WillC", "u_trans")
	path_set(frame_map, r_trans, draw_count, "WillC", "r_trans")
end)

can_trap = false
trapexec(0x800188AC, function()
	obj = a2
	ptr = readu32(obj+0x20)
	global = readentry(ptr)
	if not global.name == 'WillC' then
		return
	end
	mn_rot = readmat16(0x80057824)
	draw_count = readu32(0x80057960)
	path_set(frame_map, mn_rot, draw_count, "WillC", "mn_rot")
	can_trap = true
end)

trapexec(0x800188F8, function()
	can_trap = false
end)

trapexec(0x80039660, function()
	if can_trap == false then
		return
	end
	m_rot = {{},{},{}}
	m_rot[1].x = gte_reg("R11")
	m_rot[1].y = gte_reg("R12")
	m_rot[1].z = gte_reg("R13")
	m_rot[2].x = gte_reg("R21")
	m_rot[2].y = gte_reg("R22")
	m_rot[2].z = gte_reg("R23")
	m_rot[3].x = gte_reg("R31")
	m_rot[3].y = gte_reg("R32")
	m_rot[3].z = gte_reg("R33")
	draw_count = readu32(0x80057960)
	path_set(frame_map, m_rot, draw_count, "WillC", "m_rot")
end)

function write_tgeo(menu_idx, item_idx)
	file = io.open("output_tgeo.csv", "w")
	key_cols = {"entry", "draw_count"}
	vec_cols = add_tables(vec_csv_cols("u_trans"), vec_csv_cols("r_trans"))
	mat_cols = add_tables(mat_csv_cols("mn_rot"), mat_csv_cols("m_rot"))
	all_cols = add_tables(key_cols, vec_cols, mat_csv_cols)
	cols = table.concat(all_cols, ",")
	file:write(cols.."\n")
	for draw_count, entry_map in pairs(frame_map) do
		for gooleidstr, item_map in pairs(entry_map) do
			u_trans = item_map['u_trans']
			r_trans = item_map['r_trans']
			mn_rot = item_map['mn_rot']
			m_rot = item_map['m_rot']
			tag = string.format("%s,%i", gooleidstr, draw_count)
			line = string.format("%s,%s,%s,%s,%s", tag, vec_csv_str(u_trans),
				vec_csv_str(r_trans), mat_csv_str(mn_rot), mat_csv_str(m_rot))
			file:write(line.."\n")
		end
	end
	file:close()
end
end -- do_tgeo_log

if do_poly_id_log then

local poly_id_map = {}
poly_ids = {}
trapexec(0x80029b78, function()
	buf = readu32(gp+0x304)
	count = readu16(buf+0)
	poly_ids2 = {}
	for i=0,count-1 do
		poly_ids[i+1] = readu16(buf+(i+2)*2)
        poly_ids2[i+1] = readu16(buf+(i+2)*2)
	end
	zpp = getzpp()
	path_set(poly_id_map, poly_ids2, zpp.zoneeidstr, zpp.pathidx, zpp.pt)
end)

guitool("POLYIDS", function()
	str = ""
	for i,v in ipairs(poly_ids) do
		if i%16 == 15 then
			str = str..string.format("%04X",v)
			gui.label(str)
			str = ""
		else
			str = str..string.format("%04X, ",v)
		end
	end
end)

function write_poly_ids(menu_idx, item_idx)
	file = io.open("output_poly_ids.csv", "w")
	all_cols = {"entry", "path idx", "pt idx", "poly ids"}
	cols = table.concat(all_cols, ",")
	file:write(cols.."\n")

    for zoneeidstr, poly_id_path_map in pairs(poly_id_map) do
		for path, poly_id_pt_map in pairs(poly_id_path_map) do
			for pt, poly_ids_list in pairs(poly_id_pt_map) do
                line = ""
                poly_id_strs = {}
                for idx,poly_id in ipairs(poly_ids_list) do
                    poly_id_strs[idx] = string.format("%04X", poly_id)
                end
                tag = string.format("%s,%i,%i", zoneeidstr, path, pt)
                line = tag..",\""..table.concat(poly_id_strs, ",").."\""
                file:write(line.."\n")
            end
        end
    end
	file:close()
end
end -- do_poly_id_log

if do_cvtx_log then

local frame_map = {}

local function map_poly(frame_idx, idx, u_poly, r_poly)
    local poly=nil
    local poly_map=nil
    if frame_map[frame_idx]==nil then
        frame_map[frame_idx] = {}
    end
    frame = frame_map[frame_idx]
    if frame.poly_map == nil then
        frame.poly_map = {}
    end
    poly_map = frame.poly_map
    if poly_map[idx]==nil then
        poly_map[idx] = {}
    end
    poly = poly_map[idx]
    for vert_idx, vert in pairs(u_poly) do
        if poly[vert_idx]==nil then poly[vert_idx]={} end
        poly[vert_idx].u_trans = vert
    end
    for vert_idx, vert in pairs(r_poly) do
        if poly[vert_idx]==nil then poly[vert_idx]={} end
        vert.z = -1
        poly[vert_idx].r_trans = vert
    end
end

local function is_titleobj(obj)
	local obj = objoraddrtoobj(obj)
    if obj.anim_seq == 0 then return false end
    eid = readu32(obj.anim_seq + 4)
    eid = geteidorentryeid(eid)
	if eidtoname(eid)=='Lo1pV' then
        return true
    end
	return false
end

local is_title = false
local frame_idx = -1
local poly_count = -1
trapexec(0x8001E1D4, function()
    local obj=s4
    is_title = is_titleobj(obj)
    if not is_title then return end
    obj = objoraddrtoobj(obj)
    frame_idx = obj.anim_frame >> 8
    m_rot = {{},{},{}}
	m_rot[1].x = gte_reg("R11")
	m_rot[1].y = gte_reg("R12")
	m_rot[1].z = gte_reg("R13")
	m_rot[2].x = gte_reg("R21")
	m_rot[2].y = gte_reg("R22")
	m_rot[2].z = gte_reg("R23")
	m_rot[3].x = gte_reg("R31")
	m_rot[3].y = gte_reg("R32")
	m_rot[3].z = gte_reg("R33")
    if frame_map[frame_idx] == nil then
        frame_map[frame_idx] = {}
    end
    frame_map[frame_idx].m_rot = m_rot
end)
trapexec(0x80034BD4, function()
    if not is_title then return end
    vert_count = t5
end)
trapexec(0x80034C4C, function()
    if not is_title then return end
    u_poly[1].x = s8 & 0xFFFF
    u_poly[1].y = (s8 >> 16) & 0xFFFF
    u_poly[1].z = sp & 0xFFFF
end)
trapexec(0x80034C88, function()
    if not is_title then return end
    u_poly[2].x = s8 & 0xFFFF
    u_poly[2].y = (s8 >> 16) & 0xFFFF
    u_poly[2].z = sp & 0xFFFF
end)
trapexec(0x80034CC4, function()
    if not is_title then return end
    u_poly[3].x = s8 & 0xFFFF
    u_poly[3].y = (s8 >> 16) & 0xFFFF
    u_poly[3].z = sp & 0xFFFF
end)
trapexec(0x80034F14, function()
    if not is_title then return end
    prim=a3
    r_poly[1].x = readu32(prim+8) & 0xFFFF
    r_poly[1].y = (readu32(prim+8) >> 16) & 0xFFFF
    r_poly[2].x = readu32(prim+0x14) & 0xFFFF
    r_poly[2].y = (readu32(prim+0x14) >> 16) & 0xFFFF
    r_poly[3].x = readu32(prim+0x20) & 0xFFFF
    r_poly[3].y = (readu32(prim+0x20) >> 16) & 0xFFFF
    idx = t5-poly_count
    map_poly(frame_idx, idx, u_poly, r_poly)
end)
trapexec(0x80035074, function()
    if not is_title then return end
    prim=a3
    r_poly[1].x = readu32(prim+8) & 0xFFFF
    r_poly[1].y = (readu32(prim+8) >> 16) & 0xFFFF
    r_poly[2].x = readu32(prim+0x10) & 0xFFFF
    r_poly[2].y = (readu32(prim+0x10) >> 16) & 0xFFFF
    r_poly[3].x = readu32(prim+0x18) & 0xFFFF
    r_poly[3].y = (readu32(prim+0x18) >> 16) & 0xFFFF
    map_poly(frame_idx, idx, u_poly, r_poly)
end)
trapexec(0x80035140, function()
    is_title=false
end)

function write_cvtx(menu_idx, item_idx)
	local poly_map = nil
	local poly = nil
	local vert = nil
	file = io.open("output_cvtx.csv", "w")
	key_cols = {"frame_idx", "poly_idx", "vert_idx"}
	mat_cols = mat_csv_cols("m_rot")
	vec_cols = add_tables(vec_csv_cols("u_trans"), vec_csv_cols("r_trans"))
	all_cols = add_tables(key_cols, mat_cols, vec_cols)
	cols = table.concat(all_cols, ",")
	file:write(cols.."\n")
	print("here")
	for frame_idx, frame in pairs(frame_map) do
		poly_map = frame.poly_map
		m_rot = frame.m_rot
		print(luastr(poly_map), luastr(m_rot))
		for poly_idx, poly in pairs(poly_map) do
			for vert_idx, vert in ipairs(poly) do
                u_trans = vert.u_trans
                r_trans = vert.r_trans
                tag = string.format("%i,%i,%i", frame_idx, poly_idx, vert_idx)
                line = string.format("%s,%s,%s,%s", tag, mat_csv_str(m_rot),
                    vec_csv_str(u_trans), vec_csv_str(r_trans))
                file:write(line.."\n")
            end
		end
	end
	file:close()
end
end -- do_cvtx_log


guitool("Polys", function()
	local menu = Item:new{ control="group" }
	local btn = nil

	if do_wgeo_log then
        btn = Item:new{ control = "button", fn = write_wgeo, str = "write wgeo polys" }
        menu:add_child(btn)
	end
	if do_tgeo_log then
		btn = Item:new{ control = "button", fn = write_tgeo, str = "write tgeo info" }
		menu:add_child(btn)
	end
	if do_poly_id_log then
        btn = Item:new{ control = "button", fn = write_poly_ids, str = "write poly ids" }
        menu:add_child(btn)
    end
    if do_cvtx_log then
        btn = Item:new{ control = "button", fn = write_cvtx, str = "write cvtx polys" }
        menu:add_child(btn)
    end
	menu:draw()
end)

if do_menus then

guitool("Wall Map", function()
    local wall_map = 0x1F800100
    local cvt_wall_map = {}

    for i=1,32 do
        line = readu32(wall_map+(i-1)*4)
        cvt_wall_map[i] = {}
        for j=1,32 do
            if line & 1 == 1 then
                cvt_wall_map[i][33-j] = "X"
            else
                cvt_wall_map[i][33-j] = " "
            end
            line = line >> 1
        end
    end

    for i=1,32 do
        line = table.concat(cvt_wall_map[i], "")
        gui.label(line)
    end
end)

guitool("GTE", function()
	h = gte_reg("H")
	gui.label(string.format("GTE.H: %i", h))
end)

zone_query_once = false
trapexec(0x80037DD4, function()
    if zone_query_once == true then
        return
    end
    zone_query_once = true
    bound = readbound(a1)
    printf("%s", bound_str(bound))
end)

end
