local in_count = 0
local in_trans = {x = 0, y = 0, z = 0}
local in_rot   = {x = 0, y = 0}

local vert_idx    = 0
local frame_y     = 0
local obj_trans_y = 0
local r_vert_y    = 0

-- 0x8002BAB4: CamDeath entry
trapexec(0x8002BAB4, function()
    local count_ptr = a0
    in_count = reads32(count_ptr)

    in_trans = readvec(0x80057864) -- cam_trans {x, y, z}
    in_rot.y = reads32(0x80057870) -- cam_rot.y (Pitch)
    in_rot.x = reads32(0x80057874) -- cam_rot.x (Yaw)

    -- Extract Crash model/frame parameters
    local obj_ptr = readu32(0x8006191C)
    vert_idx    = readu32(0x80061950) >> 8
    obj_trans_y = reads32(obj_ptr + 0x84)

    local anim_frame   = readu32(obj_ptr + 0x10C) >> 8
    local anim_seq_ptr = readu32(obj_ptr + 0x108)
    local svtx_entry   = jal(0x80015A98, anim_seq_ptr + 4) -- NSLookup(&anim->eid)[cite: 3, 6]
    local frame_ptr    = readu32(svtx_entry + 16 + (anim_frame * 4))

    frame_y = reads32(frame_ptr + 12)
end)

-- 0x8002BB90: Immediately after the first GoolTransform computes r_vert
trapexec(0x8002BB90, function()
    r_vert_y = reads32(sp + 0x24) -- v37
end)

-- 0x8002BD48: CamDeath exit point (li $v0, -255 / jr $ra)
trapexec(0x8002BD48, function()
    local rot_y1  = reads32(gp + 468)
    local trans_z = reads32(gp + 476)

    local out_trans = readvec(0x80057864)
    local out_rot_y = reads32(0x80057870)
    local out_rot_x = reads32(0x80057874)

    printf("[CAM_DEATH] cnt=%d | in_trans=(%i,%i,%i) in_rot=(%i,%i) | rot_y1=%i trans_z=%i | out_trans=(%i,%i,%i) out_rot=(%i,%i) | debug=(vert:%i,frm_y:%i,r_vrt_y:%i,obj_y:%i)",
        in_count,
        in_trans.x, in_trans.y, in_trans.z,
        in_rot.x, in_rot.y,
        rot_y1, trans_z,
        out_trans.x, out_trans.y, out_trans.z,
        out_rot_x, out_rot_y,
        vert_idx, frame_y, r_vert_y, obj_trans_y
    )
end)

-- Hook at 0x8002BB90 (right after the first GoolTransform returns in CamDeath)
trapexec(0x8002BB90, function()
    local obj_ptr = readu32(0x8006191C)

    -- obj->scale offsets: 38*4 = 152 (0x98), 39*4 = 156 (0x9C), 40*4 = 160 (0xA0)
    local obj_scale_x = reads32(obj_ptr + 0x98)
    local obj_scale_y = reads32(obj_ptr + 0x9C)
    local obj_scale_z = reads32(obj_ptr + 0xA0)

    -- sp relative offsets for local vectors:
    -- v39 (u_vert): [sp+0x30], [sp+0x34], [sp+0x38]
    -- v40 (scale):  [sp+0x40], [sp+0x44], [sp+0x48]
    -- v36 (r_vert): [sp+0x20], [sp+0x24], [sp+0x28]
    local u_vert_x = reads32(sp + 0x30)
    local u_vert_y = reads32(sp + 0x34)
    local u_vert_z = reads32(sp + 0x38)

    local scale_x = reads32(sp + 0x40)
    local scale_y = reads32(sp + 0x44)
    local scale_z = reads32(sp + 0x48)

    local r_vert_x = reads32(sp + 0x20)
    local r_vert_y = reads32(sp + 0x24)
    local r_vert_z = reads32(sp + 0x28)

    printf("[CAM_DEATH_TRANS] obj_scale=(%i,%i,%i) eff_scale=(%i,%i,%i) | u_vert=(%i,%i,%i) | r_vert=(%i,%i,%i)",
        obj_scale_x, obj_scale_y, obj_scale_z,
        scale_x, scale_y, scale_z,
        u_vert_x, u_vert_y, u_vert_z,
        r_vert_x, r_vert_y, r_vert_z
    )
end)
