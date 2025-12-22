import pygame as pg
import math

# --- 定数設定 ---
# 縦長画面に変更
SCREEN_W, SCREEN_H = 600, 800
STONE_RADIUS = 20
FRICTION = 0.99   # 摩擦係数（少し滑りやすく調整）
POWER_MAX = 25    # 最大パワー

# 色の定義
WHITE = (255, 255, 255)
RED = (200, 50, 50)
YELLOW = (200, 200, 50)
BLUE = (50, 50, 200)
GRAY = (200, 200, 200)
ICE_COLOR = (230, 240, 255)  # 氷っぽい背景色

class Stone:
  def __init__(self, x, y, color):
    self.pos = pg.Vector2(x, y)
    self.vel = pg.Vector2(0, 0)
    self.color = color
    self.radius = STONE_RADIUS
    self.stopped = True

  def update(self):
    if not self.stopped:
      self.pos += self.vel
      self.vel *= FRICTION  # 減速処理

      # 速度が十分小さくなったら停止
      if self.vel.length() < 0.1:
        self.vel = pg.Vector2(0, 0)
        self.stopped = True

    # --- 壁との衝突判定（左右の壁） ---
    # 上から下へ投げるので、X座標が左右の壁を超えたら反射させる
    if self.pos.x < self.radius:
      self.pos.x = self.radius
      self.vel.x *= -0.8  # 壁反射
    elif self.pos.x > SCREEN_W - self.radius:
      self.pos.x = SCREEN_W - self.radius
      self.vel.x *= -0.8  # 壁反射

  def draw(self, screen):
    # 影
    pg.draw.circle(screen, (50, 50, 50, 100), (int(
        self.pos.x) + 2, int(self.pos.y) + 2), self.radius)
    # 本体
    pg.draw.circle(screen, self.color, (int(
        self.pos.x), int(self.pos.y)), self.radius)
    # 立体感を出すハイライト
    pg.draw.circle(screen, (255, 255, 255), (int(
        self.pos.x) - 5, int(self.pos.y) - 5), 5)

def main():
  pg.init()
  screen = pg.display.set_mode((SCREEN_W, SCREEN_H))
  pg.display.set_caption("Vertical Curling Game")
  clock = pg.time.Clock()
  font = pg.font.Font(None, 28)

  stones = []
  turn = 0

  # チャージ関連の変数
  charge_power = 0
  charge_dir = 1      # 1: 増加, -1: 減少
  is_charging = False

  game_state = "AIMING"

  # 初期配置（画面上部中央）
  current_stone = Stone(SCREEN_W // 2, 80, RED)

  exit_flag = False
  while not exit_flag:
    for event in pg.event.get():
      if event.type == pg.QUIT:
        exit_flag = True

      # --- スペースキー操作 ---
      if event.type == pg.KEYDOWN:
        if event.key == pg.K_SPACE and game_state == "AIMING":
          is_charging = True
          charge_power = 0     # 0からスタート
          charge_dir = 1       # 増える方向でスタート

      if event.type == pg.KEYUP:
        if event.key == pg.K_SPACE and game_state == "AIMING":
          # 発射！
          is_charging = False
          # ベクトル設定：X=0, Y=パワー（下向き）
          current_stone.vel = pg.Vector2(0, charge_power)
          current_stone.stopped = False
          game_state = "MOVING"

    # --- 更新処理 ---

    if game_state == "AIMING":
      # 左右キーで位置調整（X座標を動かす）
      keys = pg.key.get_pressed()
      if keys[pg.K_LEFT]:
        current_stone.pos.x -= 3
      if keys[pg.K_RIGHT]:
        current_stone.pos.x += 3

      # 画面外に出ないように制限
      if current_stone.pos.x < STONE_RADIUS: current_stone.pos.x = STONE_RADIUS
      if current_stone.pos.x > SCREEN_W - \
          STONE_RADIUS: current_stone.pos.x = SCREEN_W - STONE_RADIUS

      # === パワーゲージの往復ロジック ===
      if is_charging:
        charge_power += 0.5 * charge_dir  # 方向に応じて増減

        # 最大値または0で反転
        if charge_power >= POWER_MAX:
          charge_power = POWER_MAX
          charge_dir = -1  # 下がり始める
        elif charge_power <= 0:
          charge_power = 0
          charge_dir = 1  # 上がり始める

    elif game_state == "MOVING":
      all_stopped = True
      current_stone.update()
      if not current_stone.stopped: all_stopped = False

      for s in stones:
        s.update()
        if not s.stopped: all_stopped = False

      # 衝突判定（第22回講義のベクトルの応用）
      for s in stones:
        dist_vec = current_stone.pos - s.pos
        dist = dist_vec.length()
        if dist < STONE_RADIUS * 2:
          if dist == 0: dist = 0.1
          normal = dist_vec.normalize()
          overlap = (STONE_RADIUS * 2) - dist

          # 位置補正（めり込み防止）
          current_stone.pos += normal * overlap * 0.5
          s.pos -= normal * overlap * 0.5

          # 速度交換（弾く）
          v1 = current_stone.vel
          v2 = s.vel
          current_stone.vel = v2 + v1 * 0.5
          s.vel = v1 * 0.8
          s.stopped = False

      if all_stopped and current_stone.stopped:
        stones.append(current_stone)
        turn = 1 - turn
        next_color = RED if turn == 0 else YELLOW
        current_stone = Stone(SCREEN_W // 2, 80, next_color)
        game_state = "AIMING"
        charge_power = 0

    # --- 描画処理 ---
    screen.fill(ICE_COLOR)

    # ハウス（標的）を画面下部に描画
    target_center = (SCREEN_W // 2, SCREEN_H - 150)
    pg.draw.circle(screen, BLUE, target_center, 100)
    pg.draw.circle(screen, WHITE, target_center, 70)
    pg.draw.circle(screen, RED, target_center, 40)
    pg.draw.circle(screen, WHITE, target_center, 10)

    # ストーン描画
    for s in stones:
      s.draw(screen)
    current_stone.draw(screen)

    # UI描画
    if game_state == "AIMING":
      # パワーゲージ（横に配置）
      bar_w = 200
      bar_h = 20
      bar_x = (SCREEN_W - bar_w) // 2
      bar_y = 40

      # 枠
      pg.draw.rect(screen, GRAY, (bar_x, bar_y, bar_w, bar_h))
      # ゲージ本体（現在のパワー / MAXパワー の割合で幅を決める）
      fill_w = (charge_power / POWER_MAX) * bar_w

      # 色の変化（パワーが強いと赤くなる演出）
      gauge_color = (int(255 * (charge_power / POWER_MAX)),
                     200 - int(200 * (charge_power / POWER_MAX)), 0)
      pg.draw.rect(screen, gauge_color, (bar_x, bar_y, fill_w, bar_h))

      msg = f"Turn: {'RED' if turn == 0 else 'YELLOW'} (Left/Right: Move, SPACE: Charge)"
      screen.blit(font.render(msg, True, (0, 0, 0)), (20, 10))
    else:
      screen.blit(font.render("Moving...", True, (0, 0, 0)), (20, 10))

    pg.display.update()
    clock.tick(60)

  pg.quit()

if __name__ == "__main__":
  main()
