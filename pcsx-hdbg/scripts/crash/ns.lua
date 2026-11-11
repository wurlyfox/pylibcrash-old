local eid_charset = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_!"
function eidtoname(value)
	local char1 = ((value >> 25) & 0x3F) + 1
	local char2 = ((value >> 19) & 0x3F) + 1
	local char3 = ((value >> 13) & 0x3F) + 1
	local char4 = ((value >> 7) & 0x3F) + 1
	local char5 = ((value >> 1) & 0x3F) + 1

	char1 = eid_charset:sub(char1, char1)
	char2 = eid_charset:sub(char2, char2)
	char3 = eid_charset:sub(char3, char3)
	char4 = eid_charset:sub(char4, char4)
	char5 = eid_charset:sub(char5, char5)

	return char1 .. char2 .. char3 .. char4 .. char5
end

function iseid(value)
    if (value & 1) == 1 then
        return true
    end
    return false
end

function isoffset(value)
	if value < 0x10000 then
		return true
	end
	return false
end

function readentry(addr)
	local entry = {}
	entry.magic = readu32(addr+0)
	entry.eid = readu32(addr+4)
	entry.name = eidtoname(entry.eid)
	entry.type = readu32(addr+8)
	entry.item_count = readu32(addr+0xC)
	entry.items = {}
	for i=1,entry.item_count+1 do
		value = readu32(addr+0x10+((i-1)*4))
		ptr = value
		if isoffset(value) then
			ptr = ptr+addr
		end
		entry.items[i] = ptr
	end
	return entry
end

function readpage(addr)
	local page = {}
	page.magic = readu16(addr+0)
	page.type = readu16(addr+2)
	page.pgid = readu32(addr+4)
	page.entry_count = readu32(addr+8)
	page.checksum = readu32(addr+0xC)
	page.entries = {}
	ptr = 0
	for i=1,page.entry_count do
		value = readu32(addr+0x10+((i-1)*4))
		ptr = value
		if isoffset(value) then
			ptr = ptr+addr
		end
		page.entries[i] = readentry(ptr)
	end
	return page
end

function geteidorentryeid(value)
    if iseid(value) then
        return value
    end
    ptr = readu32(value)
    entry = readentry(ptr)
    return entry.eid
end
