local _GopA_ = { shamt = 12, mask = 0xFFF } -- GOOL operand A
local _GopB_ = { shamt = 0,  mask = 0xFFF } -- GOOL operand B
local _GopL_ = _GopB_
local _GopR_ = _GopA_
local _GopS_ = _GopA_
local _GopD_ = _GopB_

local _Im14_ = { shamt = 0,  mask = 0x3FFF }-- 14 bit immediate code offset or state id
local _Im10_ = { shamt = 0,  mask = 0x3FF } -- 10 bit immediate branch offset
local _Os_   = { shamt = 22, mask = 3 }     -- 3 bit control flow operation subtype
local _Cond_ = { shamt = 20, mask = 3 }     -- 3 bit operation condition mode
local _Ri_   = { shamt = 14, mask = 0x3F }  -- 6 bit 'register' index = object field index
local _Vs_   = { shamt = 10, mask = 0xF }   -- 4 bit variable skip count

local PAD_Gop = { shamt = 0, mask = 0xFFF }
local PAD_Pct = { shamt = 12, mask = 3 }
local PAD_Sct = { shamt = 14, mask = 3 } 
local PAD_Dir = { shamt = 16, mask = 0xF }
local PAD_Flg = { shamt = 20, mask = 1 }

local MSC_Gop = { shamt = 0, mask = 0xFFF } -- argument
local MSC_Idx = { shamt = 12, mask = 0x7 }  -- data index
local MSC_Pso = { shamt = 15, mask = 0x1F } -- primary sub-operation
local MSC_Sso = { shamt = 20, mask = 0xF }  -- secondary sub-operation

local CVM_Gop = { shamt = 0, mask = 0xFFF } 
local CVM_Lnk = { shamt = 12, mask = 0x7 }  -- link index
local CVM_Cdi = { shamt = 15, mask = 0x3F } -- color data index

local ANI_FrG = { shamt = 0, mask = 0xFFF } -- anim frame gool operand
local ANI_FrI = { shamt = 0, mask = 0x7F }  -- anim frame immediate operand
local ANI_Seq = { shamt =  7, mask = 0x1FF }-- anim sequence index
local ANI_Wt = { shamt = 16, mask = 0x3F }  -- anim wait time
local ANI_Flp = { shamt = 22, mask = 3 }    -- anim flip mode

local VEC_Gop = { shamt = 0, mask = 0xFFF } -- vector gool operand input 
local VEC_ViA = { shamt = 12, mask = 7 }    -- vector index A
local VEC_ViB = { shamt = 15, mask = 7 }    -- vector index B
local VEC_Pso = { shamt = 18, mask = 7 }    -- primary [vector] sub-operation
local VEC_ViC = { shamt = 21, mask = 7 }    -- vector index C

local JAL_Vs = { shamt = 20, mask = 0xF }   -- JAL variable skip count 

local EVT_Gop = { shamt = 0, mask = 0xFFF } -- event gool operand input (event)
local EVT_Cnd = { shamt = 12, mask = 0x3F } -- event condition = register index
local EVT_ArC = { shamt = 18, mask = 7 }    -- event num args sent to recipient
local EVT_Rec = { shamt = 21, mask = 7 }    -- event recipient = link index

local CHD_SpC = { shamt = 0, mask = 0x3F }  -- children spawn count
local CHD_Sub = { shamt =  6, mask = 0x3F } -- children objects' subtype
local CHD_Typ = { shamt = 12, mask = 0xFF } -- children objects' type
local CHD_ArC = { shamt = 20, mask = 0xF  }

local SND_Gop = { shamt = 0, mask = 0xFFF }
local SND_Ri  = { shamt = 12, mask = 0x3F } -- sound flags = 6 bit 'register' index = obj field index
local SND_Vol = { shamt = 20, mask = 0xF }  -- sound volume?

-- operand types
local function gRefI(op)
	return { name = "gRefI", op = op }
end
local function gRefO(op)
	return { name = "gRefO", op = op }
end
local function gRefX(op)
	return { name = "gRefX", op = op }
end
local function gIm(op)
	return { name = "gIm", op = op }
end
local function gReg(op)
	return { name = "gReg", op = op }
end
local function gLnk(op)
	return { name = "gLnk", op = op }
end
local function gVec(op)
	return { name = "gVec", op = op }
end
local function gCol(op)
	return { name = "gCol", op = op }
end
local function gCofs(op)
	return { name = "gCofs", op = op }
end

local instructions = {
------------------------------------------------------------
-- add, mult, and non-commutative arithmetic              --
-- string.format:  OP gopr, gopl                                 --
------------------------------------------------------------
{ name = "ADD",  operands = { gRefI(_GopR_), gRefI(_GopL_) } },
{ name = "SUB",  operands = { gRefI(_GopR_), gRefI(_GopL_) } },
{ name = "MULT", operands = { gRefI(_GopR_), gRefI(_GopL_) } },
{ name = "DIV",  operands = { gRefI(_GopR_), gRefI(_GopL_) } },
{ name = "MOD",  operands = { gRefI(_GopR_), gRefI(_GopL_) } },
{ name = "SHA",  operands = { gRefI(_GopR_), gRefI(_GopL_) } },

------------------------------------------------------------
-- commutative arithmetic                                 --
-- string.format:  OP gopa, gopb                                 --
------------------------------------------------------------
{ name = "CEQ",  operands = { gRefI(_GopA_), gRefI(_GopB_) } },
{ name = "ANDL", operands = { gRefI(_GopA_), gRefI(_GopB_) } },
{ name = "ANDB", operands = { gRefI(_GopA_), gRefI(_GopB_) } },
{ name = "ORL",  operands = { gRefI(_GopA_), gRefI(_GopB_) } },
{ name = "ORB",  operands = { gRefI(_GopA_), gRefI(_GopB_) } },
{ name = "SLT",  operands = { gRefI(_GopA_), gRefI(_GopB_) } },
{ name = "SLE",  operands = { gRefI(_GopA_), gRefI(_GopB_) } },
{ name = "SGT",  operands = { gRefI(_GopA_), gRefI(_GopB_) } },
{ name = "SGE",  operands = { gRefI(_GopA_), gRefI(_GopB_) } },
{ name = "XOR",  operands = { gRefI(_GopA_), gRefI(_GopB_) } },
{ name = "TST",  operands = { gRefI(_GopA_), gRefI(_GopB_) } },
{ name = "NOTB", operands = { gRefI(_GopA_), gRefI(_GopB_) } },

------------------------------------------------------------
-- unary arithmetic                                       --
-- string.format:  OP gops, gopd                                 --
------------------------------------------------------------
{ name = "NOTL", operands = { gRefI(_GopS_), gRefO(_GopD_) } },  -- src val, dst ref
{ name = "ABS", operands = {  gRefI(_GopS_), gRefO(_GopD_) } },

------------------------------------------------------------
-- misc arithmetic functions                              --
-- string.format:  OP gopa, gopb                                 --
------------------------------------------------------------
{ name = "RND", operands = {  gRefI(_GopA_), gRefI(_GopB_) } },
{ name = "TRI", operands = {  gRefI(_GopA_), gRefX(_GopB_) } },
{ name = "SPD", operands = {  gRefI(_GopA_), gRefI(_GopB_) } },
{ name = "PRS", operands = {  gRefI(_GopA_), gRefI(_GopB_) } },  -- period = GopA/2, phase = GopB
{ name = "SSAW", operands = { gRefI(_GopA_), gRefI(_GopB_) } },
{ name = "ANGD", operands = { gRefI(_GopR_), gRefI(_GopL_) } },
{ name = "APCH", operands = { gRefI(_GopR_), gRefI(_GopL_) } },
{ name = "ROT", operands = {  gRefI(_GopR_), gRefI(_GopL_) } },

------------------------------------------------------------
-- memory operations                                      --
-- string.format:  OP gops, gopd                                 --
--          OP gopa, gopb                                 --
--          OP im14, ri                                   --
------------------------------------------------------------
{ name = "MOVE", operands = { gRefI(_GopS_), gRefO(_GopD_) } },
{ name = "LEA",  operands = { gRefI(_GopS_), gRefO(_GopD_) } },
{ name = "PSHV", operands = { gRefI(_GopA_), gRefI(_GopB_) } },
{ name = "PSHP", operands = { gRefI(_GopA_), gRefI(_GopB_) } },
{ name = "MOVC", operands = { gCofs(_Im14_),    gReg(_Ri_) } },

------------------------------------------------------------
-- control flow                                           --
-- string.format: 0x82 type, cond, ri, **                        --
-- BRA =      .    0, cond, ri, vs, im10                  --
-- CST =      .    1, cond, ri, im14                      --
-- RET =      .    2, cond, ri                            --
-- JAL =   0x86             vs, im14                      --
-- RST =   0x88 type, cond, ri, **                        --
-- RSF =   0x89    .     .   .                            --
------------------------------------------------------------
{ name = "BRA", operands = {  gIm(_Im10_), gIm(_Vs_) } },
{ name = "BNEZ", operands = { gReg(_Ri_),  gIm(_Im10_), gIm(_Vs_) } },
{ name = "BEQZ", operands = { gReg(_Ri_),  gIm(_Im10_), gIm(_Vs_) } },
{ name = "BRAC", operands = { gIm(_Im10_), gIm(_Vs_) } },
{ name = "CST",  operands = {  gIm(_Im14_) } },
{ name = "CSNZ", operands = { gReg(_Ri_), gIm(_Im14_) } },
{ name = "CSEZ", operands = { gReg(_Ri_), gIm(_Im14_) } },
{ name = "CSTC", operands = { gIm(_Im14_) } },
{ name = "RET",  operands = { } },
{ name = "RTNZ", operands = { gReg(_Ri_) } },
{ name = "RTEZ", operands = { gReg(_Ri_) } },
{ name = "RETC", operands = { } },
{ name = "SCND", operands = { } },
{ name = "SCNZ", operands = { gReg(_Ri_) } },
{ name = "SCEZ", operands = { gReg(_Ri_) } },
{ name = "CCND", operands = { } },

{ name = "JAL",  operands = { gIm(_Im14_), gIm(JAL_Vs) } },

{ name = "GBNT", operands = { gReg(_Ri_), gIm(_Im10_), gIm(_Vs_) } }, -- change _guard (or otherwise _branch when cond == 0) if cond (_not eq. } }, != 0 with guard = _true
{ name = "GBZT", operands = { gReg(_Ri_), gIm(_Im10_), gIm(_Vs_) } }, -- change _guard (or otherwise _branch when cond != 0) if cond == 0 (_zero } }, with guard = _true
{ name = "GBNF", operands = { gReg(_Ri_), gIm(_Im10_), gIm(_Vs_) } }, -- change _guard (or otherwise _branch when cond == 0) if cond (_not eq. } }, != 0 with guard = _true
{ name = "GBZF", operands = { gReg(_Ri_), gIm(_Im10_), gIm(_Vs_) } }, -- change _guard (or otherwise _branch when cond != 0) if cond == 0 (_zero } }, with guard = _true
{ name = "RST",  operands = { gIm(_Im14_) } },                        -- _return _state transition with guard = _true
{ name = "RSNT", operands = { gReg(_Ri_), gIm(_Im14_) } },            -- _return _state transition if cond (_not eq. } }, != 0 with guard = _true 
{ name = "RSZT", operands = { gReg(_Ri_), gIm(_Im14_) } },            -- _return _state transition if cond == 0 (_zero } }, with guard = _true 
{ name = "RSCT", operands = { gIm(_Im14_) } },                        -- _return _state transition based on prev _cond with guard = _true 
{ name = "RSF",  operands = { gIm(_Im14_) } },                        -- _return _state transition with guard = _true
{ name = "RSNF", operands = { gReg(_Ri_), gIm(_Im14_) } },            -- _return _state transition if cond (_not eq. } }, != 0 with guard = _true 
{ name = "RSZF", operands = { gReg(_Ri_), gIm(_Im14_) } },            -- _return _state transition if cond == 0 (_zero } }, with guard = _true 
{ name = "RSCF", operands = { gIm(_Im14_) } },                        -- _return _state transition based on prev _cond with guard = _true 
{ name = "RNT",  operands = { } },                                    -- _return _null state transition with guard = _true
{ name = "RNNT", operands = { gReg(_Ri_) } },                         -- _return _null state transition if cond (_not eq. } }, != 0 with guard = _true 
{ name = "RNZT", operands = { gReg(_Ri_) } },                         -- _return _null state transition if cond == 0 (_zero } }, with guard = _true 
{ name = "RNCT", operands = { } },                                    -- _return _null state transition based on prev _cond with guard = _true 
{ name = "RNF", operands = { } },                                     -- _return _null state transition with guard = _true
{ name = "RNNF", operands = { gReg(_Ri_) } },                         -- _return _null state transition if cond (_not eq. } }, != 0 with guard = _true 
{ name = "RNZF", operands = { gReg(_Ri_) } },                         -- _return _null state transition if cond == 0 (_zero } }, with guard = _true 
{ name = "RNCF", operands = { } },                                    -- _return _null state transition based on prev _cond with guard = _true 
{ name = "EBT", operands = { } },                                     -- _event [service] '_begin' and set guard to _true
{ name = "EBNT", operands = { gReg(_Ri_) } },                         -- _event [service] '_begin' if cond (_not eq. } }, != 0 and set guard to _true
{ name = "EBZT", operands = { gReg(_Ri_) } },                         -- _event [service] '_begin' if cond == 0 (_zero } }, and set guard to _true
{ name = "EBCT", operands = { } },                                    -- _event [service] '_begin' based on prev _cond and set guard to _true
{ name = "EBF", operands = { } },                                     -- _event [service] '_begin' and set guard to _true
{ name = "EBNF", operands = { gReg(_Ri_) } },                         -- _event [service] '_begin' if cond (_not eq. } }, != 0 and set guard to _true
{ name = "EBZF", operands = { gReg(_Ri_) } },                         -- _event [service] '_begin' if cond == 0 (_zero } }, and set guard to _true
{ name = "EBCF", operands = { } },                                    -- _event [service] '_begin' based on prev _cond and set guard to _true

------------------------------------------------------------
-- vector operations                                      --
-- string.format: 0x85 VEC_ViC,VEC_Pso,VEC_ViB,VEC_ViA,VEC_Gop   --
--         0x8E ...                                       --
--                                                        --
-- OP = 0x85                                              --
-- PATH: VEC_Pso = 0 | VEC_Gop = path prog                --
------------------------------------------------------------       
------------------------------------------------------------   
--                                                        --
-- PROJ: VEC_Pso = 1 | VEC_Gop = out screen coord 2d vec  --
--                     VEC_ViA = in 3d vec                --
--                     VEC_ViB = out 3d orthographic vec  --
-- Display string.format: PROJ [out 2d], [in 3d], [out 3d orth]  --
--                                                        --
-- APCR: VEC_Pso = 2 | VEC_Gop = rot speed                -- 
--                     VEC_ViA = dst rot angle            --
-- Display string.format: APCR [rot speed], [dst rot angle]      --
--                                                        --
-- MATT: VEC_Pso = 4 | VEC_Gop = in vector z value        --
-- MTRT: VEC_Pso = 5 | stack = ..., in vec x, in vec y    --
--                     VEC_ViA = trans vec in (for trans) --
--                     VEC_ViB = transformed vec out      --
-- Display string.format: MATT [in vec z], [tr vec in],[vec out] --
--                 MTRT ...                               --
--                                                        --
-- TVTX: VEC_Pso = 6 | VEC_Gop = vertex index             --
--                     VEC_ViA = transformed pt (vec) out --
--                     VEC_ViD = link index (has model)   --
-- Display string.format TVTX [lnk indx], [vrt indx], [vec out]  --
--                                                        --
-- OP = 0x8E                                              --
-- RBND: VEC_Pso = 0 | VEC_Gop = dir vec out              --
--                     VEC_ViA = dir vec in               --
--                     VEC_ViB = trans vec out            --
-- Display string.format RBND [vec out], [vec in], [trans out]   --
------------------------------------------------------------
{ name = "PATH", operands = { gRefI(VEC_Gop), gVec(VEC_ViA) } },               
{ name = "PROJ", operands = { gRefI(VEC_Gop), gVec(VEC_ViA), gVec(VEC_ViB) } }, 
{ name = "APCR", operands = { gRefI(VEC_Gop), gVec(VEC_ViA) } },                -- approach obj target rot 
{ name = "MATT", operands = { gRefI(VEC_Gop), gVec(VEC_ViA), gVec(VEC_ViB) } }, -- linear/matrix transstring.formation
{ name = "MTRT", operands = { gRefI(VEC_Gop), gVec(VEC_ViA), gVec(VEC_ViB) } }, -- linear/matrix transstring.formation using target rot as basis
{ name = "TVTX", operands = { gLnk(VEC_ViC), gRefI(VEC_Gop), gVec(VEC_ViA) } }, -- linear/matrix transstring.formation on svtx vertex
{ name = "SNMT", operands = { gRefI(VEC_Gop), gVec(VEC_ViA), gVec(VEC_ViB) } }, -- matrix transform for sounds

{ name = "RBND", operands = { gRefI(VEC_Gop), gVec(VEC_ViA), gVec(VEC_ViB) } }, -- rebound vector from solid surface
{ name = "VCU1", operands = { gRefI(VEC_Gop), gVec(VEC_ViB) } },
{ name = "VCU2", operands = { gRefI(VEC_Gop), gVec(VEC_ViB) } },    
{ name = "VCU3", operands = { gRefI(VEC_Gop), gVec(VEC_ViB) } },
{ name = "VCU4", operands = { gRefI(VEC_Gop), gVec(VEC_ViB) } }, 
{ name = "VCU5", operands = { } }, 

------------------------------------------------------------
-- misc operations                                        --
-- string.format:                                                --
------------------------------------------------------------
{ name = "EARG", operands = { gRefI(MSC_Gop), gIm(MSC_Sso) } },                -- _event _a_r_gument
{ name = "DIST", operands = { gLnk(MSC_Idx),  gIm(MSC_Sso) } },                -- _d_i_s_tance between obj trans and link trans(flags in Sso } },
{ name = "VDST", operands = { gRefI(MSC_Gop), gLnk(MSC_Idx), gIm(MSC_Sso) } }, -- _d_i_s_tance between vect and link trans(flags in Sso } },
{ name = "AGDP", operands = { gRefI(MSC_Gop), gLnk(MSC_Idx) } },               -- _an_gular _dis_placement between ang and obj link ang 
{ name = "LR",   operands = { gRefI(MSC_Gop), gLnk(MSC_Idx) } },               -- _load _register [from link]
{ name = "SR",   operands = { gRefI(MSC_Gop), gLnk(MSC_Idx) } },               -- _set _register [of link]
{ name = "LXAG", operands = { gLnk(MSC_Idx) } },                               -- [retrieve] _loo_k _an_gle between obj. and link in XZ plane
{ name = "FIND", operands = { gRefI(MSC_Gop) } },                              -- _f_i_n_d object with id
{ name = "SZON", operands = { gLnk(MSC_Idx),  gRefI(MSC_Gop) } },              -- _set current _z_o_ne of link to zone containing vector
{ name = "SNRS", operands = { gRefI(MSC_Gop), gIm(MSC_Idx) } },                -- _set (or clear } }, _no _re_spawn bit of obj w/id 
{ name = "TNRS", operands = { gRefI(MSC_Gop) } },                              -- _test _no _re_spawn bit of obj w/id
{ name = "SXB",  operands = { gRefI(MSC_Gop) } },                              -- _set _exists/spawned _bit
{ name = "CXB",  operands = { gRefI(MSC_Gop) } },                              -- _clear _exists/spawned _bit
--{ name = "TXB", operands = {  gRefI(MSC_Gop) } },                              -- _test _exists/spawned _bit
{ name = "SB3",  operands = { gRefI(MSC_Gop) } },                              -- _set spawn status _bit _3
{ name = "CB3",  operands = { gRefI(MSC_Gop) } },                              -- _clear spawn status _bit _3
{ name = "TB3",  operands = { gRefI(MSC_Gop) } },                              -- _test spawn status _bit _3
{ name = "PSSB", operands = { gRefI(MSC_Gop) } },                              -- _preserve _spawn _status _bits
{ name = "RSSB", operands = { gRefI(MSC_Gop) } },                              -- _release _spawn _status _bits
{ name = "SPTB", operands = { gRefI(MSC_Gop) } },                              -- _set _preserve spawn status at _transition between levels _bit
{ name = "CPTB", operands = { gRefI(MSC_Gop) } },                              -- _clear _preserve spawn status at _transition between levels _bit
{ name = "TPTB", operands = { gRefI(MSC_Gop) } },                              -- _test _preserve spawn status at _transition between levels _bit
{ name = "SAVE", operands = { } },                                             -- _s_a_v_e level state
{ name = "LOAD", operands = { } },                                             -- [re]_l_o_a_d level state
{ name = "SPAR", operands = { gRefI(MSC_Gop) } },                              -- _set new _p_a_rent
{ name = "UNKB", operands = { gRefI(MSC_Gop) } },
{ name = "ZONE", operands = { gLnk(MSC_Idx),  gRefI(MSC_Gop) } },              -- _set object _li_n_k
{ name = "SNDU", operands = { } },
{ name = "SNDC", operands = { gRefI(MSC_Gop) } },
{ name = "TRMO", operands = { } },                                             -- _te_r_minate all _objects in current zone and its neighbors
{ name = "LYAG", operands = { gRefI(MSC_Gop), gLnk(MSC_Idx) } },               -- [retrieve] _loo_k _an_gle between vector and link in _Y -axis-                                     
{ name = "LLEV", operands = { gRefI(MSC_Gop) } },                              -- _load a new _l_e_vel
{ name = "SNSD", operands = { gRefI(MSC_Gop) } },                              -- _seek disc to location of _n_s_d file
{ name = "GLBI", operands = { } },                                             -- _g_lo_bal _initialize ([re]init all globals } },
{ name = "BACE", operands = { gLnk(MSC_Idx), gRefI(MSC_Gop), gLnk(MSC_Pso) } },-- _broadcast _asynchronously handled collision event
{ name = "TCOL", operands = { gLnk(MSC_Idx), gRefI(MSC_Gop) } },               -- _test point for _c_o_llision with object 
{ name = "CARD", operands = { gIm(MSC_Pso),  gRefI(MSC_Gop) } },               -- memory _c_a_r_d routine

{ name = "GLBR", operands = { gRefI(_GopS_) } },
{ name = "GLBW", operands = { gRefI(_GopS_),  gRefI(_GopD_) } },
{ name = "CVMR", operands = { gLnk(CVM_Lnk),  gCol(CVM_Cdi) } },
{ name = "CVMW", operands = { gLnk(CVM_Lnk),  gCol(CVM_Cdi), gRefI(CVM_Gop) } },
{ name = "ANID", operands = { gRefI(_GopS_),  gRefO(_GopD_) } },
{ name = "ANIS", operands = { gIm(ANI_FrI),   gIm(ANI_Seq),  gIm(ANI_Wt),  gIm(ANI_Flp) } },
{ name = "ANIF", operands = { gRefI(ANI_FrG), gIm(ANI_Wt),   gIm(ANI_Flp) } },
{ name = "EVNT", operands = { gRefI(EVT_Gop), gLnk(EVT_Rec), gIm(EVT_ArC), gReg(EVT_Cnd) } },
{ name = "EVNB", operands = { gRefI(EVT_Gop), gLnk(EVT_Rec), gIm(EVT_ArC), gReg(EVT_Cnd) } },
{ name = "EVNU", operands = { gRefI(EVT_Gop), gLnk(EVT_Rec), gIm(EVT_ArC), gReg(EVT_Cnd) } },
{ name = "CHLD", operands = { gIm(CHD_SpC),   gIm(CHD_Typ),  gIm(CHD_Sub), gIm(CHD_ArC) } },
{ name = "CHLF", operands = { gIm(CHD_SpC),   gIm(CHD_Typ),  gIm(CHD_Sub), gIm(CHD_ArC) } },
{ name = "NTRY", operands = { gRefI(_GopB_),  gRefI(_GopA_) } }, -- TODO: expand NTRY
{ name = "SNDA", operands = { gRefI(_GopA_),  gRefI(_GopB_) } },
{ name = "SNDB", operands = { gRefI(SND_Gop), gReg(SND_Ri),  gIm(SND_Vol) } },
{ name = "PAD",  operands = { gRefI(PAD_Gop), gIm(PAD_Pct),  gIm(PAD_Sct), gIm(PAD_Dir), gIm(PAD_Flg) } },

{ name = "NOP", operands = { } },
{ name = "GDBG", operands = { } }, -- for now
{ name = "UNK", operands = { } },
{ name = "ILL", operands = { } },

}


local disGOOL_CFL = {
{ "BRA" , "BNEZ", "BEQZ", "BRAC"},
{ "CST" , "CSNZ", "CSEZ", "CSTC"},
{ "RET" , "RTNZ", "RTEZ", "RETC"},
{ "SCND", "SCNZ", "SCEZ", "CCND"} 
}

local disGOOL_RSTT = {
{ "NOP" , "GBNT", "GBZT", "NOP" },
{ "RST" , "RSNT", "RSZT", "RSCT"},
{ "RNT" , "RNNT", "RNZT", "RNCT"},
{ "EBT" , "EBNT", "EBZT", "EBCT"} 
}

local disGOOL_RSTF = {
{ "NOP" , "GBNF", "GBZF", "NOP" },
{ "RSF" , "RSNF", "RSZF", "RSCF"},
{ "RNF" , "RNNF", "RNZF", "RNCF"},
{ "EBF" , "EBNF", "EBZF", "EBCF"} 
}

local disGOOL_VECA = {
  "PATH", "PROJ", "APCR", "NOP" , "MATT", "MTRT", "TVTX", "SNMT"
}

local disGOOL_VECB = {
  "RBND", "VCU1", "VCU2", "VCU3", "VCU4", "VCU5", "ILL" , "ILL" 
}
  
local disGOOL_MSC_SBW = {
  "SB3" , "CB3" , "SPTB", "CPTB", "PSSB", "RSSB", "NOP" , "NOP" ,
  "SXB" , "CXB" , "ILL" , "ILL" , "ILL" , "ILL" , "ILL" , "ILL" 
}

local disGOOL_MSC_SBR = {
  "NOP" , "TNRS", "TB3" , "TPTB", "ILL" , "ILL" , "ILL" , "ILL" 
}

local disGOOL_MSC_MSCB = {
  "SAVE", "LOAD", "SPAR", "UNKB", "ZONE", "SNDU", "SNDC", "TRMO",
  "LYAG", "LLEV", "SNSD", "GLBI", "ILL" , "ILL" , "ILL" , "ILL" 
}
  
local disGOOL_MSC = { 
  "EARG", "DIST", "AGDP", "LR"  , "SR"  , "LXAG", "VDST", "FIND",
  "SNRS", "SZON", "SBW" , "SBR" , "MSCB", "BACE", "TCOL", "CARD"
}

local disGOOL = {
  "ADD" , "SUB" , "MULT", "DIV" , "CEQ" , "ANDL", "ORL" , "ANDB", 
  "ORB" , "SLT" , "SLE" , "SGT" , "SGE" , "MOD" , "XOR" , "TST" , 
  "RND" , "MOVE", "NOTL", "TRI" , "LEA" , "SHA" , "PSHV", "NOTB", 
  "MOVC", "ABS" , "PAD" , "SPD" , "MSC" , "PRS" , "SSAW", "GLBR",
  "GLBW", "ANGD", "APCH", "CVMR", "CVMW", "ROT" , "PSHP", "ANID",
  "ILL" , "ILL" , "ILL" , "ILL" , "ILL" , "ILL" , "ILL" , "ILL" ,
  "ILL" , "ILL" , "ILL" , "ILL" , "ILL" , "ILL" , "ILL" , "ILL" ,
  "ILL" , "ILL" , "ILL" , "ILL" , "ILL" , "ILL" , "ILL" , "ILL" ,
  "ILL" , "ILL" , "ILL" , "ILL" , "ILL" , "ILL" , "ILL" , "ILL" ,
  "ILL" , "ILL" , "ILL" , "ILL" , "ILL" , "ILL" , "ILL" , "ILL" ,
  "ILL" , "ILL" , "ILL" , "ILL" , "ILL" , "ILL" , "ILL" , "ILL" ,
  "ILL" , "ILL" , "ILL" , "ILL" , "ILL" , "ILL" , "ILL" , "ILL" ,
  "ILL" , "ILL" , "ILL" , "ILL" , "ILL" , "ILL" , "ILL" , "ILL" ,
  "ILL" , "ILL" , "ILL" , "ILL" , "ILL" , "ILL" , "ILL" , "ILL" ,
  "ILL" , "ILL" , "ILL" , "ILL" , "ILL" , "ILL" , "ILL" , "ILL" ,
  "ILL" , "ILL" , "ILL" , "ILL" , "ILL" , "ILL" , "ILL" , "ILL" ,
  "DBG" , "UNK" , "CFL" , "ANIS", "ANIF", "VECA", "JAL" , "EVNT",
  "RSTT", "RSTF", "CHLD", "NTRY", "SNDA", "SNDB", "VECB", "EVNB", 
  "EVNU", "CHLF", "ILL" , "ILL" , "ILL" , "ILL" , "ILL" , "ILL" 
}

function GoolFormatRef(ref, mode)
	local str = ""
	if (ref & 0xFFF) == 0xE1F then
		if mode == 0 then
			str = "pop()"
		elseif mode == 1 then
			str = "push()"
		elseif mode == 2 then
			str = "inout()"
		end
	elseif (ref & 0xE00) == 0xE00 then
		reg = ref & 0x1FF
		str = string.format("obj[0x%x]", (reg*4)+0x60)
	elseif (ref & 0x800) == 0 then
 		ireg = ref & 0x3FF
		if (ref & 0x400) == 0 then
			str = string.format("ireg[0x%x]", (ireg*4))
		else
			str = string.format("pool[0x%x]", (ireg*4))
		end
	elseif (ref & 0x400) == 0 then
		if (ref & 0x200) == 0 then
			integer = (ref & 0xFF)
			if not (integer == 0) then
				sign = (ref & 0x100) >> 8
				if not (sign == 0) then
					integer = 0x100 - integer
					str = string.format("-0x%x00", integer)
				else
					str = string.format("0x%x00", integer)
				end
			else
				str = "0"
			end
		elseif (ref & 0x100) == 0 then
			integer = (ref & 0x70) >> 4;
			fraction = (ref & 0xF);
			if not ((ref & 0x7F) == 0) then
				sign = (ref & 0x80) >> 7
				if not (sign == 0) then
					integer = 8 - integer;
					fraction = 16 - fraction;
					str = string.format("-%d.%-4.4d", integer, fraction*625)
				else
					str = string.format("%d.%-4.4d", integer, fraction*625)
				end
			else
				str = "0"
			end
		elseif (ref & 0x80) == 0 then
			sign = (ref & 0x40) >> 6
			offset = ref & 0x3F
			if not (sign == 0) then
				offset = 0x40 - offset
				str = string.format("-0x%x($fp)", offset*4)
			else
				str = string.format("0x%x($fp)", offset*4)
			end
		elseif ref == 0xBE0 then
			str = "0"
		elseif (ref == 0xBF0) then  
			str = "pop(), pop()"    
		else           
			str = "INVALID OPERAND"
		end        
	else 
		lnk = (ref & 0x1C0) >> 6
		lnkstr = GoolFormatLnk(lnk)
		reg = (ref & 0x3F)
		str = string.format("%s[0x%x]", lnkstr, 0x60+(reg*4))
	end
	return str
end

function GoolFormatLnk(lnk)
  disRNameLnk = {
    "self"    , "parent"  , "sibling" , "child"   ,
    "creator" , "player"  , "collider", "sender"  
  }
  str = disRNameLnk[lnk+1]
  return str
end

function GoolFormatVec(vec)
  disRNameVec = {
    "trans"   , "rot"      , "scale"       , 
    "velocity", "targetrot", "rotvelocity" 
  }
  str = disRNameVec[vec+1]
  return str
end

function GoolFormatCol(col)
  disRNameCol = {
    "lightmatrix.v1x", "lightmatrix.v1y", "lightmatrix.v1z", 
    "lightmatrix.v2x", "lightmatrix.v2y", "lightmatrix.v2z", 
    "lightmatrix.v3x", "lightmatrix.v3y", "lightmatrix.v3z", 
    "color.r"        , "color.g"        , "color.b"        ,
    "colormatrix.v1x", "colormatrix.v1y", "colormatrix.v1z", 
    "colormatrix.v2x", "colormatrix.v2y", "colormatrix.v2z", 
    "colormatrix.v3x", "colormatrix.v3y", "colormatrix.v3z",
    "intensity.r"    , "intensity.g"    , "intensity.b"    
  }
  str = disRNameCol[col+1]
  return str
end

function map(tbl, f)
    local t = {}
    for k,v in pairs(tbl) do
        t[k] = f(v)
    end
    return t
end

function reduce(tbl, f, init)
	local res = init or {}
	for k,v in pairs(tbl) do
		prev = res
		res = f(res, v)
		if res == nil then res = prev end
	end
	return res
end
		
local instr_map = reduce(instructions, function (this, ins) 
	this[ins.name] = ins 
	return this
end)

function get_operand(ins, op)
	--printf("shamt: %i, mask: %i ", op.shamt, op.mask)
	return ((ins >> op.shamt) & op.mask)
end	


function MakeDisF(name, ins_table)
	local instr = ins_table[name]
	local mapfn = function(op)
		local str = ""
		local value = get_operand(ins, op.op)
		if op.name == 'gRefI' then
			str = GoolFormatRef(value,0)
		elseif op.name == 'gRefO' then
			str = GoolFormatRef(value,1)
		elseif op.name == 'gRefX' then
			str = GoolFormatRef(value,2)
		elseif op.name == 'gIm' then
			str = string.format("0x%x",value)
		elseif op.name == 'gReg' then
			str = string.format("self[0x%x]",0x60+(value*4))
		elseif op.name == 'gLnk' then
			str = GoolFormatLnk(value)
		elseif op.name == 'gVec' then
			str = GoolFormatVec(value)
		elseif op.name == 'gCol' then
			str = GoolFormatCol(value)
		elseif op.name == 'gCofs' then
			str = string.format("code[0x%4.4X]",value)
		end
		return str
	end
	local func = function(ins, pc)
		local ops = table.concat(map(instr.operands,  mapfn), ", ")
		local str = string.format("%5s   %s", name, ops)  
		local line = string.format("0x%-4.4X %8.8X: %s", pc, ins, str)
		return line
	end
	return func
end

local disF = reduce(instructions, function (this, ins) 
	this[ins.name] = MakeDisF(ins.name, instr_map)
	return this 
end)

local _Op_ = { shamt = 24, mask = 0xFF }

functions = {
  { name = "CFL", operands = { _Os_, _Cond_ }, ins_map = disGOOL_CFL },
  { name = "RSTT", operands = { _Os_, _Cond_ }, ins_map = disGOOL_RSTT },
  { name = "RSTF", operands = { _Os_, _Cond_ }, ins_map = disGOOL_RSTF },
  { name = "VECA", operands = { VEC_Pso } , ins_map = disGOOL_VECA },
  { name = "VECB", operands = { VEC_Pso }, ins_map = disGOOL_VECB },
  { name = "SBW", operands = { MSC_Sso }, ins_map = disGOOL_MSC_SBW },
  { name = "SBR", operands = { MSC_Sso }, ins_map = disGOOL_MSC_SBR },
  { name = "MSCB", operands = { MSC_Sso }, ins_map = disGOOL_MSC_MSCB },
  { name = "MSC", operands = { MSC_Pso }, ins_map = disGOOL_MSC }
}

local func_map = reduce(functions, function (this, func) 
	this[func.name] = func 
	return this
end)

function MakeDisFg(name, func_table)
	local fn = func_table[name]
	local ins_map = fn.ins_map
	local func = function(ins, pc)
		local cur_map = ins_map
		for i,op in ipairs(fn.operands) do
			idx = get_operand(ins, op)+1
			cur_map = cur_map[idx]
		end
		name = cur_map
		if disF[name] == nil then
			return "INSTR NOT FOUND"
		end
		return disF[name](ins, pc)
	end
	return func
end

local disFg = reduce(functions, function (this, func) 
	this[func.name] = MakeDisFg(func.name, func_map)
	return this
end)

function GoolDisassemble(ins, pc)
	local opcode = get_operand(ins, _Op_)
	local name = disGOOL[opcode+1]
	if disFg[name] ~= nil then
		return disFg[name](ins, pc)
	elseif disF[name] ~= nil then
		return disF[name](ins, pc)
	end
	return "INVALID INSTR"
end
