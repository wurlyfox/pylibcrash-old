function lw(value)
	return value & 0xFFFF
end
function hw(value)
	return (value & 0xFFFF0000) >> 16
end
function slw(value)
	return i16(value & 0xFFFF)
end
function shw(value)
	return i16((value & 0xFFFF0000) >> 16)
end
function lb(value)
	return value & 0xFF
end
function hb(value)
	return (value & 0xFF00) >> 8
end
function hb2(value)
	return (value & 0xFF0000) >> 16
end
function hb3(value)
	return (value & 0xFF000000) >> 24
end
function slb(value)
	return i8(value & 0xFF)
end
function shb(value)
	return i8((value & 0xFF00) >> 8)
end
function shb2(value)
	return i8((value & 0xFF0000) >> 16)
end
function shb3(value)
	return i8((value & 0xFF000000) >> 24)
end

 
function gte_reg(name)
	-- \#define (.*?)\s*\(psxRegs\.CP2D\.p\[ (.*?) \]\.d\)
	-- elseif name == '\1' then\n\treturn cp2d_r\2
	
	-- \#define (.*?)\s*\(psxRegs\.CP2D\.p\[ (.*?) \]\.sd\)
	-- elseif name == '\1' then\n\treturn i32(cp2d_r\2)
	
	-- \#define (.*?)\s*\(psxRegs\.CP2D\.p\[ (.*?) \]\.w.h\)
	-- elseif name == '\1' then\n\treturn hw(cp2d_r\2)
	
	-- \#define (.*?)\s*\(psxRegs\.CP2D\.p\[ (.*?) \]\.w.l\)
	-- elseif name == '\1' then\n\treturn lw(cp2d_r\2)
	
	-- \#define (.*?)\s*\(psxRegs\.CP2D\.p\[ (.*?) \]\.sw.h\)
	-- elseif name == '\1' then\n\treturn shw(cp2d_r\2)
	
	-- \#define (.*?)\s*\(psxRegs\.CP2D\.p\[ (.*?) \]\.sw.l\)
	-- elseif name == '\1' then\n\treturn slw(cp2d_r\2)
	
	-- \#define (.*?)\s*\(psxRegs\.CP2D\.p\[ (.*?) \]\.b.l\)
	-- elseif name == '\1' then\n\treturn lb(cp2d_r\2)
	
	-- \#define (.*?)\s*\(psxRegs\.CP2D\.p\[ (.*?) \]\.b.h\)
	-- elseif name == '\1' then\n\treturn hb(cp2d_r\2)
	
	-- \#define (.*?)\s*\(psxRegs\.CP2D\.p\[ (.*?) \]\.b.h2\)
	-- elseif name == '\1' then\n\treturn hb2(cp2d_r\2)
	
	-- \#define (.*?)\s*\(psxRegs\.CP2D\.p\[ (.*?) \]\.b.h3\)
	-- elseif name == '\1' then\n\treturn hb3(cp2d_r\2)
	

	-- \#define (.*?)\s*\(psxRegs\.CP2C\.p\[ (.*?) \]\.d\)
	-- elseif name == '\1' then\n\treturn cp2c_r\2
	
	-- \#define (.*?)\s*\(psxRegs\.CP2C\.p\[ (.*?) \]\.sd\)
	--elseif name == '\1' then\n\treturn i32(cp2c_r\2)
	
	-- \#define (.*?)\s*\(psxRegs\.CP2C\.p\[ (.*?) \]\.w.h\)
	-- elseif name == '\1' then\n\treturn hw(cp2c_r\2)
	
	-- \#define (.*?)\s*\(psxRegs\.CP2C\.p\[ (.*?) \]\.w.l\)
	-- elseif name == '\1' then\n\treturn lw(cp2c_r\2)
	
	-- \#define (.*?)\s*\(psxRegs\.CP2C\.p\[ (.*?) \]\.sw.h\)
	-- elseif name == '\1' then\n\treturn shw(cp2c_r\2)
	
	-- \#define (.*?)\s*\(psxRegs\.CP2C\.p\[ (.*?) \]\.sw.l\)
	-- elseif name == '\1' then\n\treturn slw(cp2c_r\2)
	
	-- \#define (.*?)\s*\(psxRegs\.CP2C\.p\[ (.*?) \]\.b.l\)
	-- elseif name == '\1' then\n\treturn lb(cp2c_r\2)
	
	-- \#define (.*?)\s*\(psxRegs\.CP2C\.p\[ (.*?) \]\.b.h\)
	-- elseif name == '\1' then\n\treturn hb(cp2c_r\2)
	
	-- \#define (.*?)\s*\(psxRegs\.CP2C\.p\[ (.*?) \]\.b.h2\)
	-- elseif name == '\1' then\n\treturn hb2(cp2c_r\2)
	
	-- \#define (.*?)\s*\(psxRegs\.CP2C\.p\[ (.*?) \]\.b.h3\)
	-- elseif name == '\1' then\n\treturn hb3(cp2c_r\2)
	if name == 'VX0' then
		return slw(cp2d_r0)
	elseif name == 'VY0' then
		return shw(cp2d_r0)
	elseif name == 'VZ0' then
		return slw(cp2d_r1)
	elseif name == 'VX1' then
		return lw(cp2d_r2)
	elseif name == 'VY1' then
		return hw(cp2d_r2)
	elseif name == 'VZ1' then
		return lw(cp2d_r3)
	elseif name == 'VX2' then
		return lw(cp2d_r4)
	elseif name == 'VY2' then
		return hw(cp2d_r4)
	elseif name == 'VZ2' then
		return lw(cp2d_r5)
	elseif name == 'R' then
		return lb(cp2d_r6)
	elseif name == 'G' then
		return hb(cp2d_r6)
	elseif name == 'B' then
		return hb2(cp2d_r6)
	elseif name == 'CODE' then
		return hb3(cp2d_r6)
	elseif name == 'OTZ' then
		return lw(cp2d_r7)
	elseif name == 'IR0' then
		return slw(cp2d_r8)
	elseif name == 'IR1' then
		return slw(cp2d_r9)
	elseif name == 'IR2' then
		return slw(cp2d_r10)
	elseif name == 'IR3' then
		return slw(cp2d_r11)
	elseif name == 'SXY0' then
		return cp2d_r12
	elseif name == 'SX0' then
		return slw(cp2d_r12)
	elseif name == 'SY0' then
		return shw(cp2d_r12)
	elseif name == 'SXY1' then
		return cp2d_r13
	elseif name == 'SX1' then
		return slw(cp2d_r13)
	elseif name == 'SY1' then
		return shw(cp2d_r13)
	elseif name == 'SXY2' then
		return cp2d_r14
	elseif name == 'SX2' then
		return slw(cp2d_r14)
	elseif name == 'SY2' then
		return shw(cp2d_r14)
	elseif name == 'SXYP' then
		return cp2d_r15
	elseif name == 'SXP' then
		return slw(cp2d_r15)
	elseif name == 'SYP' then
		return shw(cp2d_r15)
	elseif name == 'SZ0' then
		return lw(cp2d_r16)
	elseif name == 'SZ1' then
		return lw(cp2d_r17)
	elseif name == 'SZ2' then
		return lw(cp2d_r18)
	elseif name == 'SZ3' then
		return lw(cp2d_r19)
	elseif name == 'RGB0' then
		return cp2d_r20
	elseif name == 'R0' then
		return lb(cp2d_r20)
	elseif name == 'G0' then
		return hb(cp2d_r20)
	elseif name == 'B0' then
		return hb2(cp2d_r20)
	elseif name == 'CD0' then
		return hb3(cp2d_r20)
	elseif name == 'RGB1' then
		return cp2d_r21
	elseif name == 'R1' then
		return lb(cp2d_r21)
	elseif name == 'G1' then
		return hb(cp2d_r21)
	elseif name == 'B1' then
		return hb2(cp2d_r21)
	elseif name == 'CD1' then
		return hb3(cp2d_r21)
	elseif name == 'RGB2' then
		return cp2d_r22
	elseif name == 'R2' then
		return lb(cp2d_r22)
	elseif name == 'G2' then
		return hb(cp2d_r22)
	elseif name == 'B2' then
		return hb2(cp2d_r22)
	elseif name == 'CD2' then
		return hb3(cp2d_r22)
	elseif name == 'RES1' then
		return cp2d_r23
	elseif name == 'MAC0' then
		return i32(cp2d_r24)
	elseif name == 'MAC1' then
		return i32(cp2d_r25)
	elseif name == 'MAC2' then
		return i32(cp2d_r26)
	elseif name == 'MAC3' then
		return i32(cp2d_r27)
	elseif name == 'IRGB' then
		return cp2d_r28
	elseif name == 'ORGB' then
		return cp2d_r29
	elseif name == 'LZCS' then
		return cp2d_r30
	elseif name == 'LZCR' then
		return cp2d_r31
	elseif name == 'R11' then
		return slw(cp2c_r0)
	elseif name == 'R12' then
		return shw(cp2c_r0)
	elseif name == 'R13' then
		return slw(cp2c_r1)
	elseif name == 'R21' then
		return shw(cp2c_r1)
	elseif name == 'R22' then
		return slw(cp2c_r2)
	elseif name == 'R23' then
		return shw(cp2c_r2)
	elseif name == 'R31' then
		return slw(cp2c_r3)
	elseif name == 'R32' then
		return shw(cp2c_r3)
	elseif name == 'R33' then
		return slw(cp2c_r4)
	elseif name == 'TRX' then
		return i32(cp2c_r5)
	elseif name == 'TRY' then
		return i32(cp2c_r6)
	elseif name == 'TRZ' then
		return i32(cp2c_r7)
	elseif name == 'L11' then
		return slw(cp2c_r8)
	elseif name == 'L12' then
		return shw(cp2c_r8)
	elseif name == 'L13' then
		return slw(cp2c_r9)
	elseif name == 'L21' then
		return shw(cp2c_r9)
	elseif name == 'L22' then
		return slw(cp2c_r10)
	elseif name == 'L23' then
		return shw(cp2c_r10)
	elseif name == 'L31' then
		return slw(cp2c_r11)
	elseif name == 'L32' then
		return shw(cp2c_r11)
	elseif name == 'L33' then
		return slw(cp2c_r12)
	elseif name == 'RBK' then
		return i32(cp2c_r13)
	elseif name == 'GBK' then
		return i32(cp2c_r14)
	elseif name == 'BBK' then
		return i32(cp2c_r15)
	elseif name == 'LR1' then
		return slw(cp2c_r16)
	elseif name == 'LR2' then
		return shw(cp2c_r16)
	elseif name == 'LR3' then
		return slw(cp2c_r17)
	elseif name == 'LG1' then
		return shw(cp2c_r17)
	elseif name == 'LG2' then
		return slw(cp2c_r18)
	elseif name == 'LG3' then
		return shw(cp2c_r18)
	elseif name == 'LB1' then
		return slw(cp2c_r19)
	elseif name == 'LB2' then
		return shw(cp2c_r19)
	elseif name == 'LB3' then
		return slw(cp2c_r20)
	elseif name == 'RFC' then
		return i32(cp2c_r21)
	elseif name == 'GFC' then
		return i32(cp2c_r22)
	elseif name == 'BFC' then
		return i32(cp2c_r23)
	elseif name == 'OFX' then
		return i32(cp2c_r24)
	elseif name == 'OFY' then
		return i32(cp2c_r25)
	elseif name == 'H' then
		return slw(cp2c_r26)
	elseif name == 'DQA' then
		return slw(cp2c_r27)
	elseif name == 'DQB' then
		return i32(cp2c_r28)
	elseif name == 'ZSF3' then
		return slw(cp2c_r29)
	elseif name == 'ZSF4' then
		return slw(cp2c_r30)
	elseif name == 'FLAG' then
		return cp2c_r31
	end
end

