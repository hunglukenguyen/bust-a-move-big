//  1. STATE & CONSTANTS
let level = 1
let launcher_angle = 90
let is_moving = false
let game_active = false
let ceiling_drops = 0
let current_bubble : Sprite = null
let COLORS = [2, 4, 5, 7, 8, 9]
let next_color = Math.pickRandom(COLORS)
let loaded_color = Math.pickRandom(COLORS)
//  Timers in milliseconds
let shoot_timer = 0
let ceiling_timer = 0
let AUTO_SHOOT_LIMIT = 7000
let CEILING_DROP_LIMIT = 20000
//  2. SPRITE DEFINITIONS
let launcher = sprites.create(image.create(32, 32), SpriteKind.Player)
launcher.setPosition(80, 110)
let loaded_bubble_sprite = sprites.create(image.create(16, 16), SpriteKind.Player)
loaded_bubble_sprite.setPosition(80, 110)
let next_bubble_preview = sprites.create(image.create(16, 16), SpriteKind.Player)
next_bubble_preview.setPosition(20, 110)
//  3. HELPER FUNCTIONS
function get_pos_x(r: number, c: number): number {
    let x_off = r % 2 == 1 ? 8 : 0
    return c * 16 + 24 + x_off
}

function get_pos_y(r: number, c: number): number {
    return r * 14 + 10
}

function draw_launcher() {
    
    launcher.image.fill(0)
    let rad = launcher_angle * (Math.PI / 180)
    //  Gun barrel
    let x2 = 16 - Math.cos(rad) * 15
    let y2 = 16 - Math.sin(rad) * 15
    launcher.image.drawLine(16, 16, x2, y2, 1)
    launcher.image.fillRect(14, 14, 4, 4, 1)
    //  PROJECTED PATH (Aiming dots)
    let dot_x = 80
    let dot_y = 110
    let vx = -Math.cos(rad)
    let vy = -Math.sin(rad)
    for (let i = 0; i < 12; i++) {
        dot_x += vx * 10
        dot_y += vy * 10
        if (dot_x <= 8 || dot_x >= 152) {
            vx *= -1
        }
        
        if (dot_y > 5 && dot_y < 105) {
            scene.backgroundImage().setPixel(dot_x, dot_y, 1)
        }
        
    }
}

function create_bubble_img(color: number): Image {
    let temp_img = image.create(16, 16)
    temp_img.fillCircle(8, 8, 7, color)
    temp_img.drawCircle(8, 8, 7, 1)
    return temp_img
}

function update_previews() {
    
    next_bubble_preview.setImage(create_bubble_img(next_color))
    loaded_bubble_sprite.setImage(create_bubble_img(loaded_color))
    draw_launcher()
}

//  4. CEILING LOGIC
function drop_ceiling() {
    let b: Sprite;
    let x_off: any;
    
    ceiling_timer = game.runtime()
    ceiling_drops += 1
    let all_enemies = sprites.allOfKind(SpriteKind.Enemy)
    //  Shift existing bubbles down
    for (let i = 0; i < all_enemies.length; i++) {
        all_enemies[i].y += 14
        if (all_enemies[i].y > 100) {
            handle_game_over()
            return
        }
        
    }
    //  Add new top row with proper parity offset
    for (let c = 0; c < 8; c++) {
        if (Math.percentChance(80)) {
            b = sprites.create(create_bubble_img(Math.pickRandom(COLORS)), SpriteKind.Enemy)
            x_off = ceiling_drops % 2 == 1 ? 8 : 0
            b.setPosition(c * 16 + 24 + x_off, 10)
        }
        
    }
    music.play(music.melodyPlayable(music.bigCrash), music.PlaybackMode.InBackground)
}

//  5. CORE LOGIC
function start_level(lvl: number) {
    let b: Sprite;
    
    level = lvl
    game_active = true
    ceiling_drops = 0
    shoot_timer = game.runtime()
    ceiling_timer = game.runtime()
    sprites.destroyAllSpritesOfKind(SpriteKind.Enemy)
    scene.backgroundImage().fill(0)
    //  Randomly generate 2 rows for each of the 1000 levels
    for (let r = 0; r < 2; r++) {
        for (let c = 0; c < 8; c++) {
            if (Math.percentChance(80)) {
                b = sprites.create(create_bubble_img(Math.pickRandom(COLORS)), SpriteKind.Enemy)
                b.setPosition(get_pos_x(r, c), get_pos_y(r, c))
            }
            
        }
    }
    update_previews()
}

function handle_game_over() {
    
    game_active = false
    is_moving = false
    game.showLongText("GAME OVER!", DialogLayout.Center)
    start_level(1)
}

function handle_collision() {
    let c: Sprite;
    let o: Sprite;
    let d: number;
    
    is_moving = false
    shoot_timer = game.runtime()
    //  Snap to grid maintaining hexagonal parity
    let row = Math.round((current_bubble.y - 10) / 14)
    let y_target = row * 14 + 10
    let current_offset = row % 2 != ceiling_drops % 2 ? 8 : 0
    let col = Math.round((current_bubble.x - 24 - current_offset) / 16)
    let x_target = col * 16 + 24 + current_offset
    current_bubble.setPosition(x_target, y_target)
    current_bubble.setKind(SpriteKind.Enemy)
    current_bubble.setVelocity(0, 0)
    let match_color = current_bubble.image.getPixel(8, 8)
    let matches = [current_bubble]
    let m_queue = [current_bubble]
    let all_enemies = sprites.allOfKind(SpriteKind.Enemy)
    while (m_queue.length > 0) {
        c = m_queue.shift()
        for (let m_idx = 0; m_idx < all_enemies.length; m_idx++) {
            o = all_enemies[m_idx]
            if (matches.indexOf(o) < 0 && o.image.getPixel(8, 8) == match_color) {
                d = Math.sqrt((c.x - o.x) ** 2 + (c.y - o.y) ** 2)
                if (d < 18) {
                    matches.push(o)
                    m_queue.push(o)
                }
                
            }
            
        }
    }
    if (matches.length >= 3) {
        music.play(music.melodyPlayable(music.baDing), music.PlaybackMode.InBackground)
        for (let p_idx = 0; p_idx < matches.length; p_idx++) {
            matches[p_idx].setKind(SpriteKind.Food)
            matches[p_idx].vy = 120
            matches[p_idx].lifespan = 2000
        }
    }
    
    if (current_bubble.y > 100) {
        handle_game_over()
    } else if (sprites.allOfKind(SpriteKind.Enemy).length == 0) {
        start_level(level + 1)
    }
    
}

//  6. INPUT HANDLERS
function press_left() {
    
    launcher_angle = Math.clamp(15, 165, launcher_angle - 3)
    //  Precision rotation
    scene.backgroundImage().fill(0)
    draw_launcher()
}

function press_right() {
    
    launcher_angle = Math.clamp(15, 165, launcher_angle + 3)
    scene.backgroundImage().fill(0)
    draw_launcher()
}

function shoot_action() {
    let rad: number;
    
    if (!game_active) {
        start_level(1)
        return
    }
    
    if (!is_moving) {
        is_moving = true
        shoot_timer = game.runtime()
        music.play(music.melodyPlayable(music.pewPew), music.PlaybackMode.InBackground)
        current_bubble = sprites.create(create_bubble_img(loaded_color), SpriteKind.Projectile)
        current_bubble.setPosition(80, 110)
        loaded_color = next_color
        next_color = Math.pickRandom(COLORS)
        rad = launcher_angle * (Math.PI / 180)
        current_bubble.vx = -Math.cos(rad) * 160
        current_bubble.vy = -Math.sin(rad) * 160
        update_previews()
    }
    
}

//  Default Key Mappings
controller.left.onEvent(ControllerButtonEvent.Pressed, press_left)
controller.left.onEvent(ControllerButtonEvent.Repeated, press_left)
controller.right.onEvent(ControllerButtonEvent.Pressed, press_right)
controller.right.onEvent(ControllerButtonEvent.Repeated, press_right)
//  Physical Mapping: Space/Z/X/S/Enter all act as triggers
controller.A.onEvent(ControllerButtonEvent.Pressed, shoot_action)
controller.B.onEvent(ControllerButtonEvent.Pressed, shoot_action)
controller.down.onEvent(ControllerButtonEvent.Pressed, shoot_action)
controller.menu.onEvent(ControllerButtonEvent.Pressed, function skip_level_handler() {
    
    start_level(level + 1)
})
//  7. GAME LOOP
game.onUpdate(function on_update() {
    let all_enemies: Sprite[];
    
    if (!game_active) {
        return
    }
    
    //  Auto-shoot (7s)
    if (!is_moving && game.runtime() - shoot_timer > AUTO_SHOOT_LIMIT) {
        shoot_action()
    }
    
    //  Ceiling drop (20s)
    if (game.runtime() - ceiling_timer > CEILING_DROP_LIMIT) {
        drop_ceiling()
    }
    
    if (is_moving && current_bubble) {
        if (current_bubble.x <= 8 || current_bubble.x >= 152) {
            current_bubble.vx *= -1
        }
        
        if (current_bubble.y <= 8) {
            handle_collision()
        } else {
            all_enemies = sprites.allOfKind(SpriteKind.Enemy)
            for (let e_idx = 0; e_idx < all_enemies.length; e_idx++) {
                if (current_bubble.overlapsWith(all_enemies[e_idx])) {
                    handle_collision()
                    break
                }
                
            }
        }
        
    }
    
})
//  8. START
start_level(1)
