# 1. STATE & CONSTANTS
level = 1
launcher_angle = 90
is_moving = False
game_active = False
current_bubble: Sprite = None

COLORS = [2, 4, 5, 7, 8, 9]
next_color = Math.pick_random(COLORS)
loaded_color = Math.pick_random(COLORS)

# 2. SPRITE DEFINITIONS
launcher = sprites.create(image.create(32, 32), SpriteKind.player)
launcher.set_position(80, 110)

loaded_bubble_sprite = sprites.create(image.create(16, 16), SpriteKind.player)
loaded_bubble_sprite.set_position(80, 110)

next_bubble_preview = sprites.create(image.create(16, 16), SpriteKind.player)
next_bubble_preview.set_position(20, 110)

# 3. HELPER FUNCTIONS
def get_pos_x(r: number, c: number):
    # Hexagonal nesting for tight packing
    x_off = 8 if (r % 2 == 1) else 0
    return c * 16 + 24 + x_off

def get_pos_y(r: number, c: number):
    return r * 14 + 10

def draw_launcher():
    global launcher_angle
    launcher.image.fill(0)
    rad = launcher_angle * (Math.PI / 180)
    x2 = 16 - Math.cos(rad) * 15
    y2 = 16 - Math.sin(rad) * 15
    launcher.image.draw_line(16, 16, x2, y2, 1)
    launcher.image.fill_rect(14, 14, 4, 4, 1)

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

# 4. ANIMATION & CLEANUP
def drop_bubble(b: Sprite):
    b.set_kind(SpriteKind.food)
    b.vy = 100
    b.ay = 200
    b.lifespan = 2000

def clean_up_floating():
    connected: List[Sprite] = []
    queue: List[Sprite] = []
    all_bubbles = sprites.all_of_kind(SpriteKind.enemy)
    
    for i in range(len(all_bubbles)):
        b = all_bubbles[i]
        if b.y <= 12:
            queue.append(b)
            connected.append(b)
            
    while len(queue) > 0:
        curr = queue.shift() # Static Python array management
        for j in range(len(all_bubbles)):
            other = all_bubbles[j]
            if other not in connected:
                dist = Math.sqrt((curr.x - other.x)**2 + (curr.y - other.y)**2)
                if dist < 18:
                    connected.append(other)
                    queue.append(other)
                    
    for k in range(len(all_bubbles)):
        target = all_bubbles[k]
        if target not in connected:
            drop_bubble(target)

# 5. CORE LOGIC
def start_level(lvl: number):
    global level, game_active
    level = lvl
    game_active = True
    sprites.destroy_all_sprites_of_kind(SpriteKind.enemy)
    
    # Static 2 rows as requested for short console space
    for r in range(2):
        for c in range(8):
            # Randomize position and colors
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
    global is_moving, level, current_bubble
    is_moving = False
    
    row = Math.round((current_bubble.y - 10) / 14)
    col_off = 8 if (row % 2 == 1) else 0
    col = Math.round((current_bubble.x - 24 - col_off) / 16)
    current_bubble.set_position(get_pos_x(row, col), get_pos_y(row, col))
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
            drop_bubble(matches[p_idx])
        clean_up_floating()
    
    if current_bubble.y > 100:
        handle_game_over()
        return

    if len(sprites.all_of_kind(SpriteKind.enemy)) == 0:
        start_level(level + 1)

# 6. INPUT HANDLERS
def press_left():
    global launcher_angle
    launcher_angle = Math.clamp(15, 165, launcher_angle - 8)
    draw_launcher()

def press_right():
    global launcher_angle
    launcher_angle = Math.clamp(15, 165, launcher_angle + 8)
    draw_launcher()

def shoot_action():
    global is_moving, current_bubble, next_color, loaded_color, launcher_angle, game_active
    if not game_active:
        start_level(1)
        return
    if not is_moving:
        is_moving = True
        music.play(music.melody_playable(music.pew_pew), music.PlaybackMode.IN_BACKGROUND)
        current_bubble = sprites.create(create_bubble_img(loaded_color), SpriteKind.projectile)
        current_bubble.set_position(80, 110)
        loaded_color = next_color
        next_color = Math.pick_random(COLORS)
        rad = launcher_angle * (Math.PI / 180)
        current_bubble.vx = -Math.cos(rad) * 150
        current_bubble.vy = -Math.sin(rad) * 150
        update_previews()

def skip_level():
    global level
    if level < 1000:
        start_level(level + 1)

controller.left.on_event(ControllerButtonEvent.PRESSED, press_left)
controller.left.on_event(ControllerButtonEvent.REPEATED, press_left)
controller.right.on_event(ControllerButtonEvent.PRESSED, press_right)
controller.right.on_event(ControllerButtonEvent.REPEATED, press_right)

# Shooting: A (Spacebar)
controller.A.on_event(ControllerButtonEvent.PRESSED, shoot_action)
# Next Level: B (Maps to 'X' on keyboard)
controller.B.on_event(ControllerButtonEvent.PRESSED, skip_level)

# 7. GAME LOOP
def on_update():
    global is_moving, current_bubble, game_active
    if is_moving and current_bubble and game_active:
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
