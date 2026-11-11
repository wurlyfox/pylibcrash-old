local c1_scus = require("scripts.crash.c1_scus")
game = c1_scus

if config.bootlevel then
	write8(game.bootlevel, config.bootlevel)
end

--require("scripts.crash.ns_traps")
--require("scripts.crash.gfx_traps")
--require("scripts.crash.game_traps")
--require("scripts.crash.cam_traps")
-- require("scripts.crash.gool_traps")
require("scripts.crash.cam_death_trace")

require("scripts.crash.gui")


