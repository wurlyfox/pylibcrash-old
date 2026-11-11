require('scripts.gui')
require('scripts.util')
require('scripts.refl')

require('scripts.crash.ns')
require('scripts.crash.cam')
require('scripts.crash.geom')

require('scripts.gte')
require('scripts.crash.gool')

local rot_will = false
local m_rot = {}
local m_rot2 = {}
local m_rot3 = {}
local m_light1 = {}
local m_lrot = {}
local m_lrot2 = {}
local m_lrot1 = {}
local v_in1 = {}
local v_out1 = {}
local diffc = 0

local handles = 0x80060db8
local selobj = nil

trapexec(0x800188BC, function()
	obj = s4
	crash = readu32(game.crash)
	if obj ~= crash then
		return
	end
	rot_will = true
end)

trapexec(0x800188F4, function()
	obj = s4
	crash = readu32(game.crash)
	rot_will = false
	if obj ~= crash then
		return
	end

	m_rot = { {x = gte_reg("R11"), y = gte_reg("R12"), z = gte_reg("R13") },
	          {x = gte_reg("R21"), y = gte_reg("R22"), z = gte_reg("R23") },
	          {x = gte_reg("R31"), y = gte_reg("R32"), z = gte_reg("R33") } }
end)

trapexec(0x80039578, function()
	if rot_will == false then
		return
	end
	m_rot2 = { {x = s7, y = s1, z = s5},
	           {x = s3, y = t2, z = s2},
	           {x = t8, y = s6, z = t9} }
end)

trapexec(0x800395E4, function()
	if rot_will == false then
		return
	end
	m_rot3 = { {x = s7, y = s1, z = s5},
	           {x = s3, y = t2, z = s2},
	           {x = t8, y = s6, z = t9} }
end)

trapexec(0x80039990, function()
	if rot_will == false then
		return
	end
	m_lrot = { { x = s7, y = s1, z = s5 },
			   { x = s3, y = t2, z = s2 },
			   { x = t8, y = s6, z = t9 } }
end)

trapexec(0x80039A04, function()
	if rot_will == false then
		return
	end
	crash = readu32(game.crash)
	diffc = a3 - crash
	m_light1 = readmat16(a3)
	--crash = readu32(game.crash)
	--m_light1 = readmat16(crash+0x30)
end)

trapexec(0x80039A1C, function()
	if rot_will == false then
		return
	end
	m_lrot1 = { {x = gte_reg("R11"), y = gte_reg("R12"), z = gte_reg("R13") },
	            {x = gte_reg("R21"), y = gte_reg("R22"), z = gte_reg("R23") },
	            {x = gte_reg("R31"), y = gte_reg("R32"), z = gte_reg("R33") } }
	v_in1 = { x = s7, y = s1, z = s5 }
end)

trapexec(0x80039A58, function()
	if rot_will == false then
		return
	end
	v_out1 = { x = s7, y = s1, z = s5 }
end)

trapexec(0x80039AF0, function()
	if rot_will == false then
		return
	end
	m_lrot2 = { { x = s7, y = s1, z = s5 },
			    { x = s3, y = t2, z = s2 },
			    { x = t8, y = s6, z = t9 } }
end)

local handles_root = { addr=-1, handle={type=3} }
function updatehandlesroot()
    handles_root.children = {}
    for i=1,8 do
        obj = readobj(handles+((i-1)*8))
        table.insert(handles_root.children, obj)
    end
end

function objselect(obj)
    fn = function()
        selobj = obj
    end
    return fn
end

objstrfn = function(item)
    return objstr(item.data)
end

mapfn = function(obj, mchildren, path)
    item = Item:new { control = "node", data = obj, str = objstrfn, on_select = objselect(obj), children = mchildren }
    if obj.addr==-1 then item.control = "tree" end
    return item
end

function itemchildren(item)
    return item.children
end

function setitemchildren(item, children)
    item.children = children
end

function objaddr(obj)
    if obj==nil then return 0 end
    return obj.addr
end

function itemobjaddr(item)
    obj = item.data
    if obj==nil then return 0 end
    return obj.addr
end

function guirefltext(val)
    typename = val.field.type.name
    item = { control = "property", dtype = typename, addr = val.res }
    return item
end

function guirefllist(children)
    item = { control = "node", children = children }
    return item
end

function guireflvec(children)
    item = { control = "row", children = children }
    return item
end

function guireflvec16(children)
    item = { control = "row", children = children }
    return item
end

function guireflang(children)
    item = { control = "row", children = children }
    return item
end

function guiboxcolor(item)
    r = readu32(item.children[1].addr)
    g = readu32(item.children[2].addr)
    b = readu32(item.children[3].addr)
    color = { r=r, g=g, b=b }
    return color
end

function guiboxcolor16(item)
    r = readu16(item.children[1].addr)
    g = readu16(item.children[2].addr)
    b = readu16(item.children[3].addr)
    color = { r=r, g=g, b=b }
    return color
end

function guireflrgb8(children)
    item = { control="row", children = children }
    color = guiboxcolor(item)
    rgb = { control="rgb", r=color.r, g=color.g, b=color.b }
    table.append(item.children, rgb)
    return item
end

function guireflrgb16(children)
    item = { control="row", children = children }
    color = guiboxcolor16(item)
    rgb = { control="rgb", r=color.r, g=color.g, b=color.b }
    table.append(item.children, rgb)
    return item
end

function guireflmat16(children)
    item = { control="node", children = children }
    return item
end

function guireflbound(children)
    item = { control="node", children = children }
    return item
end

function guireflobjptr(val)
    item = { control="text", data=val.res, str=function(item) return objstr(readobj(item.data)) end }
    return item
end

function guimapobjfield(val, path, mapped)
    if val.field.name == "data" then return nil end
    if val.field.name == "regs" then return nil end
    if val.field.name == "colors_i" then return nil end
    label = 1
    children = mapped
    typename = val.field.type.name
    if val.field.is_pointer then
        if typename == "gool_object" then
            item = guireflobjptr(val)
        else
            return nil
        end
    elseif children == nil then
        item = guirefltext(val)
    elseif typename == "vec" then
        item = guireflvec(children)
    elseif typename == "vec16" then
        item = guireflvec16(children)
    elseif typename == "ang" then
        item = guireflang(children)
    elseif typename == "mat16" then
        item = guireflmat16(children)
    elseif typename == "rgb8" then
        item = guireflrgb8(children)
    elseif typename == "rgb16" then
        item = guireflrgb16(children)
    elseif typename == "bound" then
        item = guireflbound(children)
    else
        item = guirefllist(children)
    end
    if label == 1 then
        item.label = val.field.name
    end
    return item
end

function guiobjview(obj)
    view = Item:new { control="group" }
    if not (obj == nil) then
        gool_object_type = refl.get_type("gool_object")
        items = gool_object_type:map(obj, guimapobjfield)
        for i,it in ipairs(items) do
            view:add_child(it)
        end
    else
        it = Item:new { control="label", str="no object selected" }
        view:add_child(it)
    end
    bot = Item:new { control="label", data=obj, str=function(item) return objcodestr(item.data) end }
    view:add_child(bot)
    return view
end

function guiobjtree(obj, sel)
    item = treemap(obj, mapfn, objchildren)
    item.control = "tree"
    return item
end

local curobjtree = nil
local curobjview = nil
local prevobjtree = nil

guitool("Objects", function()

    --[[ if there is a previous iteration, flatten the previous
         items tree and index it by addresses of bound objects
         then map the current handles to a new tree such that
         for any objects which are at the same addresses as those
         of objects which were mapped to [node] items in the previous iteration,
         the items are re-used rather than created anew, and for all other
         objects, new [node] items are created. items are re-used so that
         state (i.e. selected) can be maintained between frames
         note that the table of child items for a re-used item will need to
         be replaced by the table of mapped children ]]--

    --local status, err = xpcall(function ()
        updatehandlesroot()
        replfn = treerepl(prevobjtree, mapfn, itemchildren, setitemchildren,
                          objaddr, itemobjaddr)
        curobjtree = treemap(handles_root, replfn, objchildren)
        prevobjtree = curobjtree
        curobjview = guiobjview(selobj)
        guidraw({curobjtree})
        guidraw({curobjview})
    --end, debug.traceback)
    --print(err)
end)

guitool("Debug", function()
	local prog = ra
	gui.label(tobinary(buttons))
	gui.label(string.format("pc: %8x", prog))

	gui.label(string.format("crash: %8X", readu32(game.crash)))
	gui.label(string.format("curlid: %8X", readu32(game.curlid)))
	gui.label(string.format("curzone: %8X", readu32(game.curzone)))
	gui.label(string.format("curpath: %8X", readu32(game.curpath)))
	gui.label(string.format("curprogress: %8X", readu32(game.curprogress)))

	gui.label(string.format("cam.transx: %8X", readu32(game.cam+0)))
	gui.label(string.format("cam.transy: %8X", readu32(game.cam+4)))
	gui.label(string.format("cam.transz: %8X", readu32(game.cam+8)))
	gui.label(string.format("cam.rotx: %8X", readu32(game.cam+12)))
	gui.label(string.format("cam.roty: %8X", readu32(game.cam+16)))
	gui.label(string.format("cam.rotz: %8X", readu32(game.cam+20)))
	gui.label(string.format("cam.scalex: %8X", readu32(game.cam+24)))
	gui.label(string.format("cam.scaley: %8X", readu32(game.cam+28)))
	gui.label(string.format("cam.scalez: %8X", readu32(game.cam+32)))

	local ldat = readu32(game.ldat)
	gui.label(string.format("ldat.magic: %8X", readu32(ldat+0)))
	gui.label(string.format("ldat.lid: %8X", readu32(ldat+4)))
	gui.label(string.format("ldat.zone_spawn: %8X", readu32(ldat+8)))
	gui.label(string.format("ldat.path_spawn: %8X", readu32(ldat+12)))

	-- gui.label(string.format("player: %8X", readu32(game.curlid)))

	crash = readu32(game.crash)
	crash_trans = readvec(crash+0x80)
	crash_rot = readvec(crash+0x8C)
	crash_scale = readvec(crash+0x98)
	crash_velocity = readvec(crash+0xA4)
	crash_light_mat = readmat16(crash+0x30)
	crash_color = readrgb16(crash+0x42)
	crash_color_mat = readmat16(crash+0x48)
	crash_intensity = readrgb16(crash+0x5A)
	mn_rot = readmat16(0x80057824)
	ms_rot = readmat16(0x80057844)
	gui.label(string.format("crash->trans.x: %8X", crash_trans.x))
	gui.label(string.format("crash->trans.y: %8X", crash_trans.y))
	gui.label(string.format("crash->trans.z: %8X", crash_trans.z))
	gui.label(string.format("crash->rot.x: %8X", crash_rot.x))
	gui.label(string.format("crash->rot.y: %8X", crash_rot.y))
	gui.label(string.format("crash->rot.z: %8X", crash_rot.z))
	gui.label(string.format("crash->scale.x: %8X", crash_scale.x))
	gui.label(string.format("crash->scale.y: %8X", crash_scale.y))
	gui.label(string.format("crash->scale.z: %8X", crash_scale.z))
	gui.label(string.format("crash->velocity.x: %8X", crash_velocity.x))
	gui.label(string.format("crash->velocity.y: %8X", crash_velocity.y))
	gui.label(string.format("crash->velocity.z: %8X", crash_velocity.z))
	gui.label(string.format("crash->light_mat: %s", mat_str(crash_light_mat)))
	gui.label(string.format("crash->color: %s", rgb_str(crash_color)))
	gui.label(string.format("crash->color_mat: %s", mat_str(crash_color_mat)))
	gui.label(string.format("crash->intensity: %s", rgb_str(crash_intensity)))
	gui.label(string.format("GTE R: %s", mat_str(m_rot)))
	gui.label(string.format("mn_rot: %s", mat_str(mn_rot)))
	gui.label(string.format("ms_rot: %s", mat_str(ms_rot)))
	gui.label(string.format("m_rot2: %s", mat_str(m_rot2)))
	gui.label(string.format("m_rot3: %s", mat_str(m_rot3)))
	gui.label(string.format("m_light1: %s", mat_str(m_light1)))
	gui.label(string.format("m_lrot: %s", mat_str(m_lrot)))
	gui.label(string.format("m_lrot2: %s", mat_str(m_lrot2)))
	gui.label(string.format("m_lrot1: %s", mat_str(m_lrot1)))
	gui.label(string.format("v_in1: %s", vec_str(v_in1)))
	gui.label(string.format("v_out1: %s", vec_str(v_out1)))
	gui.label(string.format("diffc: %i", diffc))
end)

guitool("Pages", function()
	for i = 0, 22 do
		local pstruct_p = game.page_structs + i * 44
		local page_p = readu32(pstruct_p)
		local page_type = readu16(page_p + 2)
		local page_id = readu32(page_p + 4)
		local state = readu16(pstruct_p+4)
		local field_6 = readu16(pstruct_p+6)
		local pte_index = readu16(pstruct_p+8)
		local entries_to_process = readu16(pstruct_p+10)
		local field_C = readu16(pstruct_p+12)
		local decompress = readu16(pstruct_p+14)
		local field_10 = readu32(pstruct_p+16)
		local pgid = readu32(pstruct_p+20)
		local eid = readu32(pstruct_p+24)
		local page_count = readu32(pstruct_p+28)
		local field_20 = readu32(pstruct_p+32)
		local link = readu32(pstruct_p+36)
		local timestamp = readu32(pstruct_p+40)
		local eidname = eidtoname(eid)
		if page_type == 1 then
			page_id = eidtoname(page_id)
		else
			page_id = string.format("%d", page_id)
		end
		gui.label(string.format("slot %2d: page T%d; id %s, state: %d, pte_index %d, ", i, page_type, page_id, state, pte_index))
		gui.label(string.format("to_process: %d, pgid: %d, eid %s, page_count: %d", entries_to_process, pgid, eidname, page_count))
	end
end)

guitool("Zone", function()
	local curlid = readu32(game.curlid)
	local curzone = readu32(game.curzone)
	local curpath = readu32(game.curpath)
	local curprogress = readu32(game.curprogress)
	local curzoneeid = readu32(curzone+4)
	gui.label(string.format("curlid: %8X", curlid))
	gui.label(string.format("curzone: %s", eidtoname(curzoneeid)))
	gui.label(string.format("curpath: %8X", curpath))
	gui.label(string.format("curprogress: %8X", curprogress))

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

	gui.label(string.format("curpathidx: %i", curpathidx))

	local neighbor_count = readu32(header+0x210)
	for i=0, neighbor_count-1 do
		local eid_or_zone = readu32(header+0x214+(i*4))
		local eid = 0
		local zone = 0
		if ((eid_or_zone & 1) == 1) then
			eid = eid_or_zone
		end
		if ((eid_or_zone & 1) == 0) then
			zone = eid_or_zone
			eid = readu32(zone+4)
		end
		local eidname = eidtoname(eid)
		gui.label(string.format("neighbor zone %i: %s", i, eidname))
	end

	local neighbor_path_count = readu32(curpath+8)
	for i=0, neighbor_path_count-1 do
		local goal = readu8(curpath+0xC+(i*4)+0)
		local zone_idx = readu8(curpath+0xC+(i*4)+1)
		local path_idx = readu8(curpath+0xC+(i*4)+2)
		local relation = readu8(curpath+0xC+(i*4)+3)

		local eid_or_zone = readu32(header+0x214+(zone_idx*4))
		local eid = 0
		local zone = 0
		if ((eid_or_zone & 1) == 1) then
			eid = eid_or_zone
		end
		if ((eid_or_zone & 1) == 0) then
			zone = eid_or_zone
			eid = readu32(zone+4)
		end
		local eidname = eidtoname(eid)
		local relstr = ""

		gui.label(string.format("neighbor path %i: %i, %i, %s path %i", i, relation, goal, eidname, path_idx))
	end
end)


guitool("Calculated", function()
	local loc = cam_get_loc()
	local dir = cam_get_dir()
	local rot = cam_get_dir_rot(dir)

	gui.label(string.format("path point x: %04x", loc.x))
	gui.label(string.format("path point y: %04x", loc.y))
	gui.label(string.format("path point z: %04x", loc.z))

	gui.label(string.format("cam x dir: %04x", dir.x))
	gui.label(string.format("cam y dir: %04x", dir.y))
	gui.label(string.format("cam z dir: %04x", dir.z))

	gui.label(string.format("cam dir rot x: %04x", rot.x))
	gui.label(string.format("cam dir rot y: %04x", rot.y))
	gui.label(string.format("cam dir rot z: %04x", rot.z))
end)

guitool("Edit", function()
	local curpath = readu32(game.curpath)

	local neighbor_path_count = readu32(curpath+8)
	local menu = {}

	guimenus_begin()
	for i=0, neighbor_path_count-1 do
		prefix = string.format("neighbor %i ", i+1)
		menu = {
			{ label = prefix .. "goal", address = curpath+0xC+(i*4)+0, type = "uint8" },
			{ label = prefix .. "zone_idx", address = curpath+0xC+(i*4)+1, type = "uint8" },
			{ label = prefix .. "path_idx", address = curpath+0xC+(i*4)+2, type = "uint8" },
			{ label = prefix .. "relation", address = curpath+0xC+(i*4)+3, type = "uint8" }
		}
		guimenu(menu)
	end

	menu = {
		{ label = "entrance", address = curpath+0x1C, type = "uint8" },
		{ label = "exit", address = curpath+0x1D, type = "uint8" },
		{ label = "avg_node_dist", address = curpath+0x22, type = "uint16" },
		{ label = "cam_zoom", address = curpath+0x24, type = "uint16" },
		{ label = "direction_x", address = curpath+0x2C, type = "int16" },
		{ label = "direction_y", address = curpath+0x2E, type = "int16" },
		{ label = "direction_z", address = curpath+0x30, type = "int16" }
	}
	guimenu(menu)
	guimenus_end()
end)

guitool("Gpu", function()
    local tickselapsed=readu32(0x80034520)
    local drawcount=readu32(0x80057960)
    local context1=readu32(0x80058404)
    local context2=readu32(0x80058408)
    local curctxt = readu32(0x8005840C)
    local drawstamp1=readu32(context1+0x7C)
    local syncstamp1=readu32(context1+0x80)
    local tpf1 = readu32(context1+0x84)
    local drawstamp2=readu32(context2+0x7C)
    local syncstamp2=readu32(context2+0x80)
    local tpf2 = readu32(context2+0x84)
    local frameselapsed = readu32(0x80060e04)
    gui.label(string.format("ticks elapsed: %i", tickselapsed))
    gui.label(string.format("draw count: %i", context1))
    gui.label(string.format("context 1: %08X", context1))
    gui.label(string.format("context 2: %08X", context2))
    gui.label(string.format("context cur: %08X", curctxt))
    gui.label("context 1:")
    gui.label(string.format("draw stamp: %i", drawstamp1))
    gui.label(string.format("sync stamp: %i", syncstamp1))
    gui.label(string.format("ticks per frame: %i", tpf1))
    gui.label("context 2:")
    gui.label(string.format("draw stamp: %i", drawstamp2))
    gui.label(string.format("sync stamp: %i", syncstamp2))
    gui.label(string.format("ticks per frame: %i", tpf2))
    gui.label(string.format("frames elapsed: %i", frameselapsed))
end)
