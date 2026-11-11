#Table of Contents
1. [Terms](#terms)
2. [Purpose](#purpose)
3. [Usage](#usage)
   a. [Mapping ctype to ptype](#mapping)
   b. [Converting existing cobj to packed python obj](#to_pobj)
   c. [Creating a new unpacked python obj](#creating)
   d. [Modifying an unpacked python obj](#modifying)
   e. [Converting an unpacked python obj to cobj](#to_cobj)
   f. [Metadata](#metadata)

## Terms
- **ctype** - c primitive or struct type
- **ptype** - python class
- **dtype** - numpy structured array type
- **gtype** - *'generic type'*; represents a type that 
              can be constructed at runtime, with sections that can be 
              extended and removed from, before a final conversion to 
              dtype 
        (support for modification of dtypes is poor, so this is needed)
- **vtype** - gtype implementation with a fixed length start section 
              and variable length sections of offsets and data, 
              respectively
- **field metadata** - dictionary of field name -> property 
                   dictionary which exists in the ptype for a ctype. 
                   describes functionality for 'extension' to the 
                   underlying ctype struct (which the ptype can provide 
                   in addition to just acting as a wrapper)
- **field properties** - dictionary of properties for a field in the field 
                   metadata for the given ctype/ptype
- **varcount field** - a field that has a *count* property (note: not the 
                   *count* field itself). Such field is an array with 
                   variable length, where the items themselves can be 
                   either fixed in size or variable.
                   <br> 
                   --- note that said array may actually refer to the first
                   'count' items of a fixed size array (i.e. no packing
                   order), so the array itself is not necessarily 
                   variable length
- **varstruct field**  - a field with packing order that is a variable 
                   size structure OR an array of variable sized structures 
                   (typically varcount). 
                   In addition to the contents of such field, a separate
                   size/offset or array of sizes/offsets is needed in 
                   order to locate said contents.
                   The field may include an *offset* or *offsets* 
                   property which is the name of an existing field in 
                   the ctype that is a either single value, or flexible, 
                   zero-sized, or fixed-length array of at least 
                   *count* offsets.
                   If no *offset* or *offsets* property is specified,
                   (as will be the case when there are multiple varcount 
                   varsize fields) then such are assumed to be located 
                   after the offset(s) for the previous structure(s) in 
                   the packing order.
- **varsize field** - a varcount field with packing order or a varstruct
                   (non-array) field
- **cobj** - block of memory which is interpreted as a particular c 
             struct type
- **cbytes** - block of memory which is interpreted as an array of bytes
- **cdata** - block of memory which can be interpreted as cobj or cbytes

## Purpose
                                           
The ultimate goal of the mapper is *ctype* to *ptype* conversion, given
a cobj of the ctype. 

In this context a ctype is a c primitive type or structure type. 

The memory region allocated for a cobj which is to be interpreted/used 
as/casted to a particular structure ctype may extend beyond the size of 
the structure. Any data in the region past the structure end is 
inaccessible via the standard c structure field accessors (unless the 
last field is a flexible or zero-size array or any structure type with
such a last field). In this case there is a 'larger' structure at play
than that described by the ctype structure definition.

Cdata is therefore divided into 2 sections: a fixed size section which 
is the size of the structure ctype and a variable size section which 
consists of all data in the region past the structure end.
 
A ptype is a python class which wraps a cobj of structure ctype and an 
optional variable size part should it exist, and implements access to 
fields in the both the fixed and the variable length sections.

Each non-primitive ctype defined in c code should be mapped to a ptype
in python code. Each ptype should specify a metadata dictionary of field
names to property objects (dictionary) to describe the layout of any 
variable length section of underlying data. 

To convert a ctype object (CFFI) to ptype object:

- the ctype -> ptype map is used to get the corresponding ptype for the
  ctype
- the ctype field information (from ffi) along with the ptype field map 
  (metadata dictionary) is to build the representative vtype (with fixed
  length and variable length sections)
- the constructed vtype is converted to dtype
- an object of the ptype is created, which is a wrapper around numpy 
  structured array view of the ctype object with constructed dtype
        
## Usage 

### a. Mapping cdata/ctype to python obj/ptype:

1. Create the Python class that will map to the ctype:
   a. subclass ``Packable``.
   b. define a static dictionary ``field_map`` with field metadata/properties.
      
      The format of the dictionary is as follows:
      ```
      {
        '$option1': option1_value,
        '$option2': option2_value,
        ...
        'field1_name': { 'prop1': value1, 'prop2': value2, ... },
        'field2_name': { 'prop1': value1, 'prop2': value2, ... }
        ...
      }
      ```
     
      ``field_name`` may name an existing field in the [to be associated]
      ctype struct, or may name an entirely new field. New fields 
      serve as an extension to the ctype struct.
     
      The sourcing of data for a single field defined in the field map 
      may actually be the 'joint effort' of multiple fields defined in 
      the ctype struct; in such case the group of fields is represented
      by the singular field in the type map.
     
      See properties/options section for a list of possible properties
      and options.
           
2. Create all such python classes that will map to ctypes of descendant 
   members of the ctype.
   
3. Create a ``type_map`` dictionary mapping names of all such c structure 
   types to the corresponding python classes.
   
4. Call ``config()`` with the compiled ffi object and ``type_map`` created.

### b. Converting existing cobj to packed pobj

To convert an existing c object to a packed python object [of the mapped
``Packable`` subclass], load any raw cbytes data and call 
``from_cbytes()`` method of the desired ``Packable`` subclass with the 
cbytes data.
   
### c. Creating a new [unpacked] pobj

To create a new unpacked python object of a mapped ```Packable``` 
subclass type, simply call the constructor for that type. The default 
constructor takes no arguments.

### d. Modifying an unpacked pobj

A Python object which is converted from an existing c object is always
initially in the packed state. This means that all underlying data for 
the object is stored in a contiguous block, including any parts of the
object which can vary in size (variable sized arrays of structure or 
primitive, and variable sized structures).

Before the varying size parts of the object can be modified in such a 
way that would change the size (or format) of the underlying structure,
(i.e. appending or removing items), it must first be 'unpacked'.

Calling the ``unpack()`` method will unpack a packed object. The current
state can be verified by checking the ``packed`` boolean attribute. (i.e.
either *packed* (``packed==True``) or *unpacked* (``packed==False``)).

Once the object is unpacked, the underlying varying size parts of the 
object will be accessible as mutable lists (for variable sized array)
or objects which have been copied and separated from the contiguous 
packed data.

Any child objects of varying size must themselves be unpacked, and any
such descendant object, if the size or format of the underlying 
structure is to change. 

### e. Converting unpacked pobj to cobj

Before an unpacked Python object can be converted to a c object, it must
be re-packed. This also includes any and all descendant python objects 
of the object which are unpacked.

To pack an object, simply call its ``pack()`` method. If an object 
includes any external data fields, it will also need to be passed the
external data object(s) as argument(s). (this is so that the 
count(s) and/or offset(s) in the object, which are separate from the 
external object, are updated accordingly).

### f. Metadata

#### i. Properties

- ```'pack': (mode, idx)```

   specifies that the field consists of data that will be placed at the 
'end of the c structure' in the variable section, so as to extend the 
structure. The value for this property should be a tuple consisting of a 
string with the pack mode and an integer index which varies per pack mode.

  Pack modes:
  - ``'internal'`` - specifies that the field will be placed at the end 
     of the c structure for THIS corresponding object. 

     Multiple fields can be placed at the end of the struct, so the 
     order of the field is determined by the specified index.

  - ``'external'`` - specifies that the field will be placed at the end 
     of the c structure for another object, separate to that for this 
     one. The c structure for this object only contains data for fields 
     which describe/locate (and are used to source) the actual data for 
     the field in the external object.

     When the external object is mapped, it will then be necessary to 
     supply THIS object as an extra argument to the mapping function; the 
     specified index is therefore the expected index of this object as 
     the extra argument to the mapping function when it is used to map 
     the external object.

     ---note that if the field is an existing flexible or zero length array 
     at the end of the c struct the behavior is the same as if the field 
     did not exist.

- ``'count': '<count_field_name>' (1)`` <br>
  ``'count': '$remainder' (2)`` <br>
  ``'count': <function of c object> (read-only) (3)``

   specifies that the field is a variable length array, where the length 
is determined from:
    1. the value of the field with the specified name in the c object
    2. the number of elements of the field type that would fit
       within the remainder of space allocated for the structure
       within the parent structure
    3. a function of the c object

    Values of type 1 will work for fields in the c structure which are:
    - flexible array
    - zero length array
    - fixed length array <br>
    
    ...as well as new fields which do not exist in the c structure. The 
    behavior for a fixed length array is to map only the first count 
    elements and skip the remainder.

- ``'offsets': '<offsets_field_name>' or True`` <br>
  -------------------`` ('<offsets_field_name>' or True, bit_range_tuple) ``

   specifies that the field is an array of variable sized struct (or an 
   array of variable length array of primitive type) and therefore a 
   separate ``offsets`` field exists which is an array of int32s providing 
   the offsets of each object.

   There must also exist an accompanying ``type``, ``pointer``, or 
   ``pointers`` property for this field from which the type of the 
   objects in the array can be determined.

   If the field also has a ``count`` property, i.e. is variable length 
   array, then the field is variable length of array of variable size 
   struct, and therefore the corresponding separate offsets field is also 
   variable length array (but not necessarily variable length in the c 
   structure). 

   If the offsets property is specified as True, then this implies that 
   that there is neither an existing fixed length offsets array nor a 
   variable length one (i.e. flexible or zero-sized array) in the c 
   structure. In this case, the offsets are appended to the current end 
   of the *offsets section* of the mapped type being built, where the 
   type is built as such:

   - fixed section (with fields from the c structure)
   - variable length offsets section
   - variable length data section

   ...that is, at the end of the c struct/fixed section, all variable length 
   offsets arrays come first, followed by the actual data consisting of 
   variable length array of variable size struct.
 
- ``'pointers': '<name of unioned field of pointed type>'``

   specifies (along with 'offsets') that the field is an array of variable 
   size struct. 

   The property value must be the name of a field which is an array of 
   pointers to the objects at the offsets in the corresponding offsets 
   array field, typically in a union with the offsets field. From this 
   the type of the structures pointed to can be determined.

   Note that the type may be array of pointer to primitive. In this case 
   the field is interpreted as an array of variable length arrays of 
   primitive type (as variable length array of primitive type is the raw 
   bytes representation of a variable size struct).

- ``'offset': '<offset_field_name>'`` <br>
  ---------------- or ``('<offset_field_name>', bit_range_tuple)``
             
   specifies the offset of a single struct or variable size array of 
   fixed size struct, in the variable length data section, for 
   accompanying the pointer property
             
- ``'pointer': '<name of field of pointed type>'``

   specifies that the field is
   - without count - a single struct (fixed or variable size), in the
     variable length data section.
   - with count - an (variable size) array of fixed size struct,
     in the variable length data section.

   Unlike the ``pointers`` property, the ``pointer`` property does not need an
   accompanying ``offset`` property if the size of the preceding entity in 
   the variable size section can be determined by looking at its data. 
   (and, if array, does not need an accompanying offsets property as the 
    structs in the array are fixed size.)

   The property is needed for any new field (not existing in the c struct) 
   that the user desires placing at the end of the c struct (in the 
   variable length data section) as a fixed size struct or variable 
   length array of fixed size struct, so the type of the object or 
   objects in the array can be determined. (Alternatively, specify type 
   directly in the ``type`` property.)

   The name should be of a field which is intended to point to the object 
   or array of objects and thus has the type of the object(s). 

- ``'type': '<name of data type>'``

   specifies the type of the field data, as an alternative to the 
   ``pointers`` and ``pointer`` properties.

   - offsets + count + type = variable sized array of ``count`` var
                            sized structs of ``type``
   - count + type           = variable sized array of ``count`` fixed 
                            size structs of ``type``
   - offsets + type         = fixed size array of variable sized 
                            structs of ``type`` (count determined from 
                            existing c struct array field type)
   - type alone             = fixed size struct of ``type`` (in variable length 
                            data section)

- ``'size': '<name of field>'`` <br>
    -----------or ``'$last_offset'``

   specifies the name of a field in the c struct containing the size of 
   the structure if it is variable size. 

   Offsets alone are not enough to determine the actual -size- of the data 
   occupied by a variable sized section/array. If the [last] offset of 
   the last varsize array/struct in the structure is known, the size of the 
   entire containing structure can be determined if the size of that last 
   array/struct is known. However, sometimes it is not possible to 
   determine the size of the last struct (or any of the structs) by only 
   looking at its data. 

   Instead a separate field in the c struct may have the size. Such field 
   may also be located at the end of the offsets array where each offset 
   is increasing in sequence and the last offset is the size of the whole 
   struct, or offset of the end of the struct, rather than the offset of 
   an array element. In this case ``'$last_offset'`` can be specified as 
   the value. ---NOTE that the number of offsets in this case will be 1 
   plus the count [field value].

- ``'unitsize': <integer value>``

   specifies that the offsets are to be multiplied by an integer value to 
   get/set the actual values. That is-offsets are given in units of the 
   specified size.

- ``'varfmt': True or False``

   specifies, for an field of single or an array of fixed size 
   structure(s), that the structure has varying format, and therefore a 
   unique type must be generated for each instance of said structure.

   ---note: fixed size structure of varying format is enabled with the 
   ``$union`` option, allowing the 'variable length data section' to be 
   constructed in a preallocated region within the c structure itself 
   rather than as an extension.

- ``'partitions': dictionary of packed fields``

   allows array to be broken up into parts, where each part is a subarray
   of a separate type.

   Technically this is already supported with the other properties. Any 
   sequence of contiguous packed arrays (each containing a separate type 
   of elements) can also be considered as consisting of a larger containing 
   array:

   ```
   'array1': {
     'type': 'type1',
     'offsets': True,
     'count': 'count1',
     'pack': ('internal', 0)
   },
   'array2': {
     'type': 'type2',
     'offsets': True,
     'count': 'count2',
     'pack': ('internal', 1)
   },
   'array3': {
     'type': 'type3',
     'offsets': True,
     'count': 'count3',
     'pack': ('internal', 2)
   }
   ```

   ```
   [ [ array1 elems ], [ array2 elems ], [ array3 elems ] ] OR
   [array1 elems..., array2 elems..., array3 elems...]
   ```

   ...however if this were the case, the mapper does not recognize them 
   as such. 

   This motivates the usage of the ``partitions`` property:

   ```
   'items': {
     'type': 'base_type'
     'count': 'item_count'
     'pack': ('internal', 0),
     'partitions': {
           'array1': {
             'type': 'type1',
             'count': 'count1'
             'pack': ('internal', 0)
           },
           'array2': {
             'type': 'type2',
             'count': 'count2',
             'pack': ('internal', 1)
           },
           'array3': {
             'type': 'type3',
             'count': 'count3',
             'pack': ('internal', 2)
           }
     }
   }
   ```

   This has the following advantages over the other case:
   - purpose is clearer
   - the count for the parent array need not map to a field, and can be
     determined solely from the sum of the child array counts.
   - if the parent array count field -is- included, the sum of the child
     counts will be stored in that field when packing
   - pack order is relative to the group
   - offsets are implicitly partitions of the offsets for the parent 
     array 

ii) options:

- '$union': True or <field name>

specifies that the variable length section of the structure is to be 
constructed starting at:

- if True: offset 0
- if <field name>: the offset of the field with this name 
                   in the c structure

the variable length section will overwrite or 'union with' all fields 
past the given offset; in the case of offset 0, this is all fields and 
thus the entire struct

this option enables the format of the struct contents to vary while 
mantaining fixed size of the underlying c structure

- '$subclass': function of cdata returning [alternate] ptype

specifies that a potential alternate subclass is to be chosen for 
mapping the c structure. any function of the c data object of the 
corresponding c structure type can be used to determine an alternate 
class from the current one to use for mapping. if the function returns 
None, no new subclass is chosen and this class (the original) is used 
instead

this can recurse for each class that redirects to a new subclass,
enabling multiple levels of polymorphism

- '$subclass_id': name of field with integer value OR 
                  function of cdata returning integer value 
                  corresponding to an alternate ptype
                  
specifies that a potential alternate subclass is to be chosen for 
mapping the c structure. each [potential alternate] subclass that wishes
to participate must specify an static 'subclass_id' integer value in 
the class definition. the function can return any of the ids or None 
(which functions like for $subclass).

this method is used over $subclass_id when the base class and subclass
definitions are in separate files; in this case it is not possible to
use $subclass without introducing circular dependencies between imported 
classes


4) misc

a) field kind permutations
                                     
                                                          
ID| section | type      | array length | struct (or prim array) size | 
1 | fixed   | primitive | n/a          | n/a                         |
2 | fixed   | primitive | fixed        | n/a                         | 
3 | fixed   | primitive | fixed var    | n/a                         |
4 | fixed   | struct    | n/a          | fixed                       | 
5 | fixed   | struct    | fixed        | fixed                       |
6 | fixed   | struct    | fixed var    | fixed                       |
7*| var     | primitive | fixed        | n/a                         |
8*| var     | primitive | var          | n/a                         |
9 | var     | struct    | n/a          | fixed                       |
A | var     | struct    | n/a          | var                         |
B*| var     | struct    | fixed        | fixed                       |
C*| var     | struct    | fixed        | var                         |
D | var     | struct    | var          | fixed                       |
E | var     | struct    | var          | var                         |
F*| var     | pa        | fixed        | fixed                       |
G*| var     | pa        | fixed        | var                         |
H | var     | pa        | var          | fixed                       |
I | var     | pa        | var          | var                         |

* - not supported yet

section: fixed section  |           variable section          |
type   : prim  | struct |   prim  |    struct     | primarray |
alloc  :s | fa | s | fa | fa | va |  s  | fa | va |  fa |  va |
count  :na|f| v|na |f| v| f  | v  |  na |  f |  v |  f  |  v  |
chsize :<---------fixed---------->| f|v | f|v| f|v| f| v| f| v|
size   :<------fixed-------->| v  | f|v | f| var  | f|   var  |   
support:      yes       |   no    | yes | no | yes| no  | yes |

packed    = 7 thru I
varcount  = 3, 6, 8, D, E, H, I
varsize   = 8, D, E, H, I
                        A, C,  (G ?????)
varstruct = A, C, E
fixsize_array = 2, 3, 5, 6


9, A = single fixed or var size struct 
   (not varcount)
[B = fixed size array of fixed size struct]
[C = fixed sized array of var size struct]
D, E = var size array of fixed or var size struct
   (varcount)
   (offsets may be fix var in the fixed section but should treat
        the same)
         




notes on varsize_struct_to_vtype:
        # we expect each struct to be variable in size hence the need
        # for an offsets array
        # the span from the first offset to the second should consist
        # of the first struct in its entirety, from second to third 
        # the second, and so on. note that we do not know the exact
        # span of the last struct as there is no offset following 
        # the last; such an offset if it existed would correspond 
        # to the size of the struct (if the corresponding pointed
        # struct were 'zero sized' so it would not count as a 'last'
        # struct)
        # ALTERNATIVELY the struct could be interpreted as simply 
        # variable size -array- of primitive type (or more rarely,
        # fixed size struct). this is the case if the actual 
        # pointers themselves are primitive type, in which case 
        # usually more than one of the primitive type spans between
        # 2 offsets. the rule is, if child type is fixed size and at
        # least 2 of the type fit in the span between some 2 offsets
        # then the format of each child becomes variable-sized array
        # of the fixed size type.
        # for now we only handle the case where the child type is 
        # primitive             


 

"""
partition:

allows array to be broken up into parts, where each part is a subarray
of a separate type

technically this is already supported with basic metadata. any sequence
of contiguous packed arrays (each containing a separate type of elements)
can also be considered as consisting of a larger containing array:

'array1': {
  'type': 'type1',
  'count': 'count1',
  'pack': ('internal', 0)
},
'array2': {
  'type': 'type2',
  'count': 'count2',
  'pack': ('internal', 1)
},
'array3': {
  'type': 'type3',
  'count': 'count3',
  'pack': ('internal', 2)
}

[ [ array1 elems ], [ array2 elems ], [ array3 elems ] ] OR
[array1 elems..., array2 elems..., array3 elems...]

however if this were the case, the mapper does not recognize them as 
such. 

so we have the partitions property:

'items': {
  'type': 'base_type'
  'count': 'item_count'
  'pack': ('internal', 0),
  'partitions': {
        'array1': {
          'type': 'type1',
          'count': 'count1'
          'pack': ('internal', 0)
        },
        'array2': {
          'type': 'type2',
          'count': 'count2',
          'pack': ('internal', 1)
        },
        'array3': {
          'type': 'type3',
          'count': 'count3',
          'pack': ('internal', 2)
        }
  }
}

this has the following advantages over the other case:
  - purpose is clearer
  - the count for the parent array need not map to a field, and can be
        determined solely from the sum of the child array counts.
  - if the parent array count field -is- included, the sum of the child
        counts will be stored in that field when packing
  - pack order is relative to the group
  - offsets are contiguous in the group
        (currently it is necessary to specify the c field with the offsets 
         for even just a normal array of variable sized structs, but this 
         should not be necessary in the case that they are packed in the 
         variable section, where the offset of the offsets can be determined
         from the current offset section size)
  - future requirements may include the option to switch between the
        partitions and full array as representation, however for now the 
        parent array field/unpacked list is not included in the python object
        as it would require syncing with modifications to the partitions

=technically there is only support for:

  fixed count array of prim                   [1,2,3]
  var count array of prim                     [1,2,3,...]
  fixed count array of fixed size structure   [S,S,S]
  var count array of fixed size structure     [S,S,S,...]
  fixed count array of fixed size prim array  [[1,2],[3,4],[5,6]]
  var count array of fixed size prim array    [[1,2],[3,4],[5,6],...]
  fixed count array of var size structure     [S...,S..,S.]
  var count array of var size structure       [S...,S..,S.,...]
  fixed count array of var size prim array    [[1,2,3,...],[1,2,3,...],[1,2,3,...]]
  var count array of var size prim array      [[1,2,3,...],[1,2,3,...],[1,2,3,...],...]
  
=(it is possible to add support for fixed/var count array of var size struct array)

=the structure type can be made to map to a polymorphic ptype, a type of
which can be determined by the structure contents.  
"""



flow
====

ctype_to_vtype(ctype, obj):

- if ctype is primitive then simply generate the corresponding 
  primitive dtype vtype
- if ctype is array (of elements of same type) then 
  - extract the elements ctype and convert it with recursive call 
    to this function
  - get the dtype from the result vtype and generate the array dtype
    which is count of the result dtype
  - put the array dtype in a new dtype and return
- if ctype is a struct then
  - create the initial vtype for the struct
  - generate the 'fixed' part of the struct (which may be the whole struct):
    - for each field in the c structure definition which is not variable
      size (not flexible or zero length array) [or if variable count of 
      items is actually used and is fixed size array]:
      - if the field is a bitfield then skip for now and process it later
      - if the ctype of the field maps to a fixed ptype in the type map:
        (as will be the case for any structures detected as fixed size
	 at config init)
        - put the ptype in a vtype and use that as the field format
      - else (the ctype -should- be primitive type, array of primitive,
	      or array of fixed size struct)
        - convert it with recursive call to this function, and put
	  in vtype and use as field format
        - if the recursive call failed then skip this field
      - (EDIT: what if the field is var format struct? accordingly to
               this logic, currently fields in the fixed part which are 
	       marked as var format are not processed as such and 
	       therefore take only the form of their fixed part)
      - append a new field with the c field name, determined format, 
        and c field offset-to the fixed section of the vtype  
    - manually set the fixed part length of the vtype to the size of 
      the c structure
    - one case that will occur is if a field located at 'the end' of
      the c structure that is a non-array variable size structure type 
      (any preceding fields in the fixed section of the structure which 
       are of c structure type and are intended to map to a variable 
       size python structure type [as directed by metadata] will map to a 
       ptype which ONLY includes the fixed part of that type)
      fields at the end of the c structure are those such that the offset
      of the field PLUS the -fixed- size of its c type is equal to the 
      -fixed- size of this [containing/parent] c structure type
      
      in this case, from the fixed part length of the vtype is subtracted 
      the largest sized end field (though there would usually be an issue
      if an anonymous structure at the end consisting of primitive or 
      some other type followed by a smaller structure type was in an 
      anonymous union with a larger structure type also at the end, 
      because the preceding primtive or other type field would be 
      completely lost). this way the size of the constructed dtype for 
      the fixed section will fit exactly the fields constructed. the
      variable sized structure field will have been skipped in this 
      section and will instead be processed when building the variable
      size section(s) of the vtype
  - generate the variable part of the struct (if such fields exist):
    - get the type metadata information for the struct type; 
      [pass the obj to the constructor for the typeinfo so if the type 
      metadata defines an alternate subclass[id] function/field then the
      object will determine which subclass to use]
      
    - use the object, any external objects, type info, and the allocated
    
  
  
      

      
      
  - if metadata marks the struct as variable size or variable format:
  
============

update 1/10/22 - need to have the pobj as the first argument to lambda 
functions specified in properties for setting the size/count. if the 
cobj is used the user may have written a function which attempts to use 
offsets or pointers data which are invalid at the invocation of the 
lambda i.e. during or before packing (unless sync_cdata has been invoked)
