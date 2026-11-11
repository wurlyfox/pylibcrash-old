buttons = 0xFFFFFFFF
directions = 0xFFFF

function getbuttons()
	buttons = padgetbuttons()
	directions = buttons & 0xF0
	
	-- when holding (L1?), steal directional input for menus
	if (buttons & 1024) == 0 or (buttons & 2048) == 0 then
		buttons = buttons | 0xF0
		padsetbuttons(buttons)
	else
		directions = 0xF0
	end
end

