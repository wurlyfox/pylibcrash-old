require('scripts.pad')

local menu_idx = 1
local item_idx = 1
local menu_count = 0

--[[
function guibutton(fn, m_idx, i_idx, label)
	value = ""
	selector = "  "
	if menu_idx == m_idx and item_idx == i_idx then
		selector = "X "
		if (buttons & 1024) == 0 and (directions & 0x20) == 0 then
			value = "X"
			fn(m_idx, i_idx)
		end
	end

	if label == 0 or label == nil then
		label = ""
	else
		label = label .. ": "
	end

	gui.label(string.format("%s%s%s", selector, label, value))
end

function guiedit(address, type, m_idx, i_idx, label)
	local info_map = {
		["uint32"] = { readfn = readu32, writefn = write32, fmt = "%08X", maxval = 0xFFFFFFFF, minval =          0 },
		["uint16"] = { readfn = readu16, writefn = write16, fmt = "%04X", maxval =     0xFFFF, minval =          0 },
		["uint8"]  = { readfn = readu8,  writefn = write8,  fmt = "%02X", maxval =       0xFF, minval =          0 },
		["int32"]  = { readfn = readu32, writefn = write32, fmt = "%08X", maxval = 0x7FFFFFFF, minval = 0x80000000 },
		["int16"]  = { readfn = readu16, writefn = write16, fmt = "%04X", maxval =     0x7FFF, minval =     0x8000 },
		["int8"]   = { readfn = readu8,  writefn = write8,  fmt = "%02X", maxval =       0x7F, minval =       0x80 },
		["eid"]	   = { readfn = readu32, writefn = write32, fmt = "%s"  , maxval = nil,	       minval = nil    	   }
	}

	info = info_map[type]
	readfn = info.readfn
	value = readfn(address)

	if type == 'eid' then
		value = eidtoname(value)
		idx = -1 -- no write yet
	end

	selector = "  "
	if menu_idx == m_idx and item_idx == i_idx then
		selector = "X "
		if (buttons & 1024) == 0 and (directions & 0x20) == 0 then
			value = math.min(value + 1, info.maxval)
			info.writefn(address, value)
		end
		if (buttons & 1024) == 0 and (directions & 0x80) == 0 then
			value = math.max(value - 1, info.minval)
			info.writefn(address, value)
		end
	end

	if label == 0 or label == nil then
		label = ""
	else
		label = label .. ": "
	end

	gui.label(string.format("%s%s" .. info.fmt, selector, label, value))
end


function guimenu(items)
	if (buttons & 1024) == 0 and ((directions & 0x40) == 0) then
		item_idx = math.min(item_idx+1,#items)
	end
	if (buttons & 1024) == 0 and ((directions & 0x10) == 0) then
		item_idx = math.max(item_idx-1,1)
	end

	for idx, entry in ipairs(items) do
		label = entry.label
		if entry.control == "button" then
			guibutton(entry.fn, menu_count+1, idx, label)
		else
			guiedit(entry.address, entry.type, menu_count+1, idx, label)
		end
	end
	menu_count = menu_count + 1
end

function guimenus_begin()
	getbuttons()
	menu_count = 0
end

function guimenus_end()
	if (buttons & 2048) == 0 and (directions & 0x20) == 0 then
		menu_idx = math.min(menu_idx+1,menu_count)
	end
	if (buttons & 2048) == 0 and (directions & 0x80) == 0 then
		menu_idx = math.max(menu_idx-1,1)
	end
end
]]--

local charset = "qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM1234567890"
math.randomseed(os.clock()^5)
function random_string(length)
	local ret = {}
	local r
	for i = 1, length do
		r = math.random(1, #charset)
		table.insert(ret, charset:sub(r, r))
	end
	return table.concat(ret)
end

function dtype_info(name)
    if name=="uint32" then
        return { size=4, sign=0 }
    elseif name=="uint16" then
        return { size=2, sign=0 }
    elseif name=="uint8" then
        return { size=1, sign=0 }
    elseif name=="int32" then
        return { size=4, sign=1 }
    elseif name=="int16" then
        return { size=2, sign=1 }
    elseif name=="int8" then
        return { size=1, sign=1 }
    else
        return nil
    end
end

Item = {}

function Item:new(arg)
    item = {}
    setmetatable(item, self)
    self.__index = self
    item.id = random_string(16)
    item.control = arg.control
    item.str = arg.str
    item.label = arg.label
    item.fn = arg.fn
    item.data = arg.data
    item.selectable = arg.selectable
    item.selected = arg.selected
    item.on_select = arg.on_select
    item.children = arg.children
    if item.control == "property" then
        item.addr = arg.addr
        item.dtype = arg.dtype
        item.min = arg.min
        item.max = arg.max
    end
    if item.control == "node" or item.control == "tree" then
        item.selected = 0
    end
    if item.selectable == true then
        item.on_mouse = item:mouse_handler()
        item.on_mousedown = item:select_handler()
    end
    return item
end

function Item:add_child(child)
    if self.children == nil then
        self.children = {}
    end
    table.insert(self.children, child)
end

function Item:get_tree()
    item = self
    print(luastr(item))
    if item.control == "tree" then return item end
    while not (item.parent == nil) do
        item = item.parent
        print(luastr(item))
        if item.control == "tree" then return item end
    end
    return nil
end

function Item:mouse_handler()
    return function(down)
        if self.down == nil then
            self.down = down
            return
        end
        if down == 1 and self.down == 0 then
            if self.on_mousedown == nil then return end
            self.on_mousedown()
        elseif down == 0 and self.down == 1 then
            if self.on_mouseup == nil then return end
            self.on_mouseup()
        end
    end
end

function Item:select_handler()
    if self.control == "node" or self.control == "tree" then
        tree = self:get_tree()
        if not (tree == nil) then
            if not (tree.selitem == nil) then
                tree.selitem.selected = 0
            end
            tree.selitem = self
        end
    end
    if not (self.on_select == nil) then
        self.on_select()
    end
end

function Item:draw()
    if not (self.children == nil) then
        for i,child in ipairs(self.children) do
            child.parent = self
        end
    end
    if not (self.label == nil) then
        gui.row(2)
        gui.label(self.label, self.selected)
    end
    select_handler = nil
    if self.selectable == true then
        select_handler = self.select_handler()
    end
    if type(self.str) == "function" then
        str = self.str(self)
    else
        str = self.str
    end
    str = str or ""
    if self.control == "button" then
        gui.button(str, self.fn, self.id)
    elseif self.control == "label" then
        gui.label(str, self.selected, select_handler)
    elseif self.control == "text" then
        gui.text(str, self.selected, select_handler)
    elseif self.control == "property" then
        info = dtype_info(self.dtype)
        if not (self.min == nil) and not (self.max == nil) then
            gui.property(str, self.addr, info.size, info.sign, self.min, self.max)
        else
            gui.property(str, self.addr, info.size, info.sign)
        end
    elseif self.control == "node" or self.control == "tree" then
        expanded, selected = gui.tree_push(str, self.id, self.selected)
        if self.selected == 0 and selected == 1 then
            self.selected = 1
            self:select_handler()
        else
            self.selected = selected
        end
        if expanded == 1 then
            if not (self.children == nil) then
                guidraw(self.children)
            end
            gui.tree_pop()
        end
    elseif self.control == "row" then
        if not (self.children == nil) then
            gui.row(#self.children)
            guidraw(self.children)
        end
    elseif self.control == "group" then
        if not (self.children == nil) then
            guidraw(self.children)
        end
    end
end

--[[

since the underlying gui backend (nuklear) is minimal state
the lua bindings are made to follow suite

this means that most of the state information which controls
how a widget is rendered is maintained in this layer

responding to events (mainly click within rendered widget) is
accomplished by passing a callback to each render; each rendered widget will
have its own unique callback for handling a particular type of event;
said callback can modify state that persists between renders;
such state can control how a widget renders its corresponding item
in following frames
]]--
function guidraw(items)
    for i,item in ipairs(items) do
        item:draw()
    end
end
