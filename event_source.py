listen_address = '0.0.0.0'
listen_port = 9999
# ssh -R 0.0.0.0:9999:127.0.0.1:9999 publichost

import sys
import sdl2
import sdl2.ext
import select
import socket
import time
from ctypes import c_int, byref

def check_key():
    states = (c_int * sdl2.scancode.SDL_NUM_SCANCODES)()
    numkeys = c_int(0)
    keystates = sdl2.SDL_GetKeyboardState(byref(numkeys))
    assert numkeys.value > 0
    # for key in keystates[:numkeys.value]:
    keys_down = []
    for keystate in range(numkeys.value):
        if keystates[keystate] == 1:
            # print(f"Down: {keystate}")
            if keystate not in keys_down:
                keys_down.append(keystate)
    return keys_down


# Define some global color constants
WHITE = sdl2.ext.Color(255, 255, 255)
GREY = sdl2.ext.Color(200, 200, 200)
RED = sdl2.ext.Color(255, 0, 0)
GREEN = sdl2.ext.Color(0, 255, 0)

# Create a resource, so we have easy access to the example images.
#RESOURCES = sdl2.ext.Resources(__file__, "resources")

MACROS={"magic_sysrq_reboot":  [[226,70],[226,70,21],[226,70],[226,70,8],[226,70],[226,70,12],[226,70],[226,70,22],[226,70],[226,70,24],[226,70],[226,70,5],[]],
        "term1": [[226,224],[226,224,58],[]],
        "term2": [[226,224],[226,224,59],[]],
        "term3": [[226,224],[226,224,60],[]],
        "term7": [[226,224],[226,224,64],[]],
        "next_window": [[226,41],[]],
        "open_terminal": [[224,226,23],[]],
       }

# A callback for the Button.click event.
def onclick(macro_queue, macro_type):
    def onclick_inline(button, event):
        macro_queue.extend(MACROS[macro_type])
        print(f"Keys for {macro_type} were enqueued.")
    return onclick_inline


def oncheck(button, event):
    if button.checked:
        color = GREEN
    else:
        color = RED
    if button.factory.sprite_type == sdl2.ext.SOFTWARE:
        sdl2.ext.fill(button.surface, color)
    else:
        # SDL textures do not support color manipulation operation as easy
        # as software surface (since the texture is ideally stored somwhere
        # on the GPU memory in a GPU-specific layout [or not]). To circumvent
        # this, we create a temporary sprite (texture) and exchange the button
        # texture with it.
        tmpsprite = button.factory.from_color(color, button.size)
        button.texture, tmpsprite.texture = tmpsprite.texture, button.texture
        del tmpsprite


def run():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_address = (listen_address, listen_port)
    print('listening on %s port %s' % server_address)
    sock.bind(server_address)
    sock.listen()
    read_list = [sock]

    keys_macro = []

    # You know those from the helloworld.py example.
    # Initialize the video subsystem, create a window and make it visible.
    sdl2.ext.init()
    window = sdl2.ext.Window("UI Elements", size=(800, 600))
    window.show()

    # Create a sprite factory that allows us to create visible 2D elements
    # easily. Depending on what the user chosses, we either create a factory
    # that supports hardware-accelerated sprites or software-based ones.
    # The hardware-accelerated SpriteFactory requres a rendering context
    # (or SDL_Renderer), which will create the underlying textures for us.
    if "-hardware" in sys.argv:
        print("Using hardware acceleration")
        renderer = sdl2.ext.Renderer(window, flags=sdl2.render.SDL_RENDERER_ACCELERATED)
        factory = sdl2.ext.SpriteFactory(sdl2.ext.TEXTURE, renderer=renderer)
    else:
        print("Using software rendering")
        renderer = sdl2.ext.Renderer(window, flags=sdl2.render.SDL_RENDERER_SOFTWARE)
        factory = sdl2.ext.SpriteFactory(sdl2.ext.SOFTWARE)

    # Create a UI factory, which will handle several defaults for
    # us. Also, the UIFactory can utilises software-based UI elements as
    # well as hardware-accelerated ones; this allows us to keep the UI
    # creation code clean.
    uifactory = sdl2.ext.UIFactory(factory)

    y = 50
    buttons = []
    color = RED
    for macro in MACROS.keys():
        button = uifactory.from_color(sdl2.ext.BUTTON, color, size=(50,50))
        button.position = 50, y
        button.click += onclick(keys_macro, macro)
        buttons.append(button)
        y += 80
        color = GREEN

    # Since all gui elements are sprites, we can use the
    # SpriteRenderSystem class, we learned about in helloworld.py, to
    # draw them on the Window.
    spriterenderer = factory.create_sprite_render_system(window)

    # Create a new UIProcessor, which will handle the user input events
    # and pass them on to the relevant user interface elements.
    uiprocessor = sdl2.ext.UIProcessor()

    running = True
    while running:
        events = sdl2.ext.get_events()
        for event in events:
            if event.type == sdl2.SDL_QUIT:
                running = False
                break
            # Pass the SDL2 events to the UIProcessor, which takes care of
            # the user interface logic.
            uiprocessor.dispatch(buttons, event)
        renderer.clear(0)
        # Render all user interface elements on the window.
        spriterenderer.render(buttons)

        if len(keys_macro) > 0:
            keys_down = keys_macro.pop(0)
        else:
            keys_down = check_key()

        sock_readable, sock_writable, sock_errored = select.select(read_list, read_list, [], 0)
        for s in sock_readable:
            if s is sock:
                client_socket, address = s.accept()
                read_list.append(client_socket)
                print("Connection from", address)
            else:
                try:
                    data = s.recv(1024)
                except:
                    data = None
                if data:
                    print(data)
                else:
                    s.close()
                    read_list.remove(s)
        for s in sock_writable:
            try:
                s.send(bytearray(keys_down + [0]))
            except:
                print("Error writing to socket, closing")
                if s in read_list:
                    read_list.remove(s)

        if len(keys_down) > 0:
            print(", ".join([str(i) for i in keys_down]))
        time.sleep(0.05 if len(keys_macro) == 0 else 0.5)

    sdl2.ext.quit()
    return 0


if __name__ == "__main__":
    sys.exit(run())
