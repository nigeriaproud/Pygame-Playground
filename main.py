import pygame as pg
import math
import random
import sys
import os

# --- 定数設定 ---
SCREEN_W, SCREEN_H = 600, 800
WORLD_H = 2400

# ストーン設定
STONE_RADIUS = 38
COURSE_WIDTH_HALF = 320
PLAY_MIN_X = SCREEN_W // 2 - COURSE_WIDTH_HALF
PLAY_MAX_X = SCREEN_W // 2 + COURSE_WIDTH_HALF

# 摩擦・パワー設定
FRICTION_NORMAL = 0.985
FRICTION_SWEEP = 0.995
POWER_MAX = 35

# --- 色の定義 ---
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (230, 60, 60)
YELLOW = (230, 210, 40)
BLUE = (50, 100, 200)
GRANITE_GRAY = (180, 180, 190)
SHADOW_COLOR = (0, 0, 0, 60)

SKY_COLOR_TOP = (10, 15, 30)
SKY_COLOR_BTM = (60, 80, 120)
ICE_BASE = (240, 245, 255)
FLOOR_COLOR = (200, 210, 220)
FENCE_POST = (100, 80, 60)
FENCE_ROPE = (80, 60, 40)

MAX_ENDS = 2
STONES_PER_END = 8
STONES_PER_TEAM = 4

START_Y = WORLD_H - 300
TARGET_Y = 400
SWITCH_VIEW_LINE = TARGET_Y + 500

HORIZON_Y = 150
VIEW_DIST = 5000
CAMERA_HEIGHT = 500
FOCAL_LENGTH = 500

# --- フォントヘルパー関数 ---
def get_jp_font(size):
  """ OSに合わせて日本語フォントを読み込む """
  font_names = ["meiryo", "yugothic", "hiraginosans",
                "notosanscjkjp", "msgothic", "ipagothic"]
  return pg.font.SysFont(font_names, size)

# --- クラス定義 ---

class SweepParticle:
  def __init__(self, x, y):
    self.x = x
    self.y = y
    angle = random.uniform(0, math.pi * 2)
    speed = random.uniform(2, 6)
    self.vx = math.cos(angle) * speed
    self.vy = math.sin(angle) * speed
    self.life = random.randint(20, 40)
    self.size = random.randint(3, 6)
    self.color = (200, 230, 255)

  def update(self):
    self.x += self.vx
    self.y += self.vy
    self.life -= 1
    self.size = max(0, self.size - 0.1)

  def draw(self, screen):
    if self.life > 0 and self.size > 0:
      s = pg.Surface(
          (int(self.size) * 2, int(self.size) * 2), pg.SRCALPHA)
      alpha = int(255 * (self.life / 40))
      pg.draw.circle(s, (*self.color, alpha),
                     (int(self.size), int(self.size)), int(self.size))
      screen.blit(s, (int(self.x) - self.size, int(self.y) - self.size))

class Stone:
  def __init__(self, x, y, color):
    self.pos = pg.Vector2(x, y)
    self.vel = pg.Vector2(0, 0)
    self.color = color
    self.radius = STONE_RADIUS
    self.stopped = True
    self.out_of_play = False
    self.angle = 0

  def update(self, friction):
    if not self.stopped:
      self.pos += self.vel
      self.vel *= friction
      speed = self.vel.length()
      self.angle -= speed * 5
      if speed < 0.05:
        self.vel = pg.Vector2(0, 0)
        self.stopped = True

      if self.pos.x < PLAY_MIN_X + self.radius:
        self.pos.x = PLAY_MIN_X + self.radius
        self.vel.x *= -0.5
      elif self.pos.x > PLAY_MAX_X - self.radius:
        self.pos.x = PLAY_MAX_X - self.radius
        self.vel.x *= -0.5

      if self.pos.y < 0:
        self.pos.y = 0
        self.vel.y *= -0.5
      if self.pos.y > WORLD_H:
        self.stopped = True
        self.out_of_play = True

  def draw(self, screen, view_mode, camera_y=0):
    if self.out_of_play: return

    if view_mode == "3D":
      scr_pos, scale = project_3d(self.pos, camera_y)
    else:
      scr_pos, scale = project_topdown(self.pos)

    if scr_pos is None: return

    draw_radius = max(2, int(self.radius * scale *
                      (1.5 if view_mode == "3D" else 1.0)))
    if draw_radius < 2: return

    # 影の描画
    if view_mode == "3D":
      pg.draw.ellipse(screen, SHADOW_COLOR,
                      (scr_pos[0] - draw_radius + 5, scr_pos[1] - int(draw_radius * 0.4) + 5,
                       draw_radius * 2, int(draw_radius * 0.8)))
    else:
      pg.draw.circle(screen, SHADOW_COLOR,
                     (scr_pos[0] + 3, scr_pos[1] + 3), draw_radius)

    # 本体の描画
    if view_mode == "3D":
      rect_h = int(draw_radius * 0.7)
      thickness = int(12 * scale)
      pg.draw.ellipse(screen, (100, 100, 110),
                      (scr_pos[0] - draw_radius, scr_pos[1] - rect_h // 2, draw_radius * 2, rect_h))
      pg.draw.rect(screen, (130, 130, 140),
                   (scr_pos[0] - draw_radius, scr_pos[1] - rect_h // 4 - thickness, draw_radius * 2, thickness))
      top_y = scr_pos[1] - thickness
      pg.draw.ellipse(screen, GRANITE_GRAY,
                      (scr_pos[0] - draw_radius, top_y - rect_h // 2, draw_radius * 2, rect_h))
      inner_r = int(draw_radius * 0.7)
      inner_h = int(rect_h * 0.7)
      pg.draw.ellipse(screen, self.color,
                      (scr_pos[0] - inner_r, top_y - inner_h // 2, inner_r * 2, inner_h))
      pg.draw.line(screen, (40, 40, 40), (scr_pos[0], top_y),
                   (scr_pos[0], top_y - int(8 * scale)), int(4 * scale))

      hl_w = int(draw_radius * 0.4)
      hl_h = int(rect_h * 0.3)
      hl_x = scr_pos[0] - int(draw_radius * 0.4)
      hl_y = top_y - int(rect_h * 0.3)
      s_hl = pg.Surface((hl_w * 2, hl_h * 2), pg.SRCALPHA)
      pg.draw.ellipse(s_hl, (255, 255, 255, 120), (0, 0, hl_w, hl_h))
      s_hl = pg.transform.rotate(s_hl, 20)
      screen.blit(s_hl, (hl_x, hl_y))
    else:
      pg.draw.circle(screen, GRANITE_GRAY, scr_pos, draw_radius)
      pg.draw.circle(screen, WHITE, scr_pos, draw_radius, 1)
      inner_r = int(draw_radius * 0.7)
      pg.draw.circle(screen, self.color, scr_pos, inner_r)
      pg.draw.circle(screen, (255, 255, 255),
                     (scr_pos[0] - int(inner_r * 0.3), scr_pos[1] - int(inner_r * 0.3)), int(inner_r * 0.2))
      rad = math.radians(self.angle)
      dx = inner_r * 0.8 * math.cos(rad)
      dy = inner_r * 0.8 * math.sin(rad)
      pg.draw.line(screen, (50, 50, 50),
                   (scr_pos[0] - dx, scr_pos[1] - dy), (scr_pos[0] + dx, scr_pos[1] + dy), int(6 * scale))

# --- 計算・描画ヘルパー ---

def create_ice_texture(width, height):
  surface = pg.Surface((width, height), pg.SRCALPHA)
  for _ in range(30000):
    x = random.randint(0, width)
    y = random.randint(0, height)
    alpha = random.randint(50, 120)
    color = (60, 80, 110, alpha)
    r = 1 if random.random() > 0.1 else 2
    pg.draw.circle(surface, color, (x, y), r)
  return surface

def project_3d(world_pos, camera_y):
  rel_y = camera_y - world_pos.y
  if rel_y < 10: return None, 0
  if rel_y > VIEW_DIST + 2000: return None, 0
  scale = FOCAL_LENGTH / rel_y
  screen_y = HORIZON_Y + CAMERA_HEIGHT * scale
  center_x = SCREEN_W / 2
  offset_x = (world_pos.x - center_x) * scale
  screen_x = center_x + offset_x
  return (int(screen_x), int(screen_y)), scale

def project_topdown(world_pos):
  scale = 0.8
  screen_x = SCREEN_W // 2 + (world_pos.x - SCREEN_W // 2) * scale
  screen_y = SCREEN_H // 2 + (world_pos.y - TARGET_Y) * scale
  return (int(screen_x), int(screen_y)), scale

def get_score(stones):
  target = pg.Vector2(SCREEN_W // 2, TARGET_Y)
  valid = [s for s in stones if not s.out_of_play and s.pos.y < WORLD_H / 2]
  if not valid: return 0, 0
  valid.sort(key=lambda s: s.pos.distance_to(target))
  winner = valid[0].color
  pts = 0
  for s in valid:
    if s.color == winner: pts += 1
    else: break
  return (pts, 0) if winner == RED else (0, pts)

def calculate_bot_strategy(stones, difficulty):
  target = pg.Vector2(SCREEN_W // 2, TARGET_Y)
  valid = [s for s in stones if not s.out_of_play and s.pos.y < WORLD_H / 2]
  valid.sort(key=lambda s: s.pos.distance_to(target))
  tx = target.x
  if valid and difficulty >= 2 and valid[0].color == RED:
    t_obj = valid[0]
    tx = t_obj.pos.x
    dist = START_Y - t_obj.pos.y
    power = dist * (1 - FRICTION_NORMAL) * 1.6
  else:
    dist = START_Y - TARGET_Y
    power = dist * (1 - FRICTION_NORMAL) * 1.02
  noises = {1: (80, 4.0), 2: (30, 1.5), 3: (2, 0.2)}
  ax, ap = noises.get(difficulty, (30, 1.5))
  tx += random.uniform(-ax, ax)
  power += random.uniform(-ap, ap)
  return tx, min(power, POWER_MAX)

def draw_background_3d(screen):
  for y in range(HORIZON_Y):
    ratio = y / HORIZON_Y
    r = int(SKY_COLOR_TOP[0] * (1 - ratio) + SKY_COLOR_BTM[0] * ratio)
    g = int(SKY_COLOR_TOP[1] * (1 - ratio) + SKY_COLOR_BTM[1] * ratio)
    b = int(SKY_COLOR_TOP[2] * (1 - ratio) + SKY_COLOR_BTM[2] * ratio)
    pg.draw.line(screen, (r, g, b), (0, y), (SCREEN_W, y))
  pg.draw.rect(screen, FLOOR_COLOR, (0, HORIZON_Y,
               SCREEN_W, SCREEN_H - HORIZON_Y))

def draw_stage_3d(screen, camera_y, ice_texture):
  draw_background_3d(screen)
  ice_top_y = TARGET_Y - 600
  ice_btm_y = camera_y + 600
  p_tl, _ = project_3d(pg.Vector2(PLAY_MIN_X, ice_top_y), camera_y)
  p_tr, _ = project_3d(pg.Vector2(PLAY_MAX_X, ice_top_y), camera_y)
  p_bl, _ = project_3d(pg.Vector2(PLAY_MIN_X, ice_btm_y), camera_y)
  p_br, _ = project_3d(pg.Vector2(PLAY_MAX_X, ice_btm_y), camera_y)

  poly_ice = []
  if p_tl and p_tr and p_bl and p_br:
    poly_ice = [p_tl, p_tr, p_br, p_bl]
    pg.draw.polygon(screen, ICE_BASE, poly_ice)

  world_center = pg.Vector2(SCREEN_W // 2, TARGET_Y)
  center_pos, _ = project_3d(world_center, camera_y)
  if center_pos:
    radii = [(BLUE, 180), (WHITE, 120), (RED, 60), (WHITE, 15)]
    for col, r_world in radii:
      edge_pos, _ = project_3d(pg.Vector2(
          SCREEN_W // 2 + r_world, TARGET_Y), camera_y)
      if edge_pos:
        r_w = abs(edge_pos[0] - center_pos[0])
        r_h = int(r_w * 0.25)
        if r_w > 0:
          pg.draw.ellipse(
              screen, col, (center_pos[0] - r_w, center_pos[1] - r_h, r_w * 2, r_h * 2))

  lines = [TARGET_Y, SWITCH_VIEW_LINE, TARGET_Y - 300]
  for wy in lines:
    p_l, s = project_3d(pg.Vector2(PLAY_MIN_X, wy), camera_y)
    p_r, _ = project_3d(pg.Vector2(PLAY_MAX_X, wy), camera_y)
    if p_l and p_r:
      col = RED if wy != TARGET_Y else BLUE
      pg.draw.line(screen, col, p_l, p_r, max(1, int(4 * s)))

  if poly_ice:
    pebble_layer = pg.Surface((SCREEN_W, SCREEN_H), pg.SRCALPHA)
    pebble_layer.blit(ice_texture, (0, 0))
    mask_surf = pg.Surface((SCREEN_W, SCREEN_H), pg.SRCALPHA)
    mask_surf.fill((0, 0, 0, 0))
    pg.draw.polygon(mask_surf, (255, 255, 255, 255), poly_ice)
    pebble_layer.blit(mask_surf, (0, 0), special_flags=pg.BLEND_RGBA_MULT)
    screen.blit(pebble_layer, (0, 0))

  fence_step = 300
  visible_start = max(int(ice_top_y), int(camera_y - VIEW_DIST))
  visible_end = int(camera_y + 100)
  prev_l, prev_r = None, None
  for wy in range(visible_start, visible_end, fence_step):
    pl_base, s = project_3d(pg.Vector2(PLAY_MIN_X - 10, wy), camera_y)
    pr_base, _ = project_3d(pg.Vector2(PLAY_MAX_X + 10, wy), camera_y)
    if not (pl_base and pr_base): continue
    post_h = int(60 * s)
    pl_top = (pl_base[0], pl_base[1] - post_h)
    pr_top = (pr_base[0], pr_base[1] - post_h)
    if prev_l and prev_r:
      pg.draw.line(screen, FENCE_ROPE, prev_l, pl_top, max(1, int(3 * s)))
      pg.draw.line(screen, FENCE_ROPE, prev_r, pr_top, max(1, int(3 * s)))
    pg.draw.line(screen, FENCE_POST, pl_base, pl_top, max(2, int(8 * s)))
    pg.draw.line(screen, FENCE_POST, pr_base, pr_top, max(2, int(8 * s)))
    prev_l, prev_r = pl_top, pr_top

def draw_stage_topdown(screen, ice_texture):
  screen.fill(ICE_BASE)
  screen.blit(ice_texture, (0, 0))
  pg.draw.line(screen, (200, 200, 220), (SCREEN_W // 2, 0),
               (SCREEN_W // 2, SCREEN_H), 2)
  center_scr = (SCREEN_W // 2, SCREEN_H // 2)
  scale = 0.8
  radii = [(BLUE, 180), (WHITE, 120), (RED, 60), (WHITE, 15)]
  for col, r_world in radii:
    pg.draw.circle(screen, col, center_scr, int(r_world * scale))
    pg.draw.circle(screen, (200, 200, 200),
                   center_scr, int(r_world * scale), 1)

  s_overlay = pg.Surface((SCREEN_W, SCREEN_H), pg.SRCALPHA)
  s_overlay.fill((255, 255, 255, 40))
  screen.blit(s_overlay, (0, 0))
  lines = [TARGET_Y, SWITCH_VIEW_LINE, TARGET_Y - 300]
  for wy in lines:
    _, sy = project_topdown(pg.Vector2(0, wy))
    col = RED if wy != TARGET_Y else BLUE
    pg.draw.line(screen, col, (0, sy), (SCREEN_W, sy), 3)

def draw_hammer_icon(screen, x, y, color):
  pg.draw.rect(screen, color, (x - 2, y - 5, 4, 24))
  pg.draw.rect(screen, color, (x - 10, y - 5, 20, 10))

def draw_enhanced_ui(screen, score_r, score_y, end_num, stones, current_stone, hammer_team):
  cx, cy = SCREEN_W // 2, 50
  board_w, board_h = 360, 60

  rect = pg.Rect(cx - board_w // 2, cy - board_h // 2, board_w, board_h)
  pg.draw.rect(screen, (60, 60, 70), rect, border_radius=30)
  pg.draw.rect(screen, (200, 200, 200), rect, 2, border_radius=30)

  # フォントの使い分け
  font_jp = get_jp_font(30)
  font_score = pg.font.SysFont("arial", 45, bold=True)

  # エンド表示
  t_end = font_jp.render(
      f"第 {min(end_num, MAX_ENDS)} エンド", True, (220, 220, 220))
  screen.blit(t_end, t_end.get_rect(center=(cx, cy)))

  # 赤チームスコア
  pg.draw.circle(screen, RED, (cx - 130, cy), 24)
  t_r = font_score.render(str(score_r), True, BLACK)
  screen.blit(t_r, t_r.get_rect(center=(cx - 130, cy)))

  # 黄チームスコア
  pg.draw.circle(screen, YELLOW, (cx + 130, cy), 24)
  t_y = font_score.render(str(score_y), True, BLACK)
  screen.blit(t_y, t_y.get_rect(center=(cx + 130, cy)))

  # ハンマー（後攻）アイコン
  hammer_col = (200, 200, 200)
  if hammer_team == RED: draw_hammer_icon(screen, cx - 180, cy, hammer_col)
  else: draw_hammer_icon(screen, cx + 180, cy, hammer_col)

  # 残りストーン表示
  used_r = len([s for s in stones if s.color == RED])
  used_y = len([s for s in stones if s.color == YELLOW])
  if current_stone:
    if current_stone.color == RED: used_r += 1
    else: used_y += 1

  rem_r = max(0, STONES_PER_TEAM - used_r)
  rem_y = max(0, STONES_PER_TEAM - used_y)

  start_x_r = cx - 160
  stone_y = cy + 45
  for i in range(rem_r):
    pg.draw.circle(screen, (200, 60, 60), (start_x_r + i * 25, stone_y), 7)
    pg.draw.circle(screen, (255, 255, 255),
                   (start_x_r + i * 25, stone_y), 8, 1)

  start_x_y = cx + 160
  for i in range(rem_y):
    pos_x = start_x_y - i * 25
    pg.draw.circle(screen, (220, 220, 60), (pos_x, stone_y), 7)
    pg.draw.circle(screen, (50, 50, 50), (pos_x, stone_y), 8, 1)

def draw_broom(screen, x, y, is_active):
  shake_x = 0
  if is_active: shake_x = int(math.sin(pg.time.get_ticks() * 0.05) * 15)
  pg.draw.line(screen, (200, 200, 50), (x + shake_x, y),
               (x + shake_x + 30, y - 80), 8)
  head_rect = pg.Rect(x + shake_x - 25, y - 10, 50, 20)
  pg.draw.rect(screen, (50, 50, 50), head_rect, border_radius=5)
  pg.draw.rect(screen, (200, 50, 50),
               head_rect.inflate(-4, -4), border_radius=3)

def draw_cutin(screen, text, sub_text, color, progress):
  alpha = 255
  offset_x = 0

  if progress < 0.2:
    t = progress / 0.2
    offset_x = SCREEN_W * (1 - t * t)
  elif progress > 0.8:
    t = (progress - 0.8) / 0.2
    offset_x = -SCREEN_W * (t * t)

  rect_h = 160
  rect_y = SCREEN_H // 2 - rect_h // 2

  s_shadow = pg.Surface((SCREEN_W, rect_h), pg.SRCALPHA)
  s_shadow.fill((0, 0, 0, 100))
  screen.blit(s_shadow, (0, rect_y + 10))

  poly_pts = [
      (offset_x - 50, rect_y),
      (offset_x + SCREEN_W + 50, rect_y),
      (offset_x + SCREEN_W + 20, rect_y + rect_h),
      (offset_x - 20, rect_y + rect_h)
  ]
  pg.draw.polygon(screen, color, poly_pts)
  pg.draw.polygon(screen, WHITE, poly_pts, 3)

  # 背景色に合わせて文字色を自動で見やすく調整
  text_color = BLACK if color == YELLOW else WHITE

  font_l = get_jp_font(70)
  font_s = get_jp_font(36)

  txt_surf = font_l.render(text, True, text_color)
  txt_rect = txt_surf.get_rect(
      center=(SCREEN_W // 2 + offset_x, SCREEN_H // 2 - 20))

  # 白文字の時だけ影をつける
  if text_color == WHITE:
    txt_shadow = font_l.render(text, True, (0, 0, 0))
    screen.blit(txt_shadow, (txt_rect.x + 4, txt_rect.y + 4))

  screen.blit(txt_surf, txt_rect)

  if sub_text:
    sub_surf = font_s.render(sub_text, True, text_color)
    sub_rect = sub_surf.get_rect(
        center=(SCREEN_W // 2 + offset_x, SCREEN_H // 2 + 40))
    screen.blit(sub_surf, sub_rect)

def main():
  pg.init()
  screen = pg.display.set_mode((SCREEN_W, SCREEN_H))
  pg.display.set_caption("Curling 3D")
  clock = pg.time.Clock()
  pg.mouse.set_visible(False)

  ice_texture = create_ice_texture(SCREEN_W, SCREEN_H)

  difficulty = 2
  game_state = "START_MENU"
  view_mode = "3D"

  stones = []
  thrown_count = 0
  turn = 0
  current_end = 1
  scores = [0, 0]
  current_stone = None
  charge = 0
  charge_dir = 1
  is_charging = False

  hammer_team = YELLOW

  camera_y = START_Y + 500
  bot_target_x = 0
  bot_power = 0
  bot_stage = 0

  sweep_particles = []

  # --- カットイン用変数 ---
  cutin_timer = 0
  cutin_duration = 120
  cutin_text = ""
  cutin_sub = ""
  cutin_color = RED
  cutin_next_state = ""
  cutin_cam_start = 0

  def start_cutin(text, sub, color, next_state):
    nonlocal game_state, cutin_timer, cutin_text, cutin_sub, cutin_color, cutin_next_state, cutin_cam_start
    game_state = "CUT_IN"
    cutin_timer = 0
    cutin_text = text
    cutin_sub = sub
    cutin_color = color
    cutin_next_state = next_state
    cutin_cam_start = camera_y

  running = True
  while running:
    is_sweeping = False
    mx, my = pg.mouse.get_pos()

    for event in pg.event.get():
      if event.type == pg.QUIT: running = False
      if game_state == "START_MENU":
        if event.type == pg.KEYDOWN:
          if event.key == pg.K_1: difficulty = 1; game_state = "RESET"
          if event.key == pg.K_2: difficulty = 2; game_state = "RESET"
          if event.key == pg.K_3: difficulty = 3; game_state = "RESET"
      if game_state == "AIMING" and turn == 0:
        if current_stone:
          if event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
            is_charging = True; charge = 0; charge_dir = 1
          if event.type == pg.KEYUP and event.key == pg.K_SPACE:
            is_charging = False; current_stone.vel = pg.Vector2(
                0, -charge); current_stone.stopped = False; game_state = "MOVING"; thrown_count += 1

    if game_state == "MOVING" and turn == 0:
      if pg.mouse.get_pressed()[0]:
        is_sweeping = True
        for _ in range(3):
          shake = math.sin(pg.time.get_ticks() * 0.05) * 15
          sweep_particles.append(SweepParticle(mx + shake, my))

    # --- 状態遷移ロジック ---
    if game_state == "RESET":
      stones = []; thrown_count = 0; turn = 0
      starter = RED if hammer_team == YELLOW else YELLOW
      turn = 0 if starter == RED else 1
      current_stone = None

      col = RED if starter == RED else YELLOW
      txt = "赤チーム スタート" if starter == RED else "黄チーム スタート"
      start_cutin(f"第 {current_end} エンド", txt, col, "AIMING")

    elif game_state == "CUT_IN":
      cutin_timer += 1
      target_cam = START_Y + 500
      t = cutin_timer / cutin_duration
      camera_y = cutin_cam_start * (1 - t) + target_cam * t

      if cutin_timer >= cutin_duration:
        game_state = cutin_next_state
        view_mode = "3D"
        if game_state == "AIMING":
          current_stone = Stone(
              SCREEN_W // 2, START_Y, RED if turn == 0 else YELLOW)
          charge = 0
          bot_stage = 0

    elif game_state == "AIMING":
      target_cam = START_Y + 600
      camera_y += (target_cam - camera_y) * 0.1
      view_mode = "3D"
      if current_stone:
        if turn == 0:
          keys = pg.key.get_pressed()
          if keys[pg.K_LEFT]: current_stone.pos.x -= 4
          if keys[pg.K_RIGHT]: current_stone.pos.x += 4
          if is_charging:
            charge += 0.5 * charge_dir
            if charge >= POWER_MAX: charge, charge_dir = POWER_MAX, -1
            elif charge <= 0: charge, charge_dir = 0, 1
        else:
          if bot_stage == 0: bot_target_x, bot_power = calculate_bot_strategy(
              stones, difficulty); bot_stage = 1
          elif bot_stage == 1:
            dx = bot_target_x - current_stone.pos.x
            if abs(dx) > 4: current_stone.pos.x += 4 if dx > 0 else -4
            else: bot_stage = 2
          elif bot_stage == 2:
            charge += 0.5
            if charge >= bot_power: current_stone.vel = pg.Vector2(
                0, -charge); current_stone.stopped = False; game_state = "MOVING"; thrown_count += 1; bot_stage = 0; charge = 0
        current_stone.pos.x = max(
            PLAY_MIN_X + STONE_RADIUS, min(PLAY_MAX_X - STONE_RADIUS, current_stone.pos.x))

    elif game_state == "MOVING":
      if current_stone: current_stone.update(FRICTION_SWEEP if (
          is_sweeping and turn == 0) else FRICTION_NORMAL)
      for s in stones: s.update(FRICTION_NORMAL)

      target_stone = current_stone if current_stone else (
          stones[-1] if stones else None)
      if target_stone and target_stone.pos.y < SWITCH_VIEW_LINE: view_mode = "TOPDOWN"
      else:
        view_mode = "3D"
        stone_y = target_stone.pos.y if target_stone else START_Y
        target_cam = max(
            min(stone_y + 700, START_Y + 600), TARGET_Y + 700)
        camera_y += (target_cam - camera_y) * 0.1

      all_stones = stones[:]
      if current_stone: all_stones.append(current_stone)
      for i in range(len(all_stones)):
        for j in range(i + 1, len(all_stones)):
          s1 = all_stones[i]; s2 = all_stones[j]
          if s1.out_of_play or s2.out_of_play: continue
          dist_vec = s1.pos - s2.pos; dist = dist_vec.length()
          if dist < STONE_RADIUS * 2:
            if dist == 0: dist_vec = pg.Vector2(1, 0); dist = 1
            overlap = (STONE_RADIUS * 2) - \
                dist; normal = dist_vec.normalize()
            s1.pos += normal * \
                (overlap * 0.5); s2.pos -= normal * (overlap * 0.5)
            rel_vel = s1.vel - \
                s2.vel; vel_along_normal = rel_vel.dot(normal)
            if vel_along_normal < 0:
              impulse = normal * (-(1.9) * vel_along_normal / 2)
              s1.vel += impulse; s2.vel -= impulse; s1.stopped = False; s2.stopped = False

      if all(s.stopped for s in all_stones):
        if current_stone: stones.append(current_stone)
        current_stone = None

        if thrown_count >= STONES_PER_END:
          game_state = "RESULT"
        else:
          turn = 1 - turn
          next_col = RED if turn == 0 else YELLOW
          next_txt = "RED TEAM" if turn == 0 else "YELLOW TEAM"
          sub_txt = f"投球数 {thrown_count + 1} / {STONES_PER_END}"
          start_cutin(next_txt, sub_txt, next_col, "AIMING")

    elif game_state == "RESULT":
      view_mode = "TOPDOWN"
      pg.time.delay(10)
      if pg.time.get_ticks() % 100 == 0:
        pts_r, pts_y = get_score(stones)
        scores[0] += pts_r; scores[1] += pts_y
        if pts_r > 0: hammer_team = YELLOW
        elif pts_y > 0: hammer_team = RED

        current_end += 1
        if current_end > MAX_ENDS:
          game_state = "GAME_OVER"
        else:
          start_cutin(
              "エンド終了", f"赤:{pts_r} - 黄:{pts_y}", BLUE, "RESET")

        pg.time.delay(1000)

    # --- 描画処理 ---
    if view_mode == "3D":
      draw_stage_3d(screen, camera_y, ice_texture)
    else:
      draw_stage_topdown(screen, ice_texture)

    draw_list = stones[:]
    if current_stone: draw_list.append(current_stone)
    draw_list.sort(key=lambda s: s.pos.y)
    for s in draw_list:
      s.draw(screen, view_mode, camera_y)

    for p in sweep_particles[:]:
      p.update()
      p.draw(screen)
      if p.life <= 0: sweep_particles.remove(p)

    if game_state == "START_MENU":
      pg.mouse.set_visible(True)
      screen.fill((200, 210, 230))

      title_font = get_jp_font(100)
      t = title_font.render("3D PRO", True, RED)
      t2 = title_font.render("CURLINGER", True, BLUE)
      screen.blit(t, (SCREEN_W // 2 - t.get_width() // 2, 200))
      screen.blit(t2, (SCREEN_W // 2 - t2.get_width() // 2, 280))

      menu_font = get_jp_font(36)
      m = menu_font.render(
          "[1] easy   [2] normal   [3] hard", True, (50, 50, 70))
      screen.blit(m, (SCREEN_W // 2 - m.get_width() // 2, 500))

    elif game_state == "GAME_OVER":
      pg.mouse.set_visible(True)
      s_overlay = pg.Surface((SCREEN_W, SCREEN_H), pg.SRCALPHA)
      s_overlay.fill((255, 255, 255, 180))
      screen.blit(s_overlay, (0, 0))

      res_font = get_jp_font(80)
      res = "WIN!!" if scores[0] > scores[1] else "LOSE..."
      col = RED if scores[0] > scores[1] else BLUE
      t = res_font.render(res, True, col)
      screen.blit(t, (SCREEN_W // 2 - t.get_width() // 2, 300))

      score_font = get_jp_font(40)
      score_txt = score_font.render(
          f"赤: {scores[0]}  -  黄: {scores[1]}", True, (50, 50, 50))
      screen.blit(score_txt, (SCREEN_W // 2 -
                  score_txt.get_width() // 2, 400))

      if pg.key.get_pressed()[pg.K_SPACE]: running = False
    else:
      draw_enhanced_ui(
          screen, scores[0], scores[1], current_end, stones, current_stone, hammer_team)

      if game_state == "AIMING" and current_stone and view_mode == "3D":
        pos, scale = project_3d(current_stone.pos, camera_y)
        if pos:
          bar_w = int(100 * scale)
          bar_h = int(15 * scale)
          pg.draw.rect(
              screen, BLACK, (pos[0] - bar_w // 2, pos[1] + int(40 * scale), bar_w, bar_h), 2)
          fill_w = int(bar_w * (charge / POWER_MAX))
          color = (int(255 * charge / POWER_MAX),
                   int(255 * (1 - charge / POWER_MAX)), 0)
          pg.draw.rect(
              screen, color, (pos[0] - bar_w // 2 + 2, pos[1] + int(40 * scale) + 2, fill_w - 4, bar_h - 4))

      if game_state == "CUT_IN":
        draw_cutin(screen, cutin_text, cutin_sub,
                   cutin_color, cutin_timer / cutin_duration)

      show_brush = (game_state == "MOVING" and turn == 0) or (
          game_state == "AIMING" and turn == 0)
      if show_brush and game_state != "CUT_IN":
        draw_broom(screen, mx, my, is_sweeping)
        pg.mouse.set_visible(False)
      else:
        pg.mouse.set_visible(True)

      if is_sweeping and game_state == "MOVING":
        sweep_font = get_jp_font(80)
        msg = sweep_font.render("SWEEP!!!", True, (255, 50, 50))
        txt_shake = random.randint(-2, 2)
        screen.blit(msg, (SCREEN_W // 2 - msg.get_width() //
                    2 + txt_shake, SCREEN_H - 150 + txt_shake))

    pg.display.update()
    clock.tick(60)
  pg.quit()

if __name__ == "__main__":
  main()
