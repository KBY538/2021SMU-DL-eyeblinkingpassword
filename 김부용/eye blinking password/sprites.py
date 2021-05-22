#sprite classes for ploatform game
import pygame as pg
from time import sleep
from settings import *
vec = pg.math.Vector2

#Menu Select 클래스
class Select(pg.sprite.Sprite):

    def __init__(self, game):
        pg.sprite.Sprite.__init__(self)
        self.game = game
        self.image = pg.Surface((120,40))
        self.image.blit(self.game.menu_select, (0, 0))
        self.image.set_alpha(0)
        self.image.set_colorkey(WHITE)
        self.rect = self.image.get_rect()
        self.rect.center = (WIDTH - 70, HEIGHT - 340)
        self.select_number = 0

    def update(self):
        self.acc = vec(0, 0)
        keys = pg.key.get_pressed()
        if keys[pg.K_LEFT]:
            self.game.key_sound.play()
            self.select_number -= 1
            if self.select_number < 0:
                self.select_number = 2
            sleep(0.14)

        if keys[pg.K_RIGHT]:
            self.game.key_sound.play()
            self.select_number += 1
            if self.select_number > 2:
                self.select_number = 0
            sleep(0.14)

        if keys[pg.K_z] and self.select_number == 0:
            self.game.decision_sound.play()
            self.game.start_playing = False
            self.game.playing = True
            self.game.practice = True

        if keys[pg.K_z] and self.select_number == 1:
            self.game.decision_sound.play()
            self.game.start_playing = False
            self.game.playing = True
            self.game.practice = False

        if keys[pg.K_z] and self.select_number == 2:
            self.game.exit_sound.play()
            sleep(0.5)
            pg.quit()
            quit()
        
        sleep(0.05)

class Blink(pg.sprite.Sprite):
    def __init__(self, game):
        pg.sprite.Sprite.__init__(self)
        self.game = game
        self.speed = 5
        if game.practice == True:
            self.alpha = ALPHA_MAX
        else:
            self.alpha = 0
        self.correct = 0
        self.font = pg.font.Font('font/'+GG, 50)
        self.image = self.font.render('I', True, WHITE) # eye
        self.rect = self.image.get_rect()
        self.rect.x = 0
        self.rect.y = HEIGHT/2 -25
        
    def update(self):
        self.rect.x += self.speed
        if self.rect.x >= WIDTH/2 + 15:
            self.alpha -= 2
            if self.rect.x >= WIDTH:
                self.kill()
            if self.correct != -1:
                x = self.rect.x
                if self.correct == 0:
                    self.image = self.font.render('I', True, RED)
                elif self.correct == 1:
                    self.image = self.font.render('I', True, GREEN)
                self.rect = self.image.get_rect()
                self.rect.x = x
                self.rect.y = HEIGHT/2 -25
                self.correct = -1

        self.image.set_alpha(self.alpha)

#이미지 sheet 및 이미지 로드를 위한 클래스
class Spritesheet:
    def __init__(self, filename):
        self.spritesheet = pg.image.load(filename).convert()

        """The returned Surface will contain the same color format,
        colorkey and alpha transparency as the file it came from.
        You will often want to call Surface.convert() with no arguments,
        to create a copy that will draw more quickly on the screen."""

    #불러온 이미지(self.spritesheet)를  (0,0)에 불러오며, 이미지의(x,y)부터 (width, height)까지 자르겠다.
    def get_image(self, x, y, width, height):
        image = pg.Surface((width, height))
        image.blit(self.spritesheet, (0,0), (x, y, width, height))
        return image