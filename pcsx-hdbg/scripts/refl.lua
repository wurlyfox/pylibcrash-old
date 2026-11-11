--[[
    Minimal c type reflection lib (c1 extension, Lua port)

    Usage: define 'Types' (using Type:new) for each type needing
    reflection support and use the library functions as needed.
]]--

function read(addr, size, sign)
    if sign == true then
        if size == 4 then
            return reads32(addr)
        elseif size == 2 then
            return reads16(addr)
        elseif size == 1 then
            return reads8(addr)
        else
            error("invalid size")
        end
    else
        if size == 4 then
            return readu32(addr)
        elseif size == 2 then
            return reads16(addr)
        elseif size == 1 then
            return reads8(addr)
        else
            error("invalid size")
        end
    end
end

function write(addr, size, value)
    if size == 4 then
        return write32(addr, value)
    elseif size == 2 then
        return write16(addr, value)
    elseif size == 1 then
        return write8(addr, value)
    end
end

Type = { is_inited=false, is_prim=false }
Field = { is_pointer=false }

function Type:new(arg)
    _type = {}
    setmetatable(_type, self)
    self.__index = self
    fields = arg.fields or {}
    self.name = arg.name
    self.size = arg.size
    self.sign = arg.sign
    self.fields = fields
    self.basename = arg.basename
    self.subtype_fn = arg.subtype_fn
    self.is_prim = (not (arg.size == nil))
    self.is_inited = false
    self:init()
    return _type
end

function Field:new(arg)
    field = {}
    setmetatable(field, self)
    self.__index = self
    self.name = arg.name
    self.typename = arg.typename
    self.type = nil
    self.parent = nil
    self.offset = arg.offset
    self.after = arg.after
    self.is_pointer = arg.is_pointer or false
    self.count = arg.count
    self.fcount = arg.fcount
    self.count_fn = arg.count_fn
    self.size_fn = arg.size_fn
    return field
end

function get_type(name, list)
    list = list or typelist
    for _,_type in ipairs(list) do
        if _type.name == name then return _type end
    end
    return nil
end

--[[
  perform remaining initialization for a statically defined refl_type

  this includes:
  - establishing the linked list between fields defined in the
    fields[] flexible array
  - resolving typename to a refl_type for each field
  - resolving base typename to a refl_type, if specified

  \param type refl_type* - type object
]]--
function Type:init()
    if self.is_inited then return end
    --[[ inheritance extension
        it a base type name exists then look it up
        then insert the type into the base type's subtypes list ]]--
    if not (self.basename == nil) then
        self.base = get_type(self.basename)
        if not (self.base == nil) then
            table.insert(self.base.subtypes, self)
        end
    end
    -------------------
    for i,it in ipairs(self.fields) do
        it.parent = self
        if it.type == nil and not (it.typename == nil) then
            if string.sub(it.typename,-1,-1) == '*' then
                it.typename = string.sub(it.typename,0,-1)
                it.is_pointer = true
            end
            it.type = get_type(it.typename)
        end
    end
    self.is_inited = true
end

Int = Type:new{ name="int", size=4, sign=true }
Int32 = Type:new{ name="int32", size=4, sign=true }
Int16 = Type:new{ name="int16", size=2, sign=true }
Int8 = Type:new{ name="int8", size=1, sign=true }
UInt32 = Type:new{ name="uint32", size=4, sign=false }
UInt16 = Type:new{ name="uint16", size=2, sign=false }
UInt8 = Type:new{ name="uint8", size=1, sign=false }
Void = Type:new{ name="void*", size=4, sign=false }

typelist = { Int,
             Int32, Int16, Int8,
             UInt32, UInt16, UInt8,
             Void }

--[[ look up a field of a structure type by name

 (if they exist, the chains of base types or dynamic subtypes
 are also searched from bottom to top for the field)

 \param type refl_type* - type object
 \param name char* - field name
 \param data void* - data object (only needed if searching dynamic subtypes)
--]]
st = 0
function Type:get_field(name, data)
    if name == nil then
        dummy = Field:new()
        dummy.type = self
        dummy.parent = self
        dummy.offset = 0
        return dummy
    end
    --[[ inheritance extension
         if there is a dynamic subtype then compute it and search for the field
         in the subtype --]]
    if not (data == nil) and not (self.subtype_fn == nil) then
        subtype = self.subtype_fn(data, self)
        if not (subtype == nil) and st >= 0 then
            st = st + 1
            field = subtype:get_field(name, data)
            st = st - 1
            if not field == nil then
                return field
            end
        end
    end
    --------------------------
    field = nil
    for _,it in ipairs(self.fields) do
        if it.name == name then
            field = it
            --break
        end
    end
    --[[ inheritance extension
         if the field is not found and there is a base type
         then search for the field in the base type ]]--
    if not (field == nil) and not (self.base == nil) and st <= 0 then
        st = st - 1
        field = self.base:get_field(name, data)
        st = st + 1
    end
    -----------------------
    return field
end

--[[ get the length/element count of an array field

 - if the field has a count_fn callback, it is called
   with the data and field (or fcount field if it exists)
   to get the length
 - else if the field specifies an fcount fieldname, the
   value of that field determines the length
 - else if the field specifies a constant length it
   is used as the length
 - else the field is a non-array field and the function
   returns -1

 \param data void* - data object
 \param field refl_field* - field object
 \returns int - length/element count, or -1 if error
]]--
function Field:get_count(data)
    count = nil
    if not (self.count_fn == nil) then
        _type = self.parent
        if not (self.fcount == nil) then
            fcount = _type:get_field(self.fcount, data)
        else
            fcount = field
        end
        count = self.count_fn(data, fcount)
    elseif not (self.fcount == nil) then
        _type = self.parent;
        count = _type:get_int(data, self.fcount)
    elseif not (self.count == nil) then
        count = self.count
    end
    return count
end

--[[ get the offset of a structure field

 (offset may be directly specified for the field
  or calculated as offset + size of a specified preceding field)

 \param data void* - data object
 \param field refl_field* - field object
 \returns int - field offset
]]--
function Field:get_offset(data)
    if not self.after == nil then
        _type = self.parent;
        common = _type:get_common(data, self.after)
        return common.offset + common.size
    else
        return self.offset
    end
end

--[[ get the offset of an element of an array field, with respect to
 the containing structure

 (offset is calculated as offset of array field + sum of sizes of
  preceding elements)

 idx can range from 0 to the array length; if idx is equal to the
 array length, the offset returned will be the offset plus size
 of the last element

 \param data void* - data object
 \param field refl_field* - [array] field object
 \param idx int - element index
 \returns int - field offset
]]--

function Field:get_offsetA(data, idx)
    offset = self:get_offset(data)
    if self.is_pointer then
        offset = offset + (4 * idx)
    elseif self.is_2darray then
        for i=0,idx do
            data_base = data + offset
            offset = offset + self:get_sizeA(data, i)
        end
    elseif self.is_fixed or self.is_prim then
        offset = offset + (self.type.size * idx)
    else
        offs_max = offset
        for i=0,idx do
            for j,f in ipairs(self.type.fields) do
                data_base = data + offset
                offs_base = offset + f:get_offset(data_base)
                size = f:get_size(data_base)
                offs_max = max(offs_base + size, offs_max)
            end
            offset = offs_max
        end
    end
    return offset
end

--[[ get the size of a structure field

 (where element count is 1 for non-array fields)
 - defined as element count * element size for elements of
   equal size (primitives, fixed size structs)
 - defined as offset plus size of last element of the
   array, with respect to structure, minus offset of
   the first element

 \param data void* - data object
 \param field refl_field* - field object
 \returns size_t - size
]]--
function Field:get_size(data)
    count = self:get_count(data)
    if count == nil then count = 1 end
    if field.is_pointer then
        size = 4 * count
    elseif not (field.is_2darray and
                (field.type.is_fixed or field.type.is_prim)) then
        size = field.type.size * count
    else
        offset = field:get_offsetA(data, count)
        size = offset - field:get_offset(data)
    end
    return size
end

--[[ get the size of an element of an array field

 - defined as the primitive/fixed-size type size if array of
   primitives or fixed-size type
 - defined as the result of size_fn callback for 2d primitive arrays
 - defined as the max (offset+size) value of the fields of the
   structure of the idx'th element minus the offset of the idx'th
   element, both offsets with respect to 'data'

 \param data void* - data object
 \param field refl_field* - field object
 \param idx int - element index
 \returns size_t - size
]]--
function Field:get_sizeA(data, idx)
    if self.is_pointer then
        size = 4
    elseif self.is_2darray then
        size = self.size_fn(data, field, idx)
    elseif self.type.is_fixed or self.type.is_prim then
        size = self.type.size
    else
        offset = self:get_offsetA(data, idx)
        offs_max = offset
        for i,f in ipairs(self.type.fields) do
            data_base = data + offset
            offs_base = offset + f:get_offset(data_base)
            size = f:get_size(data_base)
            offs_max = max(offs_base + size, offs_max)
        end
        size = offs_max - offset
    end
    return size
end

--[[ get common attributes for a structure field or primitive type

 \param data void* - data object
 \param type refl_type* - parent type
 \param name char* - field name (or 0 if type is prim)
 \param common refl_common* - (out) common attributes
 \return int - success code
]]--
function Type:get_common(data, name)
    common = {}
    if type.is_prim then
        common.field = nil
        common.size = self.size
        common.offset = 0
        common.idx = nil
    else
        field = self:get_field(name, data)
        if field == nil then return nil end
        common,field = field
        common.size = field:get_size(data)
        common.offset = field:get_offset(data)
        common.idx = nil
    end
    return common
end

--[[ get common attributes for a structure field

 \param data void* - data object
 \param field refl_field* - field object
 \param common refl_common* - (out) common attributes
 \return int - success code
]]--
function Field:get_common(data)
    common = {}
    common.field = field
    common.size = field:get_size(data)
    common.offset = field:get_offset(data)
    common.idx = nil
    return common
end

--[[
 get common attributes for an element of an array

 the array can be a structure field or an array of primitives

 \param data void* - data object
 \param type refl_type* - parent type
 \param name char* - field name
 \param idx int - element index
 \param common refl_common* - (out) common attributes
 \return int - success code
]]--
function Type:get_commonA(data, name, idx)
    common = {}
    if type.is_prim then
        common.field = nil
        common.size = self.size
        common.offset = self.size*idx
        common.idx = idx
    else
        field = self:get_field(name, data)
        if field == nil then return nil end
        common.field = field
        common.size = field:get_sizeA(data, idx)
        common.offset = field:get_offsetA(data, idx)
        common.idx = idx
    end
    return common
end

--[[
  get common attributes for an element of an array in a structure

 \param data void* - data object
 \param type refl_field* - field object
 \param idx int - element index
 \param common refl_common* - (out) common attributes
 \return int - success code
]]--
function Field:get_commonA(data, idx)
    common = {}
    common.field = self
    common.size = field:get_sizeA(data, idx)
    common.offset = field:get_offsetA(data, idx)
    common.idx = idx
    return common
end

--[[
  get the value of a field, using common attributes

 \param data void* - data object
 \param common refl_common* - common attributes
 \return refl_value* - value object
]]--
function get_value(data, common)
    value = {}
    value.field = common.field
    value.offset = common.offset
    value.size = common.size
    value.idx = nil
    value.res = data + value.offset
    value.valid = 1
    return value
end

--[[ get the value of a field

 \param data void* - data object
 \param type refl_type* - parent type
 \param name char* - field name
 \return refl_value* - value object
]]--
function Type:get(data, name)
    common = self:get_common(data, name)
    if common == nil then return nil end
    return get_value(data, common)
end

--[[
  get the value of a field (by field object)

  \param data void* - data object
  \param field refl_field* - field object
  \return refl_value* - value object
]]--
function Field:get(data)
    common = self:get_common(data)
    if common == nil then return nil end
    return get_value(data, common)
end

--[[
  get the value of an array element

  \param data void* - data object
  \param type refl_type* - parent type
  \param name char* - array field name
  \param idx int - element index
  \return refl_value* - value object
]]--
function Type:getA(data, name, idx)
    common = type:get_commonA(data, name, idx)
    if common == nil then return nil end
    return get_value(data, common)
end

--[[
  get the value of an array element (by field object)

  \param data void* - data object
  \param field refl_field* - field object
  \param idx int - element index
  \return refl_value* - value object
]]--
function Field:getA(data, idx)
    common = field:get_commonA(data, idx)
    if common == nil then return nil end
    return get_value(data, common)
end


--[[
    set the value of a field

 \param data void* - data object
 \param type refl_type* - parent type
 \param name char* - field name
 \param src void* - pointer to source value/data
 \return refl_value* - value object
]]--
function Type:set(data, name, src)
    common = self:get_common(data, name)
    if common == nil then return false end
    for i=0,common.size do
        val = readu8(src+i)
        write8(data+common.offset+i, val)
    end
    return true
end

--[[
  set the value of a field (by field object)

  \param data void* - data object
  \param field refl_field* - field object
  \param src void* - pointer to source value/data
  \return int - success code
]]--
function Field:set(data, src)
    common = self:get_common(data)
    if common == nil then return false end
    for i=0,common.size do
        val = readu8(src+i)
        write8(data+common.offset+i, val)
    end
    return true
end

--[[
  set the value of an array element

  \param data void* - data object
  \param type refl_type* - parent type
  \param name char* - array field name
  \param idx int - element index
  \param src void* - pointer to source value/data
  \return int - success code
]]--

function Type:setA(data, name, idx, src)
    common = self:get_commonA(data, name, idx)
    if common == nil then return false end
    for i=0,common.size do
        val = readu8(src+i)
        write8(data+common.offset+i, val)
    end
    return true
end

--[[
  set the value of an array element (by field object)

  \param data void* - data object
  \param field refl_field* - field object
  \param idx int - element index
  \param src void* - pointer to source value/data
  \return int - success code
]]--
function Field:setA(data, idx, src)
    common = self:get_commonA(data, idx)
    if common == nil then return false end
    for i=0,common.size do
        val = readu8(src+i)
        write8(data+common.offset+i, val)
    end
    return true
end

--[[ get the value of an integer valued field ]]--
function Type:get_int(data, name)
    if self.is_prim then
        return read(data, self.size, self.sign)
    end
    field = self:get_field(name, data)
    return field:get_int(data)
end

--[[ get the value of an integer valued field (by field object) ]]--
function Field:get_int(data)
    if not self.type.is_prim then
        return nil
    end
    common = self:get_common(data)
    data = data + common.offset
    return self.type:get_int(data)
end

--[[ get the value of an integer valued array element ]]--
function Type:get_intA(data, name, idx)
    if self.is_prim then
        common = self:get_commonA(data, nil, idx)
        data = data + common.offset
        return read(data, self.size, self.sign)
    end
    field = self:get_field(name, data)
    return field:get_intA(data, idx)
end

--[[ get the value of an integer valued array element (by field object) ]]--
function Field:get_intA(data, idx)
    if not self.type.is_prim then
        return nil
    end
    common = self:get_commonA(data, idx)
    data = data + common.offset
    return self.type:get_int(data)
end

--[[ set the value of an integer valued field ]]--
function Type:set_int(data, name, src)
    if self.is_prim then
        return write(data, self.size, src)
    end
    field = self:get_field(name, data)
    return field:set_int(data, src)
end

--[[ set the value of an integer valued field (by field object) ]]--
function Field:set_int(data, src)
    if not self.type.is_prim then
        return nil
    end
    common = self:get_common(data)
    data = data + common.offset
    return self.type:set_int(data, src)
end

--[[ set the value of an integer valued array element ]]--
function Type:set_intA(data, name, idx, src)
    if self.is_prim then
        common = self:get_commonA(data, nil, idx)
        data = data + common.offset
        return write(data, self.size, src)
    end
    field = self:get_field(name, data)
    return field:set_intA(data, idx)
end

--[[ set the value of an integer valued array element (by field object) ]]--
function Field:set_intA(data, idx, src)
    if not self.type.is_prim then
        return nil
    end
    common = self:get_commonA(data, idx)
    data = data + common.offset
    return self.type:set_int(data, src)
end


-- misc helper functions

--[[ get the value of a parent

  \param data void* - data object
  \param field refl_field* - field object
  \param ptype refl_type* - grandparent type
  \param pname char* - parent field name
  \return refl_value - value object
]]--
function Field:get_parent(data, ptype, pname)
    pfield = ptype:get_field(pname, 0)
    data = data - field.offset - pfield.offset
    common = ptype:get_common(data, pname)
    return get_value(data, common)
end

function strlen(data)
    done = false
    len = 0
    while not done do
        char = readu8(data + len)
        if char == 0 then done = true
        else len = len + 1 end
    end
    return len
end

--[[
  get the length of a string (char array) type field
  or the length of an element of a field of an array of
  variable length/zero-terminated string type

  intended for use as size callback for fields of such type

  \param data void* - data object
  \param field refl_field* - field object
  \param idx int - 0 for non-array, or index of array element
  \return int - string length
]]--
function Field:strlen(data, idx)
    idx = idx or 0
    offset = Field:get_offset(data)
    data = data + offset
    for i=0,idx do
        data = data + strlen(data) + 1
    end
    len = strlen(data)
    return len
end

--[[
void ReflPrintPrim(refl_value *value, refl_path *path) {
  int ivalue;

  if value.field.flags & REFL_FLAGS_2DARRAY
    printf("%s = (%i byte array)\n", path.name, value.size);
  else if value.field.flags & REFL_FLAGS_POINTER {
    ivalue = ReflGetInt32(value.res, &refl_uint32, 0);
    printf("%s = 0x%08X (pointer)\n", path.name, ivalue);
  }
  else {
    ivalue = ReflGetInt(value.res, value.field.type, 0);
    printf("%s = %i\n", path.name, ivalue);
  }
}
]]--

--[[
/**
 * push to a value path
 *
 * \param path refl_path* - path
 * \param value refl_value - value to append
 * \param id int - id (field index) to append
 * \param name char* - field name to append
 * \param type int - format type (non-array or array)
 */
static void ReflPathPush(refl_path *path, refl_value value, int id, char *name, int type) {
  int nlen, prefix;

  nlen = strlen(path.name);
  prefix = (nlen != 0);
  path.id[path.len] = id;
  path.values[path.len] = value;
  ++path.len;
  if !prefix {
    strcpy(path.name+nlen, name);
    return;
  }
  switch (type) {
  case 1: // non-array
    sprintf(path.name+nlen, ".%s", name);
    break;
  case 2: // array
    sprintf(path.name+nlen, ".%s[%d]", name, id);
    break;
  case 3: // primitive
    sprintf(path.name+nlen, "::%s", name);
    break;
  }
}

/**
 * pop from a value path
 *
 * \param path refl_path* - path
 */
static void ReflPathPop(refl_path *path) {
  int nlen, i;

  nlen = strlen(path.name);
  for (i=nlen-1;i>=0;i--) {
    if path.name[i]=='.' { break; }
    if path.name[i]==':' { --i; break; }
    //if path.name[i]=='[' { break; }
  }
  path.name[i] = 0;
  --path.len;
}
]]--

--[[
  helper function for ReflTraverseR

  runs the visit callback,
  passing the value, path, and isleaf properties for the field
  if it returns zero, then:
  - -1 is returned
  - the field is not mapped
  - no further recursion is done into the field
  otherwise if an array of already mapped children has been passed
  - the already mapped children are passed to the map callback
  otherwise if the field is a non-leaf
  - ReflTraverseR is called recursively on the field value/type/path
  - the result (array of pointers to mapped children) is passed to
    the map callback
  result of the map callback in either case is returned

  \param context refl_context* - context
  \return void** - zero terminated array of pointers to mapped fields
]]--
function traverseC(context)
    local data = context.data
    local value = context.value
    local _type = context.type
    local path = context.path
    local leaf = context.leaf
    local visit = context.visit
    local map = context.map
    local mapped = context.mapped
    local res = 1;
    if not (visit == nil) then
        res = visit(value, path, leaf)
    end
    if res == nil then return nil end
    context.data = value.res -- set new data
    context.type = value.field.type
    if not leaf and (mapped==nil) then -- non-leaf and non-array?
        mapped = traverseR(context) -- traverse child struct
    end
    context.type = _type -- restore old type
    context.data = data -- restore old data
    context.value = value
    context.leaf = leaf -- restore old leaf flag
    mapres = nil
    if not (map == nil) then
        mapres = map(value, path, mapped) -- pass value,path,mapped children
    end
    return mapres -- return the mapped field
end

--[[ traverse the next level of data structure described in the context

  \param context refl_context* - context
  \return void** - zero terminated array of pointers to mapped fields
]]--
function traverseR(context)
    local data = context.data
    local _type = context.type
    local mapped = {}
    if _type.is_prim then
        context.leaf = true
        context.value = Type:get(data, 0)
        context.mapped = nil
        table.insert(context.path, context.value)
        mapped = traverseC(context)
        table.remove(context.path)
        return mapped
    end
    for i,f in ipairs(type.fields) do
        a_mapped = {}
        context.value = _type:get(data, f.name)
        context.leaf = (f.type.is_prim or f.is_pointer)
        count = field:get_count(data)
        if not (count == nil) then
            context.mapped = nil
            for ii=0,count do
                context.value = _type:getA(data, f.name, ii)
                table.insert(context.path, context.value)
                res = traverseC(context)
                table.insert(a_mapped, res)
                table.remove(context.path)
            end
        end
        context.mapped = a_mapped
        table.insert(context.path, context.value)
        res = traverseC(context)
        table.insert(mapped, res)
        table.remove(context.path)
    end
    if _type.subtype_fn == nil then
        subtype = _type.subtype_fn(data, _type)
        if not (subtype == nil) then
            context.type = subtype
            a_mapped = traverseR(context)
            context.type = _type
            for i,it in ipairs(a_mapped) do
                table.insert(mapped, it)
            end
        end
    end
    return mapped
end

--[[
  traverse a data object of the given type

  \param data void* - data object
  \param type refl_type* - type object
  \param visit refl_visit_t - callback to run at each field node;
                              returning 0 at a given node prevents further recursion there
]]--
function Type:traverse(data, visit)
    context = {}
    path = {}
    context.data = data
    context.type = self
    context.path = path
    context.visit = visit
    return traverseR(context)
end

--[[
  map a data object of the given type

  \param data void* - data object
  \param type refl_type* - type object
  \param map refl_map_t - callback to map each field node
  \return array of pointers to the [recursively] mapped fields of type
          it is the user's responsibility to free this array
]]--
function Type:map(data, map)
    context = {}
    path = {}
    context.data = data
    context.type = self
    context.path = path;
    context.map = map
    return traverseR(context)
end

-- main export
refl = {}
refl.Type = Type
refl.Field = Field
refl.get_type = get_type
return refl
