//
// PCSX-HDBG - PCSX-based hack debugger
// Copyright (C) 2019-2021  "chekwob" <chek@wobbyworks.com>
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <http://www.gnu.org/licenses/>.
//

#include <hdbg_cpu.h>
#include <hdbg_trap.h>

#include "lua.h"
#include "lauxlib.h"

#include "../core/r3000a.h"

extern void (*psxBSC[64])();
extern int branch;

static inline void execI() { 
    if (CONSIDER_TRAP(psxRegs.pc)) {
        trap_raise(psxRegs.pc);
    }

	u32 *code = Read_ICache(psxRegs.pc, FALSE);
	psxRegs.code = ((code == NULL) ? 0 : SWAP32(*code));

	// debugI();

	psxRegs.pc += 4;
	psxRegs.cycle += BIAS;

	psxBSC[psxRegs.code >> 26]();
}

static int scr_getreg(lua_State *L)
{
    int reg = luaL_checkinteger(L, 1) - 1;
    if (reg < 0 || reg >= 34 + 32 + 32 + 32 + 1) {
        return luaL_error(L, "register index out of bounds");
    }
    lua_pushinteger(L, (uint32_t)psxRegs.GPR.r[reg]);
    return 1;
}

static int scr_setreg(lua_State *L)
{
    int reg = luaL_checkinteger(L, 1) - 1;
    uint32_t value = luaL_checkinteger(L, 2);
    if (reg < 0 || reg >= 34 + 32 + 32 + 32 + 1) {
        return luaL_error(L, "register index out of bounds");
    }
    if (reg == 0) {
        return luaL_error(L, "attempted to set register r0");
    }
    psxRegs.GPR.r[reg] = value;
    return 0;
}

static int scr_jal(lua_State *L)
{
	int i, argc;
	uint32_t pc, sp, v0, reg[4], link;
	uint32_t addr, arg[4];
	uint32_t res;
    
    addr = luaL_checkinteger(L, 1);    
    for (argc=0;argc<4;argc++) {
        if (lua_isnoneornil(L, argc+2)) break;
        arg[argc] = luaL_checkinteger(L, argc+2);
    }
    
    pc = psxRegs.pc;
    sp = psxRegs.GPR.n.sp;
    link = psxRegs.GPR.r[31]; /* save current ret addr */
    v0 = psxRegs.GPR.n.v0;  
    for (i=0;i<argc;i++) {
        reg[i] = psxRegs.GPR.r[4+i];
        psxRegs.GPR.r[4+i] = arg[i];
    }
    
    psxRegs.GPR.r[31] = pc;
    branch = 0; /* branch and link; no delay slot */
    psxRegs.pc = addr;
    psxBranchTest();
    
    for (;;) {
        if (psxRegs.pc == pc && psxRegs.GPR.n.sp == sp) break; 
        execI();
    }
    
    /* restore regs */
    res = psxRegs.GPR.n.v0;
    psxRegs.GPR.n.v0 = v0;
    psxRegs.GPR.r[31] = link;
    for (i=0;i<argc;i++) {
        psxRegs.GPR.r[4+i] = reg[i];
    }
    
    lua_pushinteger(L, res);
    return 1;
}

extern lua_State *L;

#define DEFINE_LUA_FUNCTION(name) \
    lua_pushcfunction(L, scr_##name); \
    lua_setglobal(L, #name);

void cpu_init(void)
{
    DEFINE_LUA_FUNCTION(getreg);
    DEFINE_LUA_FUNCTION(setreg);
    DEFINE_LUA_FUNCTION(jal);
}

void cpu_quit(void)
{
}
