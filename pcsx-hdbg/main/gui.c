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

#include <hdbg_gui.h>

#include <stdio.h>
#include <stdlib.h>

#include <hdbg_pad.h>

#include <SDL.h>
#include <GL/gl.h>
#include "lua.h"
#include "lauxlib.h"

#define NK_IMPLEMENTATION
#define NK_INCLUDE_DEFAULT_ALLOCATOR
#define NK_INCLUDE_DEFAULT_FONT
#define NK_INCLUDE_FONT_BAKING
#define NK_INCLUDE_VERTEX_BUFFER_OUTPUT
#define NK_SIZE_TYPE size_t
#define NK_POINTER_TYPE uintptr_t
#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wunused-function"
#pragma GCC diagnostic ignored "-Wunused-but-set-variable"
#include "nuklear.h"
#pragma GCC diagnostic pop

float gui_scale;
SDL_Window *gui_window;
SDL_GLContext gui_glctx;
SDL_GLContext gui_gpuglctx;
struct nk_context gui_nkctx;

static bool inputstarted = false;

#define GUI_FONT_SIZE (gui_scale * 16.0f)

struct tool {
    char name[20];
    int func;
    struct tool *next;
};

static int slots = -1;

static int level = -1;
static int nodestack[32] = { 0 };

static int toolchain_len;
static struct tool *toolchain;
static struct tool *active_tool;

static int scr_guitool(lua_State *L)
{
    const char *name = luaL_checkstring(L, 1);
    luaL_checktype(L, 2, LUA_TFUNCTION);

    lua_pushvalue(L, 2);
    int func = luaL_ref(L, LUA_REGISTRYINDEX);

    struct tool *new_tool = malloc(sizeof(struct tool));
    if (!new_tool) {
        return luaL_error(L, "failed to allocate memory for tool");
    }

    strncpy(new_tool->name, name, sizeof(new_tool->name));
    new_tool->name[sizeof(new_tool->name) - 1] = '\0';
    new_tool->func = func;
    new_tool->next = NULL;

    struct tool **tailptr = &toolchain;
    while (*tailptr)
        tailptr = &(*tailptr)->next;

    *tailptr = new_tool;
    toolchain_len++;
    return 0;
}

typedef struct {
    int pressed;
    int released;
} scr_mouse;

static void scr_do_mouse_handler(lua_State *L, int idx) {
    int type = lua_type(L, idx);
    if (type == LUA_TFUNCTION) {
        int down = nk_widget_has_mouse_click_down(&gui_nkctx, NK_BUTTON_LEFT, 1);
        lua_pushvalue(L, idx);
        lua_pushinteger(L, down);
        // lua_pushstring(L, id)
        int err = lua_pcall(L, 1, 0, 0);
        if (err != LUA_OK) {
            const char *msg = lua_tostring(L, -1);
            if (msg) {
                fprintf(
                    stderr,
                    "Error executing handler: %s\n",
                    msg
                );
            } else {
                fprintf(
                    stderr,
                    "Error executing handler; no error message\n"
                );
            }
        }
    }
}

static int scr_gui_row(lua_State *L)
{
    int columns = luaL_checkinteger(L, 1);

    if (slots == -1) {
        return luaL_error(L, "gui function called outside gui code");
    }

    nk_layout_row_dynamic(&gui_nkctx, GUI_FONT_SIZE, columns);
    slots = columns;

    return 0;
}

static int scr_gui_label(lua_State *L)
{
    const char *str = luaL_checkstring(L, 1);
    int selected = luaL_optinteger(L, 2, -1);

    if (slots == -1) {
        return luaL_error(L, "gui function called outside gui code");
    } else if (slots == 0) {
        nk_layout_row_dynamic(&gui_nkctx, GUI_FONT_SIZE, 1);
        slots = 1;
    }

    scr_do_mouse_handler(L, 3);
    if (selected==-1)
        nk_label(&gui_nkctx, str, NK_TEXT_LEFT);
    else
        nk_select_label(&gui_nkctx, str, NK_TEXT_LEFT, selected);
    slots--;

    return 0;
}

static int scr_gui_text(lua_State *L)
{
    const char *str = luaL_checkstring(L, 1);
    int selected = luaL_optinteger(L, 2, -1);
    int len = strlen(str);

    if (slots == -1) {
        return luaL_error(L, "gui function called outside gui code");
    } else if (slots == 0) {
        nk_layout_row_dynamic(&gui_nkctx, GUI_FONT_SIZE, 1);
        slots = 1;
    }

    scr_do_mouse_handler(L, 3);
    if (selected==-1)
        nk_text(&gui_nkctx, str, len, NK_TEXT_LEFT);
    else
        nk_select_text(&gui_nkctx, str, len, NK_TEXT_LEFT, selected);
    slots--;

    return 0;
}

static int scr_gui_button(lua_State *L)
{
    const char *str = luaL_checkstring(L, 1);
    luaL_checktype(L, 2, LUA_TFUNCTION);
    char *id = luaL_optstring(L, 3, "");

    if (slots == -1) {
        return luaL_error(L, "gui function called outside gui code");
    } else if (slots == 0) {
        nk_layout_row_dynamic(&gui_nkctx, GUI_FONT_SIZE, 1);
        slots = 1;
    }

    if (nk_button_label(&gui_nkctx, str)) {
        lua_pushvalue(L, 2);
        lua_pushstring(L, id);
        int err = lua_pcall(L, 1, 0, 0);
        if (err != LUA_OK) {
            const char *msg = lua_tostring(L, -1);
            if (msg) {
                fprintf(
                    stderr,
                    "Error executing button handler for id %s: %s\n",
                    id,
                    msg
                );
            } else {
                fprintf(
                    stderr,
                    "Error executing button handler for id %s; no error message\n",
                    id
                );
            }
        }
    }
    slots--;

    return 0;
}

#define min(a,b) ((a)<(b)?(a):(b))
#define max(a,b) ((a)>(b)?(a):(b))

static int scr_gui_property(lua_State *L)
{
    const char *name = luaL_checkstring(L, 1);
    uint32_t addr = luaL_checkinteger(L, 2);
    uint32_t size = luaL_checkinteger(L, 3);
    int sign = lua_toboolean(L, 4);
    int mn = luaL_optinteger(L, 5, sign ? INT_MIN : 0);
    int mx = luaL_optinteger(L, 6, sign ? INT_MAX : UINT_MAX);

    void *data = psxMemPointer(addr);
    uint32_t value;
    int mmn, mmx;

    if (slots == -1) {
        return luaL_error(L, "gui function called outside gui code");
    } else  if (slots == 0) {
        nk_layout_row_dynamic(&gui_nkctx, GUI_FONT_SIZE, 1);
        slots = 1;
    }

    switch (size) {
    case 4:
        value = psxMemRead32(addr);
        mmn = INT_MIN; mmx = INT_MAX;
        if (!sign) { mmx = UINT_MAX; }
        break;
    case 2:
        value = psxMemRead16(addr);
        mmn = SHRT_MIN; mmx = SHRT_MAX;
        if (!sign) { mmx = USHRT_MAX; }
        break;
    case 1:
        value = psxMemRead8(addr);
        mmn = CHAR_MIN; mmx = CHAR_MAX;
        if (!sign) { mmx = UCHAR_MAX; }
        break;
    }
    if (!sign) { mmn = 0; }
    mn = min(max(mn, mmn), mmx);
    mx = min(max(mn, mx), mmx);
    nk_property_int(&gui_nkctx, name, mn, (int*)&value, mx, 1, 1.0);
    switch (size) {
    case 4:
        psxMemWrite32(addr, value);
        break;
    case 2:
        psxMemWrite16(addr, value);
        break;
    case 1:
        psxMemWrite8(addr, value);
        break;
    }
    slots--;

    return 0;
}

static int scr_gui_rgb(lua_State *L)
{
    int r = luaL_checkinteger(L, 1);
    int g = luaL_checkinteger(L, 2);
    int b = luaL_checkinteger(L, 3);

    nk_rgb(r, g, b);

    return 0;
}

static int scr_gui_tree_push(lua_State *L)
{
    const char *title = luaL_checkstring(L, 1);
    const char *hash = luaL_checkstring(L, 2);
    int selected = luaL_optinteger(L, 3, -1);
    int len = strlen(hash);

    int res;

    if (slots == -1) {
        return luaL_error(L, "gui function called outside gui code");
    } else  if (slots == 0) {
        nk_layout_row_dynamic(&gui_nkctx, GUI_FONT_SIZE, 1);
        slots = 1;
    }

    //scr_do_mouse_handler(L, 4);
    nodestack[++level] = (selected != -1);
    if (selected == -1)
        res = nk_tree_push_hashed(&gui_nkctx, NK_TREE_TAB, title, NK_MAXIMIZED, hash, len, 0);
    else
        res = nk_tree_element_push_hashed(&gui_nkctx, NK_TREE_TAB, title, NK_MAXIMIZED, &selected, hash, len, 0);
    slots--;

    if (!res) { level--; }

    lua_pushinteger(L, res);
    lua_pushinteger(L, selected);
    return 2;
}

static int scr_gui_tree_pop(lua_State *L)
{
    if (nodestack[level--] == 0)
        nk_tree_pop(&gui_nkctx);
    else
        nk_tree_element_pop(&gui_nkctx);
    return 0;
}

extern lua_State *L;

#define DEFINE_LUA_FUNCTION(name) \
    lua_pushcfunction(L, scr_##name); \
    lua_setglobal(L, #name);

#define DEFINE_LUA_LOCAL_FUNCTION(prefix, name) \
    lua_pushcfunction(L, scr_##prefix##_##name); \
    lua_setfield(L, -2, #name);

void gui_init(void)
{
    int ok;
    lua_getglobal(L, "config");

    lua_getfield(L, -1, "scale");
    gui_scale = lua_tonumberx(L, -1, &ok);
    if (!ok) {
        fprintf(
            stderr,
            "Error in config: Bad scale (not a number)\n"
        );
        exit(EXIT_FAILURE);
    }
    if (gui_scale < 0.1) {
        fprintf(
            stderr,
            "Error in config: Bad scale (less than minimum 0.1)\n"
        );
        exit(EXIT_FAILURE);
    }
    lua_pop(L, 1);

    lua_pop(L, 1);

    DEFINE_LUA_FUNCTION(guitool);
    lua_newtable(L);
    DEFINE_LUA_LOCAL_FUNCTION(gui, row);
    DEFINE_LUA_LOCAL_FUNCTION(gui, label);
    DEFINE_LUA_LOCAL_FUNCTION(gui, text);
    DEFINE_LUA_LOCAL_FUNCTION(gui, button);
    DEFINE_LUA_LOCAL_FUNCTION(gui, property);
    DEFINE_LUA_LOCAL_FUNCTION(gui, rgb);
    DEFINE_LUA_LOCAL_FUNCTION(gui, tree_push);
    DEFINE_LUA_LOCAL_FUNCTION(gui, tree_pop);
    lua_setglobal(L, "gui");

    SDL_GL_SetAttribute(SDL_GL_RED_SIZE, 8);
    SDL_GL_SetAttribute(SDL_GL_GREEN_SIZE, 8);
    SDL_GL_SetAttribute(SDL_GL_BLUE_SIZE, 8);
    SDL_GL_SetAttribute(SDL_GL_ALPHA_SIZE, 8);
    SDL_GL_SetAttribute(SDL_GL_DOUBLEBUFFER, 1);

    gui_window = SDL_CreateWindow(
        "PCSX-HDBG",
        SDL_WINDOWPOS_CENTERED,
        SDL_WINDOWPOS_CENTERED,
        GUI_WIDTH,
        GUI_HEIGHT,
        SDL_WINDOW_OPENGL
    );
    if (!gui_window) {
        fprintf(stderr, "SDL_CreateWindow failed: %s\n", SDL_GetError());
        exit(EXIT_FAILURE);
    }

    gui_glctx = SDL_GL_CreateContext(gui_window);
    if (!gui_glctx) {
        fprintf(stderr, "SDL_GL_CreateContext failed: %s\n", SDL_GetError());
        SDL_DestroyWindow(gui_window);
        exit(EXIT_FAILURE);
    }

    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);

    glMatrixMode(GL_PROJECTION);
    glOrtho(0.0f, GUI_WIDTH, GUI_HEIGHT, 0.0f, -1.0f, 1.0f);
    glMatrixMode(GL_MODELVIEW);

    static struct nk_font *font;
    static struct nk_font_atlas font_atlas;
    int font_width;
    int font_height;
    const void *font_pixels;
    nk_font_atlas_init_default(&font_atlas);
    nk_font_atlas_begin(&font_atlas);
    font = nk_font_atlas_add_default(&font_atlas, GUI_FONT_SIZE, NULL);
    font_pixels = nk_font_atlas_bake(
        &font_atlas,
        &font_width,
        &font_height,
        NK_FONT_ATLAS_RGBA32
    );
    glTexImage2D(
        GL_TEXTURE_2D,
        0,
        GL_RGBA,
        font_width,
        font_height,
        0,
        GL_RGBA,
        GL_UNSIGNED_BYTE,
        font_pixels
    );
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST);
    nk_font_atlas_end(&font_atlas, nk_handle_id(0xDEAD), 0);

    nk_init_default(&gui_nkctx, &font->handle);

    gui_gpuglctx = SDL_GL_CreateContext(gui_window);
    if (!gui_gpuglctx) {
        fprintf(stderr, "SDL_GL_CreateContext failed: %s\n", SDL_GetError());
        SDL_GL_DeleteContext(gui_glctx);
        SDL_DestroyWindow(gui_window);
        exit(EXIT_FAILURE);
    }
}

void gui_quit(void)
{
    SDL_GL_DeleteContext(gui_gpuglctx);
    SDL_GL_DeleteContext(gui_glctx);
    SDL_DestroyWindow(gui_window);
}

_Bool gui_isopen = 0;

void gui_setopen(_Bool open)
{
    if (gui_isopen == open)
        return;

    if (open) {
        pad_clearkeys();
    }

    gui_isopen = open;
}

void gui_update(void)
{
    if (!inputstarted) {
        nk_input_begin(&gui_nkctx);
        inputstarted = true;
    }

    SDL_Event ev;
    while (SDL_PollEvent(&ev)) {
        switch (ev.type) {

        case SDL_QUIT:
            exit(EXIT_SUCCESS);

        case SDL_KEYDOWN:
        case SDL_KEYUP:
            // Toggle GUI open status when pressing escape.
            if (ev.key.keysym.scancode == SDL_SCANCODE_ESCAPE) {
                if (ev.type == SDL_KEYDOWN) {
                    gui_setopen(!gui_isopen);
                }
                break;
            }

            /*if (gui_isopen) {
                // TODO
            } else {*/
                pad_handlekey(ev.key.keysym.scancode, ev.type == SDL_KEYDOWN);
            //}
            break;

        case SDL_CONTROLLERBUTTONDOWN:
        case SDL_CONTROLLERBUTTONUP:
            pad_handlejbutton(ev.cbutton.button, ev.type == SDL_CONTROLLERBUTTONDOWN);
            break;

        case SDL_CONTROLLERAXISMOTION:
            pad_handlejaxis(ev.caxis.axis, ev.caxis.value);
            break;

        case SDL_MOUSEBUTTONDOWN:
        case SDL_MOUSEBUTTONUP:
            if (gui_isopen) {
                int button =
                    (ev.button.button == SDL_BUTTON_LEFT)   ? NK_BUTTON_LEFT   :
                    (ev.button.button == SDL_BUTTON_RIGHT)  ? NK_BUTTON_RIGHT  :
                    (ev.button.button == SDL_BUTTON_MIDDLE) ? NK_BUTTON_MIDDLE :
                    -1;
                if (button != -1) {
                    nk_input_button(
                        &gui_nkctx,
                        button,
                        ev.button.x,
                        ev.button.y,
                        ev.type == SDL_MOUSEBUTTONDOWN
                    );
                }
            }
            break;

        case SDL_MOUSEMOTION:
            if (gui_isopen) {
                nk_input_motion(&gui_nkctx, ev.motion.x, ev.motion.y);
            }
            break;

        case SDL_MOUSEWHEEL:
            if (gui_isopen) {
                nk_input_scroll(&gui_nkctx, nk_vec2(ev.wheel.x, ev.wheel.y));
            }
            break;

        }
    }

    extern void update_lua(void);
    update_lua();
}

static void gui_draw(void)
{
    if (inputstarted) {
        nk_input_end(&gui_nkctx);
        inputstarted = false;
    }

    const float window_spacing = 80.0f * gui_scale;
    const struct nk_rect window_rect = {
        window_spacing,
        window_spacing,
        GUI_WIDTH - 2 * window_spacing,
        GUI_HEIGHT - 2 * window_spacing
    };
    if (nk_begin(&gui_nkctx, "PCSX-HDBG (" __DATE__ ")", window_rect, NK_WINDOW_TITLE)) {
        nk_layout_row_dynamic(&gui_nkctx, GUI_FONT_SIZE + 4.0f, toolchain_len);

        for (struct tool *tool = toolchain; tool; tool = tool->next) {
            if (tool == active_tool) {
                nk_label(&gui_nkctx, tool->name, NK_TEXT_CENTERED);
            } else {
                if (nk_button_label(&gui_nkctx, tool->name)) {
                    active_tool = tool;
                }
            }
        }

        nk_layout_row_dynamic(&gui_nkctx, 4, 0);

        if (active_tool) {
            lua_rawgeti(L, LUA_REGISTRYINDEX, active_tool->func);
            slots = 0;
            int err = lua_pcall(L, 0, 0, 0);
            slots = -1;
            if (err != LUA_OK) {
                const char *msg = lua_tostring(L, -1);
                if (msg) {
                    fprintf(
                        stderr,
                        "Error executing tool %p: %s\n",
                        (void *)active_tool,
                        msg
                    );
                } else {
                    fprintf(
                        stderr,
                        "Error executing tool %p; no error message\n",
                        (void *)active_tool
                    );
                }
            }
        } else {
            nk_layout_row_dynamic(&gui_nkctx, GUI_FONT_SIZE, 1);
            nk_label(&gui_nkctx, "No tool selected.", NK_TEXT_LEFT);
        }
    }
    nk_end(&gui_nkctx);

    glPushAttrib(GL_CURRENT_BIT | GL_SCISSOR_BIT);
    glEnable(GL_BLEND);
    glEnable(GL_SCISSOR_TEST);

    struct vtx {
        float pos[2];
        float uvs[2];
        unsigned char col[4];
    };

    struct nk_draw_vertex_layout_element layout[] = {
        { NK_VERTEX_POSITION, NK_FORMAT_FLOAT, offsetof(struct vtx, pos) },
        { NK_VERTEX_TEXCOORD, NK_FORMAT_FLOAT, offsetof(struct vtx, uvs) },
        { NK_VERTEX_COLOR, NK_FORMAT_R8G8B8A8, offsetof(struct vtx, col) },
        { NK_VERTEX_LAYOUT_END }
    };

    struct nk_convert_config cfg = {};
    cfg.vertex_layout = layout;
    cfg.vertex_size = sizeof(struct vtx);
    cfg.vertex_alignment = _Alignof(struct vtx);
    cfg.global_alpha = 0.8f;

    struct nk_buffer cmds;
    struct nk_buffer vbuf;
    struct nk_buffer ebuf;
    nk_buffer_init_default(&cmds);
    nk_buffer_init_default(&vbuf);
    nk_buffer_init_default(&ebuf);

    nk_convert(&gui_nkctx, &cmds, &vbuf, &ebuf, &cfg);

    const nk_byte *vertices = nk_buffer_memory_const(&vbuf);
    const nk_ushort *elements = nk_buffer_memory_const(&ebuf);

    glEnableClientState(GL_VERTEX_ARRAY);
    glEnableClientState(GL_TEXTURE_COORD_ARRAY);
    glEnableClientState(GL_COLOR_ARRAY);

    glVertexPointer(2, GL_FLOAT, sizeof(struct vtx), vertices + offsetof(struct vtx, pos));
    glTexCoordPointer(2, GL_FLOAT, sizeof(struct vtx), vertices + offsetof(struct vtx, uvs));
    glColorPointer(4, GL_UNSIGNED_BYTE, sizeof(struct vtx), vertices + offsetof(struct vtx, col));

    const struct nk_draw_command *cmd;
    nk_draw_foreach(cmd, &gui_nkctx, &cmds) {
        if (!cmd->elem_count)
            continue;

        // TODO - scissor

        if (cmd->texture.id == 0xDEAD)
            glEnable(GL_TEXTURE_2D);

        glDrawElements(GL_TRIANGLES, cmd->elem_count, GL_UNSIGNED_SHORT, elements);
        elements += cmd->elem_count;

        glDisable(GL_TEXTURE_2D);
    }

    glDisableClientState(GL_VERTEX_ARRAY);
    glDisableClientState(GL_TEXTURE_COORD_ARRAY);
    glDisableClientState(GL_COLOR_ARRAY);

    nk_buffer_free(&cmds);
    nk_buffer_free(&vbuf);
    nk_buffer_free(&ebuf);

    glDisable(GL_BLEND);
    glDisable(GL_SCISSOR_TEST);
    glPopAttrib();

    nk_clear(&gui_nkctx);
}

static void gui_drawbackdrop(void)
{
    glPushAttrib(GL_CURRENT_BIT);
    glEnable(GL_BLEND);

    glBegin(GL_QUADS);
    glColor4f(0.0f, 0.0f, 0.0f, 0.2f);
    glVertex2f(0.0f,      0.0f);
    glVertex2f(GUI_WIDTH, 0.0f);
    glColor4f(0.5f, 0.5f, 0.0f, 0.5f);
    glVertex2f(GUI_WIDTH, GUI_HEIGHT);
    glColor4f(0.0f, 0.5f, 0.5f, 0.5f);
    glVertex2f(0.0f,      GUI_HEIGHT);
    glEnd();

    glDisable(GL_BLEND);
    glPopAttrib();
}

void gui_finishframe(void)
{
    if (gui_isopen) {
        glFinish();
        SDL_GL_MakeCurrent(gui_window, gui_glctx);

        gui_drawbackdrop();
        gui_draw();

        glFinish();
        SDL_GL_MakeCurrent(gui_window, gui_gpuglctx);
    }

    SDL_GL_SwapWindow(gui_window);
}
