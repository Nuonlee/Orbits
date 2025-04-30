import random

from collections import defaultdict

import pyglet
from pyglet.window import key

import cocos.layer
import cocos.sprite
import cocos.collision_model as cm
import cocos.euclid as eu
import math

import pygame


# Actor class
class Actor(cocos.sprite.Sprite):
    def __init__(self, image, x, y):
        super(Actor, self).__init__(image)
        self.position = pos = eu.Vector2(x, y)
        self.cshape = cm.CircleShape(pos, self.width * 0.5)
        self.massive = 100
        self.collasped = False

    def move(self, offset):
        self.position += offset
        self.cshape.center += offset

    def update(self, elapsed):
        pass

    def collide(self, other):
        pass


# player
class Player_Planet(Actor):
    KEYS_PRESSED = defaultdict(int)
    def __init__(self, x, y):
        super(Player_Planet, self).__init__('rock_type_planet.png', x, y)
        print("player", self.position)
        self.speed = eu.Vector2(200, 0)
        self.bullets = 1
        self.rad = math.pi * 2
        self.radspeed = math.pi / 40
        self.massive = 1000
        self.distance = 150

    def update(self, elapsed):
        pressed = Player_Planet.KEYS_PRESSED
        movement = pressed[key.RIGHT] - pressed[key.LEFT]
        if movement != 0:
            rad = self.rad
            newY = self.distance * math.cos(rad + self.radspeed * movement)
            newX = self.distance * math.sin(rad + self.radspeed * movement)
            self.rad = rad + self.radspeed * movement
            self.position = repos = eu.Vector2(newX + 400, newY + 325)
            self.cshape.center = repos

    def collide(self, other):
        if other == type(Sun):
            self.collasped = True
            self.kill()
        else:
            other.kill()

class Sun(Actor):
    def __init__(self, x, y):
        super(Sun, self).__init__('img/star.png', x, y)
        self.massive = 5000
        self.collasped = False
    def collide(self, other):
        if other == type(Player_Planet):
            self.collasped = True
            self.kill()
        else:
            other.kill()

# Gameloop
class GameLayer(cocos.layer.Layer):
    is_event_handler = True

    def on_key_press(self, k, _):
        Player_Planet.KEYS_PRESSED[k] = 1

    def on_key_release(self, k, _):
        Player_Planet.KEYS_PRESSED[k] = 0

    def __init__(self, hud):
        super(GameLayer, self).__init__()
        w, h = cocos.director.director.get_window_size()
        self.hud = hud
        self.width = w
        self.height = h
        self.update_pl_massive()
        self.updata_sn_massive()
        self.create_player()
        cell = 1.25 * 50
        self.collman = cm.CollisionManagerGrid(0, w, 0, h,
                                               cell, cell)
        self.schedule(self.update)
        self.scorepoint = 1
        self.stability = 1
        self.tempcount = 0
        self.update_stability(self.stability)
        self.planets = []
        self.level = 1
        self.switch = True

    def create_player(self):
        self.player = Player_Planet(self.width * 0.5, self.height * 0.5 + 150)
        self.add(self.player)
        self.sun = Sun(self.width * 0.5, self.height * 0.5)
        self.add(self.sun)
        self.hud.update_pl_ms(self.player.massive)
        self.hud.update_sun_ms(self.sun.massive)

    def update_pl_massive(self, ms=1000):
        self.hud.update_pl_ms(ms)
    def updata_sn_massive(self, ms=10000):
        self.hud.update_sun_ms(ms)
    def update_stability(self, stability=1):
        self.hud.update_stability(stability)

    def update(self, dt):
        self.collman.clear()
        for _, node in self.children:
            self.collman.add(node)
            if not self.collman.knows(node):
                self.remove(node)
        comet = comets()

        playerClsObj = self.collide(self.player)
        if playerClsObj != None:
            self.massive_heavier(self.player, playerClsObj)
            self.player.distance += playerClsObj.massive /40
            self.update_pl_massive(self.player.massive)

        SunClsObj = self.collide(self.sun)
        if SunClsObj != None:
            self.massive_heavier(self.sun, SunClsObj)
            self.player.distance -= SunClsObj.massive / 40
            self.updata_sn_massive(self.sun.massive)

        for pl in self.planets:
            PlClsObj = self.collide(pl)
            if PlClsObj != None:
                self.massive_heavier(pl, PlClsObj)


        if self.switch:
            for _, node in self.children:
                node.update(dt)

        if self.tempcount == 20:
            self.add(comet)
            self.tempcount = 0
        else:
            self.tempcount +=1

        if self.player.distance >= 160 + 45 * self.level:
            print(self.player.distance, self.level)
            self.planets.append(Planets(self.width * 0.5, self.height * 0.5, self.level))
            self.add(self.planets[len(self.planets) - 1])
            self.level += 1

        if len(self.planets) != 0:
            massivesum = 0
            for pl in self.planets:
                massivesum += pl.massive
            self.stability = (massivesum + self.player.massive) / self.sun.massive
        else:
            self.stability = 1
        self.update_stability(self.stability)

        if self.stability <= 0 or self.stability >= 2 or self.player.collasped == True or self.sun.collasped == True:
            self.hud.show_game_over()
            self.switch = False

        if len(self.planets) >=3:
            self.hud.show_game_end()
            self.switch = False

    def collide(self, node):
        if node is not None:
            for other in self.collman.iter_colliding(node):
                if (type(node) == Player_Planet and type(other) == Sun) or (type(node) == Sun and type(other) == Player_Planet):
                    self.hud.show_game_over()
                node.collide(other)
                return other
        return None
    def massive_heavier(self, obj, comets):
        obj.massive += comets.massive * len(self.planets)

class comets(Actor):
    def __init__(self, img='smallrockchipped_640.png'):
        rad = math.pi / 100 * random.randint(0, 201)
        x = math.cos(rad)
        y = math.sin(rad)
        self.massive = 100
        super(comets, self).__init__(img, x * 400 + 400, y * 400 + 325)
        self.speed = eu.Vector2(x, y)

    def update(self, elapsed):
        self.move(self.speed * elapsed * -100)

class Planets(Actor):
    def __init__(self, x, y, level):
        self.PLANET_ING = ['Space Sprites/PLanet_Shadow_1.png', 'Space Sprites/Planet0.png', 'Space Sprites/Planet1.png', 'Space Sprites/Planet2.png', 'Space Sprites/Planet3.png', 'Space Sprites/Planet4.png', 'Space Sprites/Planet5.png']
        super(Planets, self).__init__(self.PLANET_ING[random.randint(0, len(self.PLANET_ING) - 1)], x, y + 45*level + 55)
        print(self.position)
        self.rad = math.pi * 2
        self.radspeed = math.pi / 100
        self.level = level

    def update(self, elapsed):
        rad = self.rad
        newY = 150 * math.cos(rad + self.radspeed) * self.level
        newX = 150 * math.sin(rad + self.radspeed) * self.level
        self.rad = rad + self.radspeed
        self.position = repos = eu.Vector2(newX + 400, newY + 325)
        self.cshape.center = repos

    def collide(self, other):
        self.massive += other.massive
        other.kill()


class HUD(cocos.layer.Layer):
    def __init__(self):
        super(HUD, self).__init__()
        w, h = cocos.director.director.get_window_size()
        self.player_ms_text = cocos.text.Label('', font_size=18)
        self.player_ms_text.position = (20, h - 40)
        self.sun_ms_text = cocos.text.Label('', font_size=18)
        self.sun_ms_text.position = (20, h - 80)
        self.stability_text = cocos.text.Label('', font_size=18)
        self.stability_text.position = (w - 160, h - 40)
        self.add(self.player_ms_text)
        self.add(self.sun_ms_text)
        self.add(self.stability_text)

    def update_pl_ms(self, massive):
        self.player_ms_text.element.text = 'Planet: %s' % massive

    def update_sun_ms(self, massive):
        self.sun_ms_text.element.text = 'Star: %s' % massive
    def update_stability(self, stability):
        self.stability_text.element.text = 'Stability: %s' % round(stability, 2)
    def show_game_over(self):
        w, h = cocos.director.director.get_window_size()
        game_over = cocos.text.Label('Game Over', font_size=50,
                                     anchor_x='center',
                                     anchor_y='center')
        game_over.position = w * 0.5, h * 0.5
        self.add(game_over)
        pygame.quit()

    def show_game_end(self):
        w, h = cocos.director.director.get_window_size()
        game_win = cocos.text.Label('You Win!', font_size=50,
                                    anchor_x='center',
                                    anchor_y='center')
        game_win.position = w * 0.5, h * 0.5
        self.add(game_win)
        pygame.quit()

if __name__ == '__main__':
    pygame.init()
    cocos.director.director.init(caption='Cocos Invaders',
                                 width=800, height=650)
    mySound = pygame.mixer.Sound('396239__romariogrande__alien-dream.wav')
    mySound.play(-1)
    main_scene = cocos.scene.Scene()
    hud_layer = HUD()
    main_scene.add(hud_layer, z=1)
    game_layer = GameLayer(hud_layer)
    main_scene.add(game_layer, z=0)
    cocos.director.director.run(main_scene)