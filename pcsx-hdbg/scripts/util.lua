function tcopy(t)
    res = {}
    for k,v in pairs(t) do
        res[k] = v
    end
    return res
end

function map(t, f, keys)
    keys = keys or false
    _t2 = {}
    if keys == false then
        for k,v in pairs(t) do
            table.insert(_t2, f(v,k))
        end
    else
        for k,v in pairs(t) do
            res = f(v,k)
            nv=res[1]
            nk=res[2]
            _t2[nk]=nv
        end
    end
    return _t2
end

function treemap(t, f, cf, root, keys, path)
    local _t2 = {}
    -- default arguments
    keys = keys or false
    path = path or {}
    root = root or true
    if root == true then
        -- t refers to an 'object' type table instead of an 'array' type table
        -- use cf to extract children from t
        children = cf(t)
        if children == nil then
            children = {}
            _t2 = nil
        end
        for k,c in pairs(children) do
            -- make copy of current path and append to it the key for this child
            pnext = {}
            for i,p in ipairs(path) do
                table.insert(pnext, p)
            end
            table.insert(pnext, k)
            -- recursively call on child object with the new path;
            -- all other arguments stay the same
            mcn = treemap(c, f, cf, true, keys, pnext)
            -- add mapped object to 'children' dictionary
            if keys == true then
                -- the above treemap should have mapped the key for the child object
                -- in addition to the object itself
                -- the result should be a pair (table of 2 elems)
                -- with the respective mapped key and object to add
                mv = mcn[1]
                mk = mcn[2]
                _t2[mk] = mv
            else
                -- the above treemap should have mapped only the child object
                -- the result should be just the mapped object
                -- add it to the 'children' dictionary under the original unmapped/key
                _t2[k] = mcn
            end
        end
        -- call mapping function with
        -- - unmapped (root) object
        -- - dictionary of mapped children
        -- - path of (root) object
        res = f(t, _t2, path)
        -- return the custom mapped/merged result
        return res
    else
        -- t refers to an 'array' type table;
        -- so we map the array via recursive call to this function,
        -- but with the 'object' type (input) table variant
        mt = {}
        for i,v in ipairs(t) do
            -- make copy of current path and append to it the index (unmapped key) for this child
            pnext = {}
            for k,p in pairs(path) do
                table.insert(pnext, k)
            end
            table.insert(pnext, i)
            -- recursively call on child object with new path
            mcn = treemap(v, f, cf, true, keys, pnext)
            -- put mapped child in result 'array' type table
            mt[i] = mcn
        end
        return mt
    end
end

function pathstr(path)
    str = ""
    for i, part in ipairs(path) do
        if type(part) == "number" then
            str = str .. '[' .. tostring(part) .. ']'
        elseif str == "" then
            str = part
        else
            str = str .. '.' .. part
        end
    end
    return str
end

--[[ flatten a tree of nested tables;
     by default keys in the result table are path strings for the corresponding nested values
     if nk == true then values are instead inserted sequentially into the result table, and keyed by integer index
     if nk == false then pf can be a function with alternate logic for choosing the keys
--]]
function treeflatten(t, cf, nk, pf, vt)
    flat = {}
    nk = nk or false
    pf = pf or pathstr
    vt = vt or function(v) return not (type(v)=="table") end
    treemap(t, function(v, mc, p)
        if vt(v) then
            if nk == false then
                k = pf(p, v, mc)
                flat[k] = v
            else
                table.insert(flat, v)
            end
        end
        return nil
    end, cf)
    return flat
end

--[[ return a function which can be used to map
     a tree of nodes of type A to a tree of nodes of type B
     and optionally re-use existing type B nodes from a tree
     that previous resulted from the function
     and that have the same type A hash --]]

function treerepl(mroot, fn, cb, scb, ha, hb)
    fb = function(path, item)
        return hb(item)
    end
    if mroot == nil then
        mfprev = {}
    else
        mfprev = treeflatten(mroot, cb, false, fb, function(_) return true end)
    end
    return function(obj, mchildren, path)
        hash = ha(obj)
        if not (mfprev[hash] == nil) then
            scb(mfprev[hash], mchildren)
        else
            mfprev[hash] = fn(obj, mchildren, path)
        end
        return mfprev[hash]
    end
end

function tableornil(v)
  if not (type(v) == "table") then return nil end
  return v
end

function tobinary(x)
	ret=""
	while x~=1 and x~=0 do
		ret=tostring(x%2)..ret
		x=math.modf(x/2)
	end
	ret=tostring(x)..ret
	return ret
end


function add_tables(tab1, tab2, ...)
	tab3 = {}
	for _,v in ipairs(tab1) do
		table.insert(tab3, v)
	end
	for _,v in ipairs(tab2) do
		table.insert(tab3, v)
	end
	if select('#', ...) >= 1 then
		return add_tables(tab3, ...)
	end
	return tab3
end


function split(inputstr, sep)
   if sep == nil then
      sep = "%s"
   end
   t={}
   for str in string.gmatch(inputstr, "([^"..sep.."]+)") do
      table.insert(t, str)
   end
   return t
end


function path_set(table, value, ...)
	count = select('#', ...)
	prev = table
	for i=1,count-1 do
		key = select(i, ...)
		if prev[key] == nil then
			prev[key] = {}
		end
		prev = prev[key]
	end
	key = select(count, ...)
	prev[key] = value
	return prev[key]
end

function path_get(table, value, ...)
	count = select('#', ...)
	prev = table
	for i=1,count do
		key = select(i, ...)
		prev = prev[key]
	end
	return prev
end

function luastr(obj, indent, level)
    indent = indent or 2
    level = level or 0
    if level > 6 then return "..." end
    local str = ""
    if obj == nil then
        return "nil"
    elseif type(obj) == "table" then
        str = "{\n"
        for k,v in pairs(obj) do
            if not (type(k) == "string") then
                k = luastr(k)
            end
            cstr = luastr(v, indent, level+1)
            line = string.rep(" ", (level+1)*indent) .. k .. ": " .. cstr .. ",\n"
            str = str .. line
        end
        str = str .. string.rep(" ", level*indent) .. "}"
        return str
    elseif type(obj) == "number" or type(obj) == "boolean" then
        return tostring(obj)
    elseif type(obj) == "string" then
        return obj
    else
        return type(obj)
    end
    return "unknown"
end
