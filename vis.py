import pygame
import sys
import math
import random
import tkinter as tk
from tkinter import filedialog

def choose_file():
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(
        title="(Replay File)",
        filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
    )
    return file_path

def load_replay(filename):
    with open(filename, 'r') as f:
        lines = [line.strip() for line in f.readlines() if line.strip()]
    
    parts = lines[0].split()
    W, H, NUM_AGENTS = int(parts[0]), int(parts[1]), int(parts[2])
    NUM_WALLS = int(parts[3]) if len(parts) > 3 else 0
    
    starts = list(map(int, lines[1].split()))
    is_mine = list(map(int, lines[2].split()))
    
    walls = []
    move_start_idx = 3
    if NUM_WALLS > 0:
        walls = list(map(int, lines[3].split()))
        move_start_idx = 4
        
    moves = []
    winner = 0
    for line in lines[move_start_idx:]:
        parts = line.split()
        if parts[0] == 'W':
            winner = int(parts[1])
        else:
            moves.append(parts)
            
    return W, H, NUM_AGENTS, starts, is_mine, walls, moves, winner

def precompute_paths(starts, moves, W, NUM_AGENTS):
    move_dict = {'U': (0, -1), 'D': (0, 1), 'L': (-1, 0), 'R': (1, 0), '?': (0, 0)}
    paths = [[(starts[i] % W, starts[i] // W)] for i in range(NUM_AGENTS)]
    alive_history = [[True] * NUM_AGENTS]
    current_alive = [True] * NUM_AGENTS
    death_turns = [-1] * NUM_AGENTS
    
    for turn_idx, turn_moves in enumerate(moves):
        for i in range(NUM_AGENTS):
            m = turn_moves[i] if i < len(turn_moves) else '?'
            if m == '?' and current_alive[i]:
                current_alive[i] = False
                death_turns[i] = turn_idx
            
            px, py = paths[i][-1]
            dx, dy = move_dict.get(m, (0, 0))
            paths[i].append((px + dx, py + dy))
            
        alive_history.append(list(current_alive))
        
    for i in range(NUM_AGENTS):
        if death_turns[i] == -1: death_turns[i] = len(moves)
            
    return paths, alive_history, death_turns


class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(1, 5)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.timer = random.randint(20, 40)
        self.color = color

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.timer -= 1

    def draw(self, surface):
        if self.timer > 0:
            alpha = max(0, int(255 * (self.timer / 40)))
            surf = pygame.Surface((4, 4), pygame.SRCALPHA)
            pygame.draw.circle(surf, (*self.color, alpha), (2, 2), 2)
            surface.blit(surf, (int(self.x), int(self.y)))

def create_glow_surface(width, height, color, radius, solid_core=True):
    surf = pygame.Surface((width + radius*2, height + radius*2), pygame.SRCALPHA)
    for r in range(radius, 0, -2):
        alpha = int(255 * (1 - r/radius)**2 * 0.3)
        pygame.draw.rect(surf, (*color, alpha), (radius-r, radius-r, width+r*2, height+r*2), border_radius=r)
    
    if solid_core:
        pygame.draw.rect(surf, color, (radius, radius, width, height), border_radius=2)
        
    return surf

def draw_neon_line(surface, color, start, end, width):
    pygame.draw.line(surface, (*color, 100), start, end, width + 8)
    pygame.draw.line(surface, color, start, end, width)
    pygame.draw.line(surface, (255, 255, 255), start, end, max(2, width // 3))

def lerp(a, b, t):
    return a + (b - a) * t


def main():
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
    else:
        filepath = choose_file() 
        
    if not filepath: sys.exit()

    W, H, NUM_AGENTS, starts, is_mine, walls, moves, winner = load_replay(filepath)
    paths, alive_history, death_turns = precompute_paths(starts, moves, W, NUM_AGENTS)
    max_turns = len(moves)

    MAX_BOARD_PIXELS = 800
    CELL_SIZE = min(MAX_BOARD_PIXELS // W, MAX_BOARD_PIXELS // H)
    CELL_SIZE = max(CELL_SIZE, 15)

    BOARD_W = W * CELL_SIZE
    BOARD_H = H * CELL_SIZE
    SIDE_PANEL_W = 350
    BOTTOM_UI_H = 80
    
    WIDTH = BOARD_W + SIDE_PANEL_W
    HEIGHT = max(BOARD_H, 600) + BOTTOM_UI_H

    BG_COLOR = (10, 5, 20)
    GRID_COLOR = (40, 20, 60)
    PANEL_BG = (15, 10, 25)
    TEAM_1_COLORS = [(0, 255, 255), (0, 150, 255), (0, 255, 150), (100, 100, 255)] 
    TEAM_2_COLORS = [(255, 0, 127), (255, 100, 0), (255, 50, 50), (200, 0, 200)]   
    WALL_COLOR = (80, 80, 90)

    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption(f"Tron AI PvP - Cyberpunk Animated")
    
    font_title = pygame.font.SysFont("impact", 32)
    font_bold = pygame.font.SysFont("arial", 22, bold=True)
    font_small = pygame.font.SysFont("arial", 18)
    clock = pygame.time.Clock()

    wall_surf = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
    pygame.draw.rect(wall_surf, (50, 50, 70), (0, 0, CELL_SIZE, CELL_SIZE))
    pygame.draw.rect(wall_surf, (100, 100, 130), (2, 2, CELL_SIZE-4, CELL_SIZE-4), 2)
    pygame.draw.line(wall_surf, (150, 150, 180), (4, 4), (CELL_SIZE-4, CELL_SIZE-4), 1)

    glow_radius = CELL_SIZE // 2
    rect_size = CELL_SIZE - 4
    t1_glows = [create_glow_surface(rect_size, rect_size, c, glow_radius) for c in TEAM_1_COLORS]
    t2_glows = [create_glow_surface(rect_size, rect_size, c, glow_radius) for c in TEAM_2_COLORS]
    wall_glow = create_glow_surface(CELL_SIZE, CELL_SIZE, WALL_COLOR, 4)

    current_turn = 0
    is_playing = False
    speed_delay = 300 
    last_update_time = pygame.time.get_ticks()
    bg_offset_y = 0
    particles = []
    exploded_agents = set()

    while True:
        current_time = pygame.time.get_ticks()
        
        anim_progress = 0.0
        if is_playing:
            anim_progress = min(1.0, (current_time - last_update_time) / max(1, speed_delay))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE: is_playing = not is_playing
                elif event.key == pygame.K_RIGHT:
                    is_playing = False; anim_progress = 0; particles.clear(); exploded_agents.clear()
                    if current_turn < max_turns: current_turn += 1
                elif event.key == pygame.K_LEFT:
                    is_playing = False; anim_progress = 0; particles.clear(); exploded_agents.clear()
                    if current_turn > 0: current_turn -= 1
                elif event.key == pygame.K_UP: speed_delay = max(50, speed_delay - 50)
                elif event.key == pygame.K_DOWN: speed_delay = min(1000, speed_delay + 50)

        if is_playing and anim_progress >= 1.0:
            if current_turn < max_turns:
                current_turn += 1
                last_update_time = current_time
                anim_progress = 0.0
            else:
                is_playing = False

        screen.fill(BG_COLOR)

        bg_offset_y = (bg_offset_y + 0.5) % CELL_SIZE
        for x in range(0, BOARD_W + 1, CELL_SIZE):
            pygame.draw.line(screen, GRID_COLOR, (x, 0), (x, BOARD_H), 1)
        for y in range(0, BOARD_H + CELL_SIZE, CELL_SIZE):
            pygame.draw.line(screen, GRID_COLOR, (0, y + bg_offset_y - CELL_SIZE), (BOARD_W, y + bg_offset_y - CELL_SIZE), 1)

        for w_idx in walls:
            wx, wy = w_idx % W, w_idx // W
            screen.blit(wall_glow, (wx * CELL_SIZE - 4, wy * CELL_SIZE - 4))
            screen.blit(wall_surf, (wx * CELL_SIZE, wy * CELL_SIZE))

        t1_count, t2_count = 0, 0
        agent_colors = []

        for i in range(NUM_AGENTS):
            if is_mine[i]:
                glow = t1_glows[t1_count % len(TEAM_1_COLORS)]
                main_color = TEAM_1_COLORS[t1_count % len(TEAM_1_COLORS)]
                t1_count += 1
            else:
                glow = t2_glows[t2_count % len(TEAM_2_COLORS)]
                main_color = TEAM_2_COLORS[t2_count % len(TEAM_2_COLORS)]
                t2_count += 1
                
            agent_colors.append(main_color)

            path_points = []
            for t in range(current_turn + 1):
                px, py = paths[i][t]
                path_points.append((px * CELL_SIZE + CELL_SIZE//2, py * CELL_SIZE + CELL_SIZE//2))

            if len(path_points) > 1:
                neon_surface = pygame.Surface((BOARD_W, BOARD_H), pygame.SRCALPHA)
                pygame.draw.lines(neon_surface, (*main_color, 150), False, path_points, CELL_SIZE // 2 + 4)
                pygame.draw.lines(neon_surface, main_color, False, path_points, CELL_SIZE // 2 - 2)
                pygame.draw.lines(neon_surface, (255,255,255), False, path_points, 2)
                screen.blit(neon_surface, (0,0))

            if alive_history[current_turn][i]:
                curr_pos = paths[i][current_turn]
                
                if is_playing and current_turn < max_turns and alive_history[current_turn+1][i]:
                    next_pos = paths[i][current_turn + 1]
                    anim_x = lerp(curr_pos[0], next_pos[0], anim_progress)
                    anim_y = lerp(curr_pos[1], next_pos[1], anim_progress)
                    
                    start_pt = (curr_pos[0]*CELL_SIZE + CELL_SIZE//2, curr_pos[1]*CELL_SIZE + CELL_SIZE//2)
                    end_pt = (anim_x*CELL_SIZE + CELL_SIZE//2, anim_y*CELL_SIZE + CELL_SIZE//2)
                    if start_pt != end_pt:
                        draw_neon_line(screen, main_color, start_pt, end_pt, CELL_SIZE // 2 - 2)
                else:
                    anim_x, anim_y = curr_pos[0], curr_pos[1]

                draw_x = anim_x * CELL_SIZE + 2 - glow_radius
                draw_y = anim_y * CELL_SIZE + 2 - glow_radius
                screen.blit(glow, (draw_x, draw_y))
                
                head_center = (int(anim_x * CELL_SIZE + CELL_SIZE//2), int(anim_y * CELL_SIZE + CELL_SIZE//2))
                pygame.draw.circle(screen, (255, 255, 255), head_center, max(3, CELL_SIZE//4))
            else:
                if i not in exploded_agents and current_turn == death_turns[i]:
                    dead_pos = paths[i][death_turns[i]]
                    px = dead_pos[0] * CELL_SIZE + CELL_SIZE//2
                    py = dead_pos[1] * CELL_SIZE + CELL_SIZE//2
                    for _ in range(30):
                        particles.append(Particle(px, py, main_color))
                    exploded_agents.add(i)
                
                if current_turn >= death_turns[i]:
                    dead_pos = paths[i][death_turns[i]]
                    draw_x = dead_pos[0]*CELL_SIZE + 2 - glow_radius
                    draw_y = dead_pos[1]*CELL_SIZE + 2 - glow_radius
                    screen.blit(glow, (draw_x, draw_y))
                    pygame.draw.line(screen, (255, 50, 50), (dead_pos[0]*CELL_SIZE, dead_pos[1]*CELL_SIZE), (dead_pos[0]*CELL_SIZE+CELL_SIZE, dead_pos[1]*CELL_SIZE+CELL_SIZE), 2)

        for p in particles[:]:
            p.update()
            p.draw(screen)
            if p.timer <= 0:
                particles.remove(p)

        pygame.draw.rect(screen, PANEL_BG, (BOARD_W, 0, SIDE_PANEL_W, HEIGHT))
        pygame.draw.line(screen, (100, 50, 150), (BOARD_W, 0), (BOARD_W, HEIGHT), 3)

        screen.blit(font_title.render("CYBER MATCH STATS", True, (255, 255, 255)), (BOARD_W + 20, 20))
        pygame.draw.line(screen, (100, 100, 150), (BOARD_W + 20, 60), (BOARD_W + SIDE_PANEL_W - 20, 60), 2)

        y_offset = 80
        for i in range(NUM_AGENTS):
            team_str = "TEAM BLUE" if is_mine[i] else "TEAM RED"
            is_alive = alive_history[current_turn][i]
            current_score = current_turn + 1 if is_alive else death_turns[i] + 1
            
            panel_rect = pygame.Surface((SIDE_PANEL_W - 40, 60), pygame.SRCALPHA)
            pygame.draw.rect(panel_rect, (*agent_colors[i], 30 if is_alive else 10), (0, 0, SIDE_PANEL_W - 40, 60), border_radius=8)
            screen.blit(panel_rect, (BOARD_W + 20, y_offset))

            pygame.draw.rect(screen, agent_colors[i], (BOARD_W + 30, y_offset + 20, 20, 20), border_radius=4)
            
            agent_txt = font_bold.render(f"Agent {i+1} [{team_str}]", True, (255,255,255) if is_alive else (100,100,100))
            screen.blit(agent_txt, (BOARD_W + 60, y_offset + 5))
            
            if is_alive:
                status_surf = font_small.render("ONLINE", True, (50, 255, 50))
            else:
                status_surf = font_small.render("DESTROYED", True, (255, 50, 50))
            screen.blit(status_surf, (BOARD_W + 60, y_offset + 30))
            
            score_surf = font_bold.render(f"{current_score}", True, agent_colors[i])
            screen.blit(score_surf, (BOARD_W + 280, y_offset + 15))

            y_offset += 75

        pygame.draw.rect(screen, (10, 5, 15), (0, max(BOARD_H, HEIGHT - BOTTOM_UI_H), BOARD_W, BOTTOM_UI_H))
        pygame.draw.line(screen, (100, 50, 150), (0, max(BOARD_H, HEIGHT - BOTTOM_UI_H)), (BOARD_W, max(BOARD_H, HEIGHT - BOTTOM_UI_H)), 2)
        
        status_txt = "▶ PLAYING" if is_playing else "⏸ PAUSED"
        color_status = (0, 255, 255) if is_playing else (255, 255, 0)
        
        screen.blit(font_bold.render(f"{status_txt}   |   TURN: {current_turn}/{max_turns}   |   SPEED: {speed_delay}ms", True, color_status), (20, HEIGHT - 60))
        screen.blit(font_small.render("Keys: [SPACE] Play/Pause | [ARROWS] Navigate & Speed", True, (150, 150, 150)), (20, HEIGHT - 30))

        if current_turn == max_turns:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))

            if winner == 1:
                win_text = "🏆 TEAM BLUE VICTORIOUS! 🏆"
                win_color = (0, 255, 255)
            elif winner == 2:
                win_text = "💀 TEAM RED VICTORIOUS! 💀"
                win_color = (255, 50, 50)
            else:
                win_text = "🤝 DRAW! 🤝"
                win_color = (200, 200, 200)

            large_font = pygame.font.SysFont("impact", 50)
            text_surf = large_font.render(win_text, True, win_color)
            text_rect = text_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 50))

            glow_surf = create_glow_surface(text_rect.width, text_rect.height, win_color, 20, solid_core=False)
            
            text_surf = large_font.render(win_text, True, (255, 255, 255))
            screen.blit(glow_surf, (text_rect.x - 20, text_rect.y - 20))
            screen.blit(text_surf, text_rect)
            
            sub_text = font_bold.render(f"Match ended in {max_turns} turns", True, (200, 200, 200))
            screen.blit(sub_text, sub_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 20)))

        pygame.display.flip() 
        clock.tick(60)

if __name__ == "__main__":
    main()