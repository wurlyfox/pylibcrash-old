require "scripts.crash.geom"
require "scripts.crash.ns"

--local handles = 0x80060db8
function readhandle(addr)
	handle = {}
	handle.type = readu32(addr+0)
	handle.children = readu32(addr+4)
	return handle
end

function readcolors(addr)
	colors = {}
	colors.light_mat = readmat16(addr+0)
	colors.color = readrgb16(addr+0x12)
	colors.color_mat = readmat16(addr+0x18)
	colors.intensity = readrgb16(addr+0x2A)
	return colors
end

function readobj(addr)
	obj = {}
	obj.addr = addr
	obj.handle = readhandle(addr)
	if obj.handle.type == 2 then
        obj.children = obj.handle.children
        return obj
    end
	obj.bound = readbound(addr+0x8)
	global = readu32(addr+0x20)
	if global ~= 0 then
		obj.global = readentry(global)
	else
		obj.global = nil
	end
	external = readu32(addr+0x24)
	if external ~= 0 then
		obj.external = readentry(external)
	else
		obj.external = nil
	end
	zone = readu32(addr+0x28)
	if zone ~= 0 then
		obj.zone = readentry(zone)
	else
		obj.zone = nil
	end
	obj.state = readu32(addr+0x2C)
	obj.colors = readcolors(addr+0x30)
	obj.self = readu32(addr+0x60)
	obj.parent = readu32(addr+0x64)
	obj.sibling = readu32(addr+0x68)
	obj.children = readu32(addr+0x6C)
	obj.creator = readu32(addr+0x70)
	obj.player = readu32(addr+0x74)
	obj.collider = readu32(addr+0x78)
	obj.interrupter = readu32(addr+0x7C)
	obj.trans = readvec(addr+0x80)
	obj.rot = readvec(addr+0x8C)
	obj.scale = readvec(addr+0x98)
	obj.velocity = readvec(addr+0xA4)
	obj.misc_b = readvec(addr+0xB0)
	obj.misc_c = readvec(addr+0xBC)
	obj.status_a = readu32(addr+0xC8)
	obj.status_b = readu32(addr+0xCC)
	obj.status_c = readu32(addr+0xD0)
	obj.subtype = readu32(addr+0xD4)
	obj.pid_flags = readu32(addr+0xD8)
	obj.sp = readu32(addr+0xDC)
	obj.pc = readu32(addr+0xE0)
	obj.fp = readu32(addr+0xE4)
	obj.tp = readu32(addr+0xE8)
	obj.ep = readu32(addr+0xEC)
	obj.once_p = readu32(addr+0xF0)
	obj.misc = readu32(addr+0xF4)
	obj.ack = readu32(addr+0xF8)
	obj.anim_stamp = readu32(addr+0xFC)
	obj.state_stamp = readu32(addr+0x100)
	obj.anim_counter = readu32(addr+0x104)
	obj.anim_seq = readu32(addr+0x108)
	obj.anim_frame = readu32(addr+0x10C)
	obj.entity = readu32(addr+0x110)
	obj.path_progress = reads32(addr+0x114)
	obj.path_length = readu32(addr+0x118)
	obj.floor_y = readu32(addr+0x11C)
	obj.state_flags = readu32(addr+0x120)
	obj.speed = reads32(addr+0x124)
	obj.invincibility_state = readu32(addr+0x128)
	obj.invincibility_stamp = readu32(addr+0x12C)
	obj.floor_impact_stamp = readu32(addr+0x130)
	obj.floor_impact_velocity = reads32(addr+0x134)
	obj.size = readu32(addr+0x138)
	obj.event = readu32(addr+0x13C)
	obj.cam_zoom = reads32(addr+0x140)
	obj.ang_velocity_y = reads32(addr+0x144)
	obj.hotspot_size = reads32(addr+0x148)
	obj.voice_id = readu32(addr+0x14C)
	obj._150 = readu32(addr+0x150)
	obj._154 = readu32(addr+0x154)
	obj.node = readu32(addr+0x158)
	obj.memory = {}
	for i=1,64 do
		obj.memory[i] = readu32(addr+0x15C+((i-1)*4))
	end
	return obj
end

function objoraddrtoobj(objoraddr)
    obj = objoraddr
    if type(objoraddr) == "number" then
        if objoraddr == 0 then return nil end
        obj = readobj(objoraddr)
    end
    return obj
end

function objstr(obj)
    obj = objoraddrtoobj(obj)
    if obj == nil or obj.addr == 0 then
        return "none"
    elseif obj.handle.type == 3 then
        return "root"
    elseif obj.addr < 0x400 then
        return "non-object"
    elseif obj.handle.type == 2 then
        return string.format("handle %i", (obj.addr - 0x80060DB8) / 8)
    elseif not (obj.entity == 0) then
        entity = obj.entity
        _type = readu8(entity + 0x12)
        id = readu16(entity + 0x8)
        ldat = readu32(0x8005C53C)
        eidorpte = readu32(ldat+0x14+(_type*4))
        if eidorpte & 1 == 1 then
            name = eidtoname(eidorpte)
        else
            ep = readu32(eidorpte)
            entry = readentry(ep)
            name = eidtoname(entry.eid)
        end
        return string.format("%i (%s)", id, name)
    elseif not (obj.external == 0) then
        name = eidtoname(obj.external.eid)
        subtype = obj.subtype
        return string.format("%s (subtype %i)", name, subtype)
    elseif not (obj.global == 0) then
        name = eidtoname(obj.global.eid)
        subtype = obj.subtype
        return string.format("%s (subtype %i)", name, subtype)
    else
        return string.format("no entity @%08x", obj.addr)
    end
end

function objsiblings(obj)
    obj = objoraddrtoobj(obj)
    if obj == nil then return nil end
    siblings = {}
    addr = obj.addr
    while not (addr == 0) do
        obj = readobj(addr)
        obj.addr = addr
        table.insert(siblings, obj)
        addr = obj.sibling
    end
    return siblings
end

function objchildren(obj)
    obj = objoraddrtoobj(obj)
    if obj == nil then return nil end
    if obj.handle.type == 3 then
        return obj.children
    end
    children = objsiblings(obj.children)
    return children
end

function objstackstr(obj)
    obj = objoraddrtoobj(obj)
    if obj == nil then return nil end
    res = ""
    header = obj.global.items[0]
    base_sp = readu32(header+0xC)*4
    stack = obj.addr + 0x60 + base_sp
    fp = obj.fp - stack
    sp = obj.sp - stack
    res = res .. "memory contents: \n"
    for i=0,sp do
        offs = i % 16
        if offs == 0 then
            line = string.format("%03x+60:", base_sp+i)
            res = res .. line
        end
        line = string.format("%02x", readu8(stack+i))
        if i == fp then
            line = "(" .. line
        elseif i == sp-1 then
            line = line .. ")"
        end
        res = res .. line
        if offs == 15 then
            res = res .. "\n"
        end
    end
    if not offs == 15 then
        res = res .. "\n"
    end
    res = res .. "\n"
    return res
end

function objcodestr(obj)
    obj = objoraddrtoobj(obj)
    if obj == nil then return nil end
    res = objstackstr(obj)
    code = obj.external.items[1]
    pcins = obj.pc - code
    pcs = max(pcins - ((dislen/2)*4), 0)
    pcn = pcs + dislen*4
    for pc=pcs,pcn,4 do
        ins = readu32(code+pc/4)
        line = GoolDisassemble(ins, pc)
        curstr = "    "
        if pc == pcins then
            curstr = "*** "
        end
        res = res .. curstr .. line .. '\n'
    end
    return res
end
