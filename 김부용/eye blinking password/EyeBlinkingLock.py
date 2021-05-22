import os
import pygame as pg
from time import sleep
import cv2
from settings import *
from sprites import *
from keras.models import load_model
from silence_tensorflow import silence_tensorflow
from utils import VideoStream
vec = pg.math.Vector2

class Game:
    def __init__(self):
        # initialize game window, etc
        pg.init()
        pg.mixer.init()
        self.screen = pg.display.set_mode((WIDTH, HEIGHT)) # 창 크기
        pg.display.set_caption(TITLE)
        pg.display.set_icon(pg.image.load('images/icon.png'))      #set icon

        self.blink_event = pg.event.Event(pg.USEREVENT)
        
        self.load_data()

        self.clock = pg.time.Clock()
        self.start_tick = 0
        self.game_tick = 0

        self.blink_index = 0
        self.blink_sign = list()
        self.blink_action = 0

        self.playing = False
        self.start = True
        self.practice = True
    
    def new(self):
        # start a new game
        self.clear = False
        self.ending = False

        self.hit_count = 0
        self.blink_data = list()     # data list
        self.blink_dataLen = 0       # data len
        
        self.vs = VideoStream(self, device=0, model=self.CNN).start()

        self.all_sprites = pg.sprite.Group()
        self.blinks = pg.sprite.Group() # 깜빡임 지시자 sprite 그룹 생성
        
        pg.mixer.music.load(os.path.join(self.snd_dir, METRONOME)) #배경음 로드
        
        self.run()

    def run(self):
        
        self.ready_sound.play()
        self.start_tick = pg.time.get_ticks()
        self.load_blinkData()
        #game loop
        pg.mixer.music.play(loops=-1) #배경음 플레이 (loops 값 false = 반복, true = 한번)

        self.playing = True
        while self.playing:
            self.clock.tick(FPS)
            self.update()
            self.draw()
            self.events()
                
        pg.mixer.music.fadeout(500) #배경음이 갑자기 꺼지지 않고 점점 꺼지게 함

    def update(self):
        #game loop - update
        self.all_sprites.update()
        self.game_tick = pg.time.get_ticks() - self.start_tick

        # 끝
        if self.ending == True:
            self.playing = False
            if self.hit_count == self.blink_dataLen -1: #잠금 해제
                self.clear_text()
                sleep(0.5)
                self.clear = True

    def clear_text(self):
        for i in range(8):
            self.draw_text('!!패턴 일치!!', 60, BLUE, WIDTH/2, HEIGHT/2-100)
            pg.display.update()
            sleep(0.1)
            self.draw_text('!!패턴 일치!!', 60, GRAY, WIDTH/2, HEIGHT/2-100)
            pg.display.update()
            sleep(0.1)

    def events(self):
        #game loop - events
        for event in pg.event.get():
            if event.type == pg.USEREVENT:
                if self.blink_action < self.blink_dataLen-1:
                    position_of_bar =  self.blink_sign[self.blink_action].rect.x
                    print(position_of_bar)
                    if position_of_bar >= (WIDTH/2-15) and position_of_bar <= (WIDTH/2+15):
                        self.hit_count += 1
                        print('hit!')
                        self.blink_sign[self.blink_action].correct = 1
                    self.blink_action += 1
                    if self.hit_count == self.blink_dataLen-1:
                        self.ending = True

            elif event.type == pg.QUIT:
                if self.playing:
                    self.playing = False
                    self.start = False
                self.start = False

    # 데이터를 불러오는 함수
    def load_data(self):
        self.dir = os.path.dirname(__file__)

        #model
        silence_tensorflow()
        self.CNN = load_model('models/'+MODEL_VER)
        
        #image
        self.img_dir = os.path.join(self.dir, 'images')
        self.bg_img = pg.image.load(os.path.join(self.img_dir, 'main.png'))
        self.team_img1 = pg.image.load(os.path.join(self.img_dir, 'team1.jpg'))
        self.team_img2 = pg.image.load(os.path.join(self.img_dir, 'team2.jpg'))
        self.end_img = pg.image.load(os.path.join(self.img_dir, 'ending.png'))
        self.menu_select = pg.image.load(os.path.join(self.img_dir, 'menu_select.png'))

        self.font_name = pg.font.match_font(FONT_NAME) #FONT_NMAE과 맞는 폰트를 검색
        self.fnt_dir = os.path.join(self.dir, 'font')
        self.gg_font = os.path.join(self.fnt_dir, GG)

        #sound(효과음)
        self.snd_dir = os.path.join(self.dir, 'sound')
        self.key_sound = pg.mixer.Sound(os.path.join(self.snd_dir, KEY))
        self.decision_sound = pg.mixer.Sound(os.path.join(self.snd_dir, DECISION))
        self.fail_sound = pg.mixer.Sound(os.path.join(self.snd_dir, FAIL))
        self.good_sound = pg.mixer.Sound(os.path.join(self.snd_dir, APPLAUSE))
        self.success_sound = pg.mixer.Sound(os.path.join(self.snd_dir, SUCCESS))
        self.exit_sound = pg.mixer.Sound(os.path.join(self.snd_dir, EXIT))
        self.blink_sound = pg.mixer.Sound(os.path.join(self.snd_dir, BLINK))
        self.count_sound = pg.mixer.Sound(os.path.join(self.snd_dir, COUNT))
        self.ready_sound = pg.mixer.Sound(os.path.join(self.snd_dir, READY))
        
    def load_blinkData(self):
        with open(PATTERN_DATA_PATH, "r", encoding = 'UTF-8') as data_file:
            data_lines = data_file.read().split('\n')
            
        for data_line in data_lines:
            if data_line[0] == '0':
                time_list = data_line.split(':')
                
            elif data_line[0] == 'E':
                last_line = data_line.split('-')
                time_list = last_line[1].split(':')

            timing = int(time_list[0]) * 60000 + int(time_list[1]) * 1000 + int(time_list[2]) * 10
            self.blink_data.append(timing)

        self.blink_dataLen = len(self.blink_data)

    def draw(self):
        #game loop - draw
        frame = self.vs.read()
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
        frame = cv2.flip(frame, flipCode=0)
        frame = pg.surfarray.make_surface(frame)
        self.screen.blit(frame, (0,0))
        if self.practice == True:
            pg.draw.circle(self.screen, YELLOW, (WIDTH/2, HEIGHT/2), WIDTH*0.01)
            self.draw_text("PRACTICE MODE", 15, BLACK, WIDTH/2, HEIGHT/5 - 20, WHITE)
            self.draw_text("막대가 화면의 중앙에 올 때 눈을 깜빡여주세요.", 22, BLACK, WIDTH/2, HEIGHT/5)
        else:
            self.draw_text("PRACTICAL MODE", 15, BLACK, WIDTH/2, HEIGHT/5 - 20, WHITE)
            self.draw_text("잠금 해제 중...", 22, BLACK, WIDTH/2, HEIGHT/5)
        if self.game_tick >= self.blink_data[-1]:
            self.ending = True
        else:
            self.create_blink()
            self.all_sprites.draw(self.screen)
        pg.display.update()

###-------- start_screen 부분

    def start_new(self):
        self.start_group = pg.sprite.Group()
        self.select = Select(self)
        self.start_group.add(self.select)
        self.start_run()

    def start_run(self):
        #start loop
        pg.mixer.music.load(os.path.join(self.snd_dir, MAIN))
        pg.mixer.music.play(loops=-1)
        self.start_playing = True
        while self.start_playing:
            self.clock.tick(FPS)
            self.start_events()
            self.start_update()
            self.start_draw()
        pg.mixer.music.fadeout(200)

    def start_events(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                if self.start_playing:
                    self.start_playing = False
                self.start = False

    def start_update(self):
        self.start_group.update()

    def start_draw(self):
        self.screen.blit(self.bg_img, (0,0))
        self.start_group.draw(self.screen)

        self.draw_text("눈 깜빡임 패턴으로 잠금 해제하기", 22, WHITE, WIDTH/2, HEIGHT/2 + 25, BLACK)
        if self.select.select_number == 0:
            self.draw_text('연습', 46, WHITE, 200, 320)
            self.draw_text('실전', 36, BLACK, 320, 320)
            self.draw_text('EXIT', 36, BLACK, 440, 320)
        elif self.select.select_number == 1:
            self.draw_text('연습', 36, BLACK, 200, 320)
            self.draw_text('실전', 46, WHITE, 320, 320)
            self.draw_text('EXIT', 36, BLACK, 440, 320)
        elif self.select.select_number == 2:
            self.draw_text('연습', 36, BLACK, 200, 320)
            self.draw_text('실전', 36, BLACK, 320, 320)
            self.draw_text('EXIT', 46, WHITE, 440, 320)
        pg.display.update()

    def create_blink(self):
        if self.blink_index <= self.blink_dataLen-1 and self.game_tick >= self.blink_data[self.blink_index]:    
            obj_b = Blink(self)
            self.blink_sign.append(obj_b)
            self.all_sprites.add(obj_b)
            self.blinks.add(obj_b)
            
            self.blink_index += 1

###---------------end

    def fail_screen(self):
        # fail 시에 나타낼 스크린
        self.background = pg.Surface((WIDTH, HEIGHT))           # 검은 배경
        self.background = self.background.convert()
        self.background.fill(BLACK)
        self.screen.blit(self.background, (0,0))
        self.fail_sound.play()
        self.draw_text("잠금을 해제하지 못했습니다.", 48, WHITE, WIDTH/2, HEIGHT/3)
        self.draw_text("'Z':main screen, 'ESC':QUIT", 22, WHITE, WIDTH/2, HEIGHT*2/3)
        pg.display.update()
        pg.mixer.music.load(os.path.join(self.snd_dir, WAITING))
        pg.mixer.music.play(loops=-1)
        self.wait_for_key()
        pg.mixer.music.fadeout(200)
    
    def good_screen(self):
        # 연습 성공 시에 나타낼 스크린
        self.background = pg.Surface((WIDTH, HEIGHT))           # 검은 배경
        self.background = self.background.convert()
        self.background.fill(BLACK)
        self.screen.blit(self.background, (0,0))
        self.good_sound.play()
        self.draw_text("참 잘했어요.", 48, WHITE, WIDTH/2, HEIGHT/3)
        self.draw_text("'Z':main screen, 'ESC':QUIT", 22, WHITE, WIDTH/2, HEIGHT*2/3)
        pg.display.update()
        pg.mixer.music.load(os.path.join(self.snd_dir, GOOD))
        pg.mixer.music.play(loops=-1)
        self.wait_for_key()
        pg.mixer.music.fadeout(200)

    #클리어시 나타낼 화면
    def ending_screen(self):
        
        self.success_sound.play()
        pg.mixer.music.load(os.path.join(self.snd_dir, ENDING))
        pg.mixer.music.play(loops=-1)
        cv2.destroyAllWindows()
        self.screen.blit(self.end_img, (0,0))
        self.draw_text("잠금을 해제했습니다.", 30, WHITE, WIDTH/2, HEIGHT/3)
        self.draw_text("상명대학교 AI SW 공모전", 20, WHITE, WIDTH/2, HEIGHT*2/3)
        self.draw_text("팀: 느낌알조~?", 18, WHITE, WIDTH/2, HEIGHT*2/3 + 22)
        self.draw_text("지도교수:양희경교수님", 18, WHITE, WIDTH/2, HEIGHT*2/3 + 42)
        pg.display.update()
        sleep(8)
        pg.mixer.music.fadeout(200)
        sleep(2)
        pg.quit()
        quit()

    #화면대기
    def wait_for_key(self):
        self.ending = False
        waiting = True
        while waiting:
            self.clock.tick(FPS)
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    pg.quit()
                    quit()
                elif event.type == pg.KEYDOWN:
                    if event.key == pg.K_ESCAPE:
                        self.exit_sound.play()
                        sleep(0.5)
                        pg.quit()
                        quit()
                    if event.key == pg.K_z:
                        self.decision_sound.play()
                        waiting = False
                        self.start = True
                        self.playing = False
                        sleep(0.14)
            sleep(0.1)

    #화면에 텍스트 처리를 위한 메서드
    def draw_text(self, text, size, color, x, y, back=None):
        font = pg.font.Font(self.gg_font, size)
        text_surface = font.render(text, True, color, back)
        text_rect = text_surface.get_rect()
        text_rect.midtop = (x, y)
        self.screen.blit(text_surface, text_rect)
        #render(text, antialias, color, background=None) -> Surface

    def draw_sprite(self, pos, spr, alpha = ALPHA_MAX):
            spr.set_alpha(alpha)
            self.screen.blit(spr, (round(pos[0]), round(pos[1])))

    #Intro
    def intro(self):
        screen_alpha = 10
        pg.mixer.music.load(os.path.join(self.snd_dir, INTRO))
        pg.mixer.music.play(loops=-1)
        self.background = pg.Surface((WIDTH, HEIGHT))           # 리셋
        self.background.fill(WHITE)

        while(screen_alpha <= ALPHA_MAX):
            self.screen.blit(self.background, (0,0))
            if screen_alpha % 2 == 0:
                img = self.team_img1
            else:
                img = self.team_img2
            self.draw_sprite((0,0), img, screen_alpha)
            screen_alpha += 1
            pg.display.update()
            sleep(0.02)
        pg.mixer.music.fadeout(400)
        sleep(0.5)

    #Ready
    def ready(self):
        cnt = ['3', '2', '1', 'READY?', 'START!']
        for i in cnt:
            self.background = pg.Surface((WIDTH, HEIGHT))           # 리셋
            self.background.fill(BLACK)
            self.screen.blit(self.background, (0,0))
            self.draw_text(i, 70, WHITE, WIDTH/2, HEIGHT/2 -35)
            pg.display.update()
            if i != cnt[-1]:
                self.count_sound.play()
                sleep(1)

g = Game()
g.intro()
while g.start:
    g.start_new()
    while g.playing:
        g.ready()
        g.new()
        if g.start == False:
            break
        if g.ending == True:
            sleep(0.5)
            if g.practice == True:
                if g.clear == True:
                    g.good_screen()
                else:
                    g.fail_screen()
            else:
                if g.clear == True:
                    g.ending_screen()
                else:
                    g.fail_screen()
                
    cv2.destroyAllWindows()