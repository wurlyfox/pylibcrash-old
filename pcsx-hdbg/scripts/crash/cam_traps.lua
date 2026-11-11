require('scripts.crash.cam')


--trapexec(0x8002BA80, function()
--	dir = cam_get_dir()
--	rot = cam_get_dir_rot(dir)

--	write32(0x80057870, rot.x)
--	write32(0x80057874, rot.y)
--	write32(0x80057878, rot.z)
--end)

function camstr(cam)
    res =
    string.format("cur_path: %08x\n", readu32(cam+0)) ..
    string.format("next_path: %08x\n", readu32(cam+4)) ..
    string.format("progress: %i\n", reads32(cam+8)) ..
    string.format("exit: %i\n", reads32(cam+12)) ..
    string.format("entrance: %i\n", reads32(cam+16)) ..
    string.format("delta_progress: %i\n", reads32(cam+20)) ..
    string.format("dist: %i\n", readu32(cam+24)) ..
    string.format("flags: %08x\n", readu32(cam+28)) ..
    string.format("relation: %08x\n", readu32(cam+32)) ..
    string.format("pan_x: %i\n", reads32(cam+36)) ..
    string.format("zoom: %i\n", reads32(cam+40)) ..
    string.format("pan_y: %i\n", reads32(cam+44)) ..
    string.format("progress_made: %i\n", reads32(cam+48))
    return res
end

trapexec(0x8002B218, function()
    print(string.format("%i", v0))
end)

trapexec(0x8002B280, function()
    print(string.format("%i", a0))
end)


trapexec(0x8002B13C, function()
    icam = s4
    cam = sp+0x18
    for i=1,icam do
        str = camstr(cam)
        cam = cam + 0x34
        print(string.format("cam %i", i))
        print(str)
    end
end)

trapexec(0x8002A7F4, function()
    crash = 0x800566B4
    obj = readu32(crash)
    trans_x = readu32(obj+0x80)
    trans_y = readu32(obj+0x84)
    trans_z = readu32(obj+0x88)
    print(string.format("crash trans x: %i", trans_x))
    print(string.format("crash trans y: %i", trans_y))
    print(string.format("crash trans z: %i", trans_z))
    print(string.format("v_dist.x: %i", reads32(sp+0x20)))
    print(string.format("v_dist.y: %i", reads32(sp+0x24)))
    print(string.format("v_dist.z: %i", reads32(sp+0x28)))
end)
