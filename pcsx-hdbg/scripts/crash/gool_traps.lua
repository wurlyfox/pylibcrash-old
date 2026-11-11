require "scripts.crash.gool"
require "scripts.crash.disgool"

function cprintf(s, f, ...)
	return s .. string.format(f, ...)
end

function objprint(obj)
	out = ""
	
	if obj.external == nil then return end
	header = obj.external.items[1]
	base_sp = readu32(header+0xC)*4
	stack = (obj.addr + 0x60) + base_sp
	objfp = obj.fp - stack
	objsp = obj.sp - stack
	out = cprintf(out, "stack start: %x+60\n", base_sp)
	out = cprintf(out, "stack size: %x\n", objsp)
	out = cprintf(out, "stack frame: %x | %x\n", base_sp+objfp, base_sp+objsp)
	out = cprintf(out, "memory contents: \n")
	offs = 0
	if objsp < 0 then return end
	for i=1,objsp do
		offs = (i-1)%16
		if offs == 0 then
			out = cprintf(out, "%03x+60:", base_sp+(i-1))
		end
		if (i-1) == objfp then
			out = cprintf(out, "(%02x", readu8(stack+i-1))
		elseif (i-1) == objsp-1 then
			out = cprintf(out, " %02x)", readu8(stack+i-1))
		else
			out = cprintf(out, " %02x", readu8(stack+i-1))
		end
		if offs == 15 then
			out = cprintf(out, "\n")
		end
	end
	if not offs == 15 then
		out = cprintf(out, "\n")
	end
	--out = cprintf(out, "\n")
	printf("%s", out)
end

local dislen = 8
function objprintdebug(obj)
	if obj.external == nil then return end
	objprint(obj)
	code = obj.external.items[2]
	pcins = obj.pc - code
	if pcins < 0 then return end
	pcs = math.max(pcins - ((dislen/2)*4), 0)
	pcn = pcs + (dislen*4)
	-- printf("current code window:")
	for pc=pcs,pcn-1,4 do
		ins = readu32(code+pc)
		line = GoolDisassemble(ins, pc)
		if pc == pcins then
			printf("*** %s", line)
		else
			printf("    %s", line)
		end
	end
	-- printf("")
end

trapexec(0x80020218, function()
	obj = readobj(s2)
	if obj.global.name ~= 'WillC' then
		return
	end
	objprintdebug(obj)
end)

trapexec(0x8001D728, function()
	obj = readobj(s0)
	if obj.global.name ~= 'WillC' then
		return
	end
	printf("changing to state %i\n", obj.state)
end)
