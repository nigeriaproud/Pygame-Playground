import pygame as pg

def main():

  # 初期化処理
  pg.init()
  pg.display.set_caption('ぼくのかんがえたさいきょうのげーむ')
  disp_w, disp_h = 800, 600
  screen = pg.display.set_mode((disp_w, disp_h))  # WindowSize
  clock = pg.time.Clock()
  font = pg.font.Font(None, 15)
  frame = 0
  exit_flag = False
  exit_code = '000'

  ball_p = pg.Vector2(50, 90)  # x=50, y=90 (px)
  ball_v = pg.Vector2(2, 0)   # vx=2, vy=0 (px/frm)
  ball_a = pg.Vector2(0, 0.9)  # ax=0, ay=0.9 (px/frm^2)
  ball_r = 24  # ボールの半径
  ball_c = pg.Color('#ff0000')

  ground_img = pg.image.load(f'data/img/map-ground-center.png')
  ground_s = pg.Vector2(48, 48)  # 地面画像サイズ

  jump = False

  # ゲームループ
  while not exit_flag:

    # システムイベントの検出
    for event in pg.event.get():
      if event.type == pg.QUIT:  # ウィンドウ[X]の押下
        exit_flag = True
        exit_code = '001'
      if event.type == pg.KEYDOWN:
        # スペースキーが押下されたら jump を True に
        if event.key == pg.K_SPACE:
          jump = True

    # 背景描画
    screen.fill(pg.Color('WHITE'))

    # ボールの描画と位置計算
    pg.draw.circle(screen, ball_c, ball_p, ball_r, width=2)
    if jump:
      pg.draw.circle(screen, ball_c, ball_p, ball_r)
      ball_v.y = -8
      ball_v.x += 0.5 if ball_v.x > 0 else -0.5
      jump = False
    ball_p += ball_v
    ball_v += ball_a

    # 地面との衝突処理
    if ball_p.y >= disp_h - ground_s.y - ball_r:
      ball_p.y = disp_h - ground_s.y - ball_r
      ball_v.y = - 0.7 * (ball_v.y - ball_a.y)
      if abs(ball_v.y) < 3.5:
        ball_v.y = 0
        ball_v.x *= 0.98

    # 右端と左端との衝突
    if ball_p.x + ball_r > disp_w:
      ball_p.x = disp_w - ball_r
      ball_v.x = -0.8 * ball_v.x
    elif ball_p.x - ball_r < 0:
      ball_p.x = ball_r
      ball_v.x = -0.8 * ball_v.x

    # 地面描画
    for x in range(0, disp_w, int(ground_s.x)):
      screen.blit(ground_img, (x, disp_h - ground_s.y))

    # フレームカウンタの描画
    frame += 1
    frm_str = f'{frame:05}'
    screen.blit(font.render(frm_str, True, 'BLACK'), (10, 10))

    # 画面の更新と同期
    pg.display.update()
    clock.tick(30)  # 最高速度を 30 フレーム/秒に制限

  # ゲームループ [ここまで]
  pg.quit()
  return exit_code

if __name__ == "__main__":
  code = main()
  print(f'プログラムを「コード{code}」で終了しました。')
