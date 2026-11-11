require('scripts.crash.ns')

trapexec(game.page_update_entries, function()
	local pageslot = a0
	local pstruct_p = a0 * 44 + game.page_structs
	local page_p = readu32(pstruct_p)
	local page_type = readu16(page_p + 2)
	local page_id = readu32(page_p + 4)
	if page_type == 1 then
		page_id = eidtoname(page_id)
	end
	printf("PAGE   LOAD @ slot %2d: page T%d; id %s", pageslot, page_type, page_id)
end)
trapexec(game.page_free, function()
	local pageslot = (a0 - game.page_structs) // 44
	local pstruct_p = a0
	local page_p = readu32(pstruct_p)
	local page_type = readu16(page_p + 2)
	local page_id = readu32(page_p + 4)
	if page_type == 1 then
		page_id = eidtoname(page_id)
	end
	printf("PAGE UNLOAD @ slot %2d: page T%d; id %s", pageslot, page_type, page_id)
end)
trapexec(game.page_translate, function()
	local pstruct_p = a0
	local page_p = readu32(pstruct_p)
	local page_type = readu16(page_p+2)
	local page_id = readu32(page_p+4)
	if not page_type == 0 then
		--page_id = eidtoname(page_id)
		--printf("translating page %s", page_id)
		return
	else
		printf("translating page %d", page_id)
	end
	
	--local entry_count = readu32(page_p+8)
	--printf("entry count: %d", entry_count)
	--for i=0,entry_count-1 do
	--	local entry_p = page_p + readu32(page_p+16+(i*4))
	--	local eid = readu32(entry_p+4)
	--	local eid_name = eidtoname(eid)
	--	local item_count = readu32(entry_p+12)
	--	printf("entry %d: %s", i+1, eid_name)
	--printf("item count: %d", item_count)
	--end
end) 
trapexec(game.entry_open, function()
	local pte_p = a0
	local eid = readu32(pte_p)
	if eid & 1 == 1 then
		local eid_name = eidtoname(eid)
		printf("ENTRY OPEN: entry %s", eid_name)
	end
end)
trapexec(0x80015164, function()
	local pair = v0
	printf("found entry PTE at %8X", pair)
end)
trapexec(0x80015424, function()
	local pstruct_p = v1
	printf("found/loaded page struct: %8X", pstruct_p)
end)
trapexec(game.entry_lookup, function()
	local eid_p = a0
	local eid = readu32(eid_p)
	if eid & 1 == 1 then
		local eid_name = eidtoname(eid)
		printf("ENTRY LOOKUP: entry %s", eid_name)
	end
end)
trapexec(0x80015B44, function() 
	local entry_p = v0
	local eid = readu32(v0+4)
	local eid_name = eidtoname(eid)
	printf("found entry with eid: %s", eid_name)
end)
trapexec(0x80025504, function()
	local result = v0
	printf("pointer to opened entry: %8X", result)
end)
trapexec(0x80012F68, function()
	local page_p = a0
	local pgid = readu32(page_p+4)
	local entry_count = readu32(page_p+8)
	printf("resolving entries for page %d. entry count: %d", pgid, entry_count)
end)
local tried = 0
trapexec(0x80012FC0, function()
	tried = 0
	local eid = v0
	local eidname = eidtoname(eid)
	local idx = (eid >> 15) & 0xFF
	local buckets = readu32(0x8005C530)
	printf("finding eid %s starting at bucket %d", eidname, idx)
end)
trapexec(0x80013000, function() 
	local pte_p = s1
	local eid = readu32(s1)
	local eidname = eidtoname(eid)
	local findeid = eidtoname(v1)
	tried = tried + 1
	if (tried < 10) 
	then
		printf("comparing pte at %08X, eid: %s with eid: %s", pte_p, eidname, findeid)
	end
end)
trapexec(0x8001300C, function()
	local pte_p = s1
	local eid = readu32(s1)
	local eidname = eidtoname(eid)
	local findeid = eidtoname(v1)
	tried = tried + 1
	if (tried < 10) 
	then
		printf("comparing pte at %08X, eid: %s with eid: %s", pte_p, eidname, findeid)
	end
end)
trapexec(0x80013020, function()
	local pte_p = s3
	local entry_p = a1
	local pte_eid = readu32(pte_p)
	local pte_eidname = eidtoname(pte_eid)
	local entry_eid = readu32(entry_p+4)
	local entry_eidname = eidtoname(entry_eid)
	printf("storing pointer to entry %8X in pte at %8X", entry_p, pte_p)
	printf("pte.eid = %s, entry.eid = %s", pte_eidname, entry_eidname)
end)
