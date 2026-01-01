# 1. STATE & CONSTANTS
level = 1
launcher_angle = 90
is_moving = False
game_active = False
ceiling_drops = 0
current_bubble: Sprite = None

COLORS = [2, 4, 5, 7, 8, 9]
next_color = Math.pick_random(COLORS)
loaded_color = Math.pick_random(COLORS)

# Timers in milliseconds
shoot_timer = 0
ceiling_timer = 0
AUTO_SHOOT_LIMIT = 7000
CEILING_DROP_LIMIT = 20000

# 2. SPRITE DEFINITIONS
launcher = sprites.create(image.create(32, 32), SpriteKind.player)
launcher.set_position(80, 110)

loaded_bubble_sprite = sprites.create(image.create(16, 16), SpriteKind.player)
loaded_bubble_sprite.set_position(80, 110)

next_bubble_preview = sprites.create(image.create(16, 16), SpriteKind.player)
next_bubble_preview.set_position(20, 110)

# 3. HELPER FUNCTIONS
def get_pos_x(r: number, c: number):
    x_off = 8 if (r % 2 == 1) else 0
    return c * 16 + 24 + x_off

def get_pos_y(r: number, c: number):
    return r * 14 + 10

def draw_launcher():
    global launcher_angle
    launcher.image.fill(0)
    rad = launcher_angle * (Math.PI / 180)
    
    # Gun barrel
    x2 = 16 - Math.cos(rad) * 15
    y2 = 16 - Math.sin(rad) * 15
    launcher.image.draw_line(16, 16, x2, y2, 1)
    launcher.image.fill_rect(14, 14, 4, 4, 1)

    # PROJECTED PATH (Aiming dots)
    dot_x = 80
    dot_y = 110
    vx = -Math.cos(rad)
    vy = -Math.sin(rad)
    for i in range(12):
        dot_x += vx * 10
        dot_y += vy * 10
        if dot_x <= 8 or dot_x >= 152:
            vx *= -1
        if dot_y > 5 and dot_y < 105:
            scene.background_image().set_pixel(dot_x, dot_y, 1)

def create_bubble_img(color: number):
    temp_img = image.create(16, 16)
    temp_img.fill_circle(8, 8, 7, color)
    temp_img.draw_circle(8, 8, 7, 1)
    return temp_img

def update_previews():
    global next_color, loaded_color
    next_bubble_preview.set_image(create_bubble_img(next_color))
    loaded_bubble_sprite.set_image(create_bubble_img(loaded_color))
    draw_launcher()

# 4. CEILING LOGIC
def drop_ceiling():
    global ceiling_timer, ceiling_drops
    ceiling_timer = game.runtime()
    ceiling_drops += 1
    
    all_enemies = sprites.all_of_kind(SpriteKind.enemy)
    # Shift existing bubbles down
    for i in range(len(all_enemies)):
        all_enemies[i].y += 14
        if all_enemies[i].y > 100:
            handle_game_over()
            return

    # Add new top row with proper parity offset
    for c in range(8):
        if Math.percent_chance(80):
            b = sprites.create(create_bubble_img(Math.pick_random(COLORS)), SpriteKind.enemy)
            x_off = 8 if (ceiling_drops % 2 == 1) else 0
            b.set_position(c * 16 + 24 + x_off, 10)
    
    music.play(music.melody_playable(music.big_crash), music.PlaybackMode.IN_BACKGROUND)

# 5. CORE LOGIC
def start_level(lvl: number):
    global level, game_active, shoot_timer, ceiling_timer, ceiling_drops
    level = lvl
    game_active = True
    ceiling_drops = 0
    shoot_timer = game.runtime()
    ceiling_timer = game.runtime()
    sprites.destroy_all_sprites_of_kind(SpriteKind.enemy)
    scene.background_image().fill(0)
    
    # Randomly generate 2 rows for each of the 1000 levels
    for r in range(2):
        for c in range(8):
            if Math.percent_chance(80):
                b = sprites.create(create_bubble_img(Math.pick_random(COLORS)), SpriteKind.enemy)
                b.set_position(get_pos_x(r, c), get_pos_y(r, c))
    update_previews()

def handle_game_over():
    global game_active, is_moving
    game_active = False
    is_moving = False
    game.show_long_text("GAME OVER!", DialogLayout.CENTER)
    start_level(1)

def handle_collision():
    global is_moving, current_bubble, shoot_timer
    is_moving = False
    shoot_timer = game.runtime()
    
    # Snap to grid maintaining hexagonal parity
    row = Math.round((current_bubble.y - 10) / 14)
    y_target = row * 14 + 10
    current_offset = 8 if (row % 2 != ceiling_drops % 2) else 0
    col = Math.round((current_bubble.x - 24 - current_offset) / 16)
    x_target = col * 16 + 24 + current_offset
    
    current_bubble.set_position(x_target, y_target)
    current_bubble.set_kind(SpriteKind.enemy)
    current_bubble.set_velocity(0, 0)
    
    match_color = current_bubble.image.get_pixel(8, 8)
    matches: List[Sprite] = [current_bubble]
    m_queue: List[Sprite] = [current_bubble]
    all_enemies = sprites.all_of_kind(SpriteKind.enemy)
    
    while len(m_queue) > 0:
        c = m_queue.shift()
        for m_idx in range(len(all_enemies)):
            o = all_enemies[m_idx]
            if o not in matches and o.image.get_pixel(8, 8) == match_color:
                d = Math.sqrt((c.x - o.x)**2 + (c.y - o.y)**2)
                if d < 18:
                    matches.append(o)
                    m_queue.append(o)
    
    if len(matches) >= 3:
        music.play(music.melody_playable(music.ba_ding), music.PlaybackMode.IN_BACKGROUND)
        for p_idx in range(len(matches)):
            matches[p_idx].set_kind(SpriteKind.food)
            matches[p_idx].vy = 120
            matches[p_idx].lifespan = 2000
            
    if current_bubble.y > 100:
        handle_game_over()
    elif len(sprites.all_of_kind(SpriteKind.enemy)) == 0:
        start_level(level + 1)

# 6. INPUT HANDLERS
def press_left():
    global launcher_angle
    launcher_angle = Math.clamp(15, 165, launcher_angle - 3) # Precision rotation
    scene.background_image().fill(0)
    draw_launcher()

def press_right():
    global launcher_angle
    launcher_angle = Math.clamp(15, 165, launcher_angle + 3)
    scene.background_image().fill(0)
    draw_launcher()

def shoot_action():
    global is_moving, current_bubble, next_color, loaded_color, launcher_angle, game_active, shoot_timer
    if not game_active:
        start_level(1)
        return
    if not is_moving:
        is_moving = True
        shoot_timer = game.runtime()
        music.play(music.melody_playable(music.pew_pew), music.PlaybackMode.IN_BACKGROUND)
        current_bubble = sprites.create(create_bubble_img(loaded_color), SpriteKind.projectile)
        current_bubble.set_position(80, 110)
        loaded_color = next_color
        next_color = Math.pick_random(COLORS)
        rad = launcher_angle * (Math.PI / 180)
        current_bubble.vx = -Math.cos(rad) * 160
        current_bubble.vy = -Math.sin(rad) * 160
        update_previews()

def skip_level_handler():
    global level
    start_level(level + 1)

# Default Key Mappings
controller.left.on_event(ControllerButtonEvent.PRESSED, press_left)
controller.left.on_event(ControllerButtonEvent.REPEATED, press_left)
controller.right.on_event(ControllerButtonEvent.PRESSED, press_right)
controller.right.on_event(ControllerButtonEvent.REPEATED, press_right)

# Physical Mapping: Space/Z/X/S/Enter all act as triggers
controller.A.on_event(ControllerButtonEvent.PRESSED, shoot_action)
controller.B.on_event(ControllerButtonEvent.PRESSED, shoot_action)
controller.down.on_event(ControllerButtonEvent.PRESSED, shoot_action)
controller.menu.on_event(ControllerButtonEvent.PRESSED, skip_level_handler)

# 7. GAME LOOP
def on_update():
    global is_moving, current_bubble, game_active, shoot_timer, ceiling_timer
    if not game_active:
        return

    # Auto-shoot (7s)
    if not is_moving and (game.runtime() - shoot_timer > AUTO_SHOOT_LIMIT):
        shoot_action()

    # Ceiling drop (20s)
    if game.runtime() - ceiling_timer > CEILING_DROP_LIMIT:
        drop_ceiling()

    if is_moving and current_bubble:
        if current_bubble.x <= 8 or current_bubble.x >= 152:
            current_bubble.vx *= -1
        if current_bubble.y <= 8:
            handle_collision()
        else:
            all_enemies = sprites.all_of_kind(SpriteKind.enemy)
            for e_idx in range(len(all_enemies)):
                if current_bubble.overlaps_with(all_enemies[e_idx]):
                    handle_collision()
                    break

game.on_update(on_update)

# 8. START
start_level(1)