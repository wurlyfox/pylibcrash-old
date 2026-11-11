trapexec(game.level_update, function()
	--printf("level_update")
	local entry_p = a0
	local eid = readu32(entry_p+4)
	local eid_name = eidtoname(eid)
	--printf("a0: %8X", a0)
	--printf("trying to set zone to: %s", eid_name)
end)
