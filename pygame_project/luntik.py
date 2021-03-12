import random, sys, time, math, pygame
from pygame.locals import *

FPS = 30
WINWIDTH = 1000
WINHEIGHT = 840
HALF_WINWIDTH = int(WINWIDTH / 2)
HALF_WINHEIGHT = int(WINHEIGHT / 2)

GRASSCOLOR = (24, 255, 20)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GRAY = (185, 185, 185)

TEXTSHADOWCOLOR = GRAY
TEXTCOLOR = WHITE
GAMEOVERTIME = 3
CENTERDIST = 90     # как далеко от центра отодвинулмя игрок перед перемещением камеры
MOVESPEED = 9         # как быстро движется игрок
JUMPSPEED = 6       # как быстро игрок подпрыгивает (чем больше, тем медленнее)
JUMPHEIGHT = 30    # как высоко подпрыгивает игрок
STARTSIZE = 150       # размер игрока в начале игры
WINSIZE = 450        # насколько большим должен быть игрок, чтобы выиграть
INVULNTIME = 2       # как долго игрок будет неуязвимым после удара (сек)
MAXHEALTH = 3        # сколько здоровья у игрока в начале

NUMGRASS = 120        # количество единиц травы в активной области
NUMOBJECTS = 30    # количество движущихся объектов в активной зоне
OBJECTMINSPEED = 3  # самая низкая скорость движущегося объекта
OBJECTMAXSPEED = 7  # самая высокая скорость движущегося объекта
CHANGEDIRECT = 2    # вероятность того, что объект сменит направление (%)
LEFT = 'left'
RIGHT = 'right'

"""
Эта программа имеет три структуры данных для представления игрока, других движущихся объектов и фоновых объектов травы.
 Структуры данных представляют собой словари со следующими ключами:
 Ключи, используемые всеми тремя структурами данных:
    'x' - координата левого края объекта игрока в игровом мире (не пиксельная координата на экране)
    'y' - координата верхнего края объекта игрока в игровом мире (не пиксельная координата на экране)
    'rect' - объект pygame.Rect, показывающий, где на экране расположен объект
 Ключи структуры данных игрока:
    'surface' - объект pygame.Surface, в котором хранится изображение игрока, которое будет выведено на экран
    'facing' - установлен в LEFT или RIGHT, сохраняет направление, в котором смотрит игрок
    'size' - ширина и высота игрока в пикселях (Ширина и высота всегда одинаковы)
    'jump' - показывает, в какой точке отскока находится игрок, где 0 означает неподвижность
    'health' - число, показывающее, сколько раз игрок может быть поражен несъедобным предметом, прежде чем умрет.
 Ключи структуры данных других движущихся объектов:
    'surface' - объект pygame.Surface, в котором хранится изображение белки, выводимое на экран
    'movex' - на сколько пикселей за кадр объект перемещается по горизонтали. 
              Отрицательное целое число перемещается влево, положительное - вправо
    'movey' - на сколько пикселей за кадр объект перемещается по вертикали. 
              Отрицательное целое число движется вверх, положительное - вниз
    'width' - ширина изображения объекта в пикселях
    'height' - высота изображения объекта в пикселях
    'jump' - показывает, в какой точке отскока находится объект, где 0 означает неподвижность
    'jumpspeed' - как быстро объект подпрыгивает. Меньшее число означает более быстрый отскок
    'jumpheight' - как высоко (в пикселях) подпрыгивает объект
    'view' - в зависимости от значения определяет, является объект съедобным или нет
Ключи структуры данных объекта травы:
    'grassImage' - целое число, которое относится к индексу объекта pygame.Surface в GRASSIMAGES,
                   используемого для этого объекта травы
"""


def runGame():
    pygame.mixer.music.load('фон.mp3')
    pygame.mixer.music.play(-1)
    sound_plus = pygame.mixer.Sound('бонус.mp3')
    sound_minus = pygame.mixer.Sound('антибонус.mp3')
    sound_go = pygame.mixer.Sound('gameover.mp3')
    sound_win = pygame.mixer.Sound('win.mp3')
    # настраиваем переменные для начала новой игры
    invulnerableMode = False  # если игрок неуязвим
    invulnerableStartTime = 0  # время, когда игрок стал неуязвимым
    gameOverMode = False      # если игрок проиграл
    gameOverStartTime = 0     # время, когда игрок проиграл
    gameWinStartTime = 0      # время, когда игрок выиграл
    winMode = False           # если игрок выиграл

    # camerax и cameray - координаты середины обзора камеры
    camerax = 0
    cameray = 0

    grassObjs = []    # сохраняет все объекты травы в игре
    objectsObjs = []  # сохраняет все движущиеся объекты, не относящиеся к игроку
    # сохраним объект игрока:
    playerObj = {'surface': pygame.transform.scale(LEFT_IMG, (STARTSIZE, STARTSIZE)),
                 'facing': LEFT,
                 'size': STARTSIZE,
                 'x': HALF_WINWIDTH,
                 'y': HALF_WINHEIGHT,
                 'jump': 0,
                 'health': MAXHEALTH}

    moveLeft = False
    moveRight = False
    moveUp = False
    moveDown = False

    # начнем с изображений травы в случайных местах экрана
    for i in range(10):
        grassObjs.append(makeNewGrass(camerax, cameray))
        grassObjs[i]['x'] = random.randint(0, WINWIDTH)
        grassObjs[i]['y'] = random.randint(0, WINHEIGHT)

    while True:  # основной игровой цикл
        # проверяем, нужно ли отключать неуязвимость
        if invulnerableMode and time.time() - invulnerableStartTime > INVULNTIME:
            invulnerableMode = False

        # перемещаем все движущиеся объекты, кроме игрока
        for oObj in objectsObjs:
            # перемещаем объект и регулируем его отскок
            oObj['x'] += oObj['movex']
            oObj['y'] += oObj['movey']
            oObj['jump'] += 1
            if oObj['jump'] > oObj['jumpspeed']:
                oObj['jump'] = 0  # обнулим количество прыжков

            # попытка изменить направление объекта
            if random.randint(0, 99) < CHANGEDIRECT:
                oObj['movex'] = getRandomSpeed()
                oObj['movey'] = getRandomSpeed()

        # пройдёмся по всем объектам и посмотрим, нужно ли их удалить
        for i in range(len(grassObjs) - 1, -1, -1):
            if isOutsideActiveArea(camerax, cameray, grassObjs[i]):
                del grassObjs[i]
        for i in range(len(objectsObjs) - 1, -1, -1):
            if isOutsideActiveArea(camerax, cameray, objectsObjs[i]):
                del objectsObjs[i]

        # добавим больше травы и объектов, если их не хватает
        while len(grassObjs) < NUMGRASS:
            grassObjs.append(makeNewGrass(camerax, cameray))
        while len(objectsObjs) < NUMOBJECTS:
            objectsObjs.append(makeNewObject(camerax, cameray))

        # отрегулируем camerax и cameray
        playerCenterx = playerObj['x'] + int(playerObj['size'] / 2)
        playerCentery = playerObj['y'] + int(playerObj['size'] / 2)
        if (camerax + HALF_WINWIDTH) - playerCenterx > CENTERDIST:
            camerax = playerCenterx + CENTERDIST - HALF_WINWIDTH
        elif playerCenterx - (camerax + HALF_WINWIDTH) > CENTERDIST:
            camerax = playerCenterx - CENTERDIST - HALF_WINWIDTH
        if (cameray + HALF_WINHEIGHT) - playerCentery > CENTERDIST:
            cameray = playerCentery + CENTERDIST - HALF_WINHEIGHT
        elif playerCentery - (cameray + HALF_WINHEIGHT) > CENTERDIST:
            cameray = playerCentery - CENTERDIST - HALF_WINHEIGHT

        # рисуем зеленый фон
        DISPLAYSURF.fill(GRASSCOLOR)

        # рисуем все объекты травы на экране
        for gObj in grassObjs:
            gRect = pygame.Rect((gObj['x'] - camerax,
                                  gObj['y'] - cameray,
                                  gObj['width'],
                                  gObj['height']))
            DISPLAYSURF.blit(GRASSIMAGES[gObj['grassImage']], gRect)


        # рисуем движущиеся объекты
        for oObj in objectsObjs:
            oObj['rect'] = pygame.Rect((oObj['x'] - camerax,
                                        oObj['y'] - cameray - getJumpAmount(oObj['jump'],
                                                                            oObj['jumpspeed'],
                                                                            oObj['jumpheight']),
                                        oObj['width'],
                                        oObj['height']) )
            DISPLAYSURF.blit(oObj['surface'], oObj['rect'])


        # рисуем персонажа игрока
        flashIsOn = round(time.time(), 1) * 10 % 2 == 1
        if not gameOverMode and not (invulnerableMode and flashIsOn):
            playerObj['rect'] = pygame.Rect((playerObj['x'] - camerax,
                                              playerObj['y'] - cameray - getJumpAmount(playerObj['jump'],
                                                                                       JUMPSPEED, JUMPHEIGHT),
                                              playerObj['size'],
                                              playerObj['size']))
            DISPLAYSURF.blit(playerObj['surface'], playerObj['rect'])


        # рисуем счетчик здоровья
        drawHealthMeter(playerObj['health'])

        for event in pygame.event.get():
            if event.type == QUIT:
                terminate()

            elif event.type == KEYDOWN:
                if event.key in (K_UP, K_w):
                    moveDown = False
                    moveUp = True
                elif event.key in (K_DOWN, K_s):
                    moveUp = False
                    moveDown = True
                elif event.key in (K_LEFT, K_a):
                    moveRight = False
                    moveLeft = True
                    if playerObj['facing'] != LEFT:  # меняем изображение игрока
                        playerObj['surface'] = pygame.transform.scale(LEFT_IMG, (playerObj['size'], playerObj['size']))
                    playerObj['facing'] = LEFT
                elif event.key in (K_RIGHT, K_d):
                    moveLeft = False
                    moveRight = True
                    if playerObj['facing'] != RIGHT:  # меняем изображение игрока
                        playerObj['surface'] = pygame.transform.scale(RIGHT_IMG, (playerObj['size'], playerObj['size']))
                    playerObj['facing'] = RIGHT
                elif winMode and event.key == K_r:
                    return

            elif event.type == KEYUP:
                # перестаем двигать персонажа игрока
                if event.key in (K_LEFT, K_a):
                    moveLeft = False
                elif event.key in (K_RIGHT, K_d):
                    moveRight = False
                elif event.key in (K_UP, K_w):
                    moveUp = False
                elif event.key in (K_DOWN, K_s):
                    moveDown = False
                elif event.key == K_ESCAPE:
                    terminate()

        if not gameOverMode:
            # собственно перемещаем игрока
            if moveLeft:
                playerObj['x'] -= MOVESPEED
            if moveRight:
                playerObj['x'] += MOVESPEED
            if moveUp:
                playerObj['y'] -= MOVESPEED
            if moveDown:
                playerObj['y'] += MOVESPEED

            if (moveLeft or moveRight or moveUp or moveDown) or playerObj['jump'] != 0:
                playerObj['jump'] += 1

            if playerObj['jump'] > JUMPSPEED:
                playerObj['jump'] = 0  # обнулим количество прыжков

            # проверим, не столкнулся ли игрок с другими объектами
            for i in range(len(objectsObjs)-1, -1, -1):
                obObj = objectsObjs[i]
                if 'rect' in obObj and playerObj['rect'].colliderect(obObj['rect']):
                    # игрок столкнулся с объектом

                    if obObj['view'] == 'eatable':
                        # игрок ест съедобный объект
                        sound_plus.play()
                        playerObj['size'] += int((obObj['width'] * obObj['height']) ** 0.2) + 1
                        del objectsObjs[i]

                        if playerObj['facing'] == LEFT:
                            playerObj['surface'] = pygame.transform.scale(LEFT_IMG, (playerObj['size'],
                                                                                     playerObj['size']))
                        if playerObj['facing'] == RIGHT:
                            playerObj['surface'] = pygame.transform.scale(RIGHT_IMG, (playerObj['size'],
                                                                                      playerObj['size']))

                        if playerObj['size'] > WINSIZE:
                            winMode = True  # включаем "режим выигрыша"
                            gameWinStartTime = time.time()

                    elif not invulnerableMode:
                        # игрок задевает несъедобный объект и теряет жизнь
                        sound_minus.play()
                        invulnerableMode = True
                        invulnerableStartTime = time.time()
                        playerObj['health'] -= 1
                        if playerObj['health'] == 0:
                            gameOverMode = True  # включаем "режим окончания игры"
                            gameOverStartTime = time.time()
        else:
            # игра окончена, выводим заставку "игра окончена"
            pygame.mixer.music.stop()
            sound_go.play()
            showTextScreen('Game Over')
            if time.time() - gameOverStartTime > GAMEOVERTIME:
                return  # завершаем текущую игру

        # проверим, выиграл ли игрок
        if winMode:
            pygame.mixer.music.stop()
            sound_win.play(0)
            showTextScreen('WIN')
            if time.time() - gameWinStartTime > GAMEOVERTIME:
                return
        pygame.display.update()
        FPSCLOCK.tick(FPS)

def checkForKeyPress():
    checkForQuit()
    for event in pygame.event.get([KEYDOWN, KEYUP]):
        if event.type == KEYDOWN:
            continue
        return event.key
    return None

def showTextScreen(text):
    # Функция отображает крупный текст в
    # в центре экрана, пока не будет нажата какая-нибудь клавиша.
    # Рисуем тень от текста
    titleSurf, titleRect = makeTextObjs(text, BIGFONT, TEXTSHADOWCOLOR)
    titleRect.center = (int(WINWIDTH / 2), int(WINHEIGHT / 2))
    DISPLAYSURF.blit(titleSurf, titleRect)

    # Рисуем текст
    titleSurf, titleRect = makeTextObjs(text, BIGFONT, TEXTCOLOR)
    titleRect.center = (int(WINWIDTH / 2) - 3, int(WINHEIGHT / 2) - 3)
    DISPLAYSURF.blit(titleSurf, titleRect)

    # Рисуем дополнительный текст «Нажмите клавишу, чтобы играть»
    pressKeySurf, pressKeyRect = makeTextObjs('Press a key to play.', BASICFONT, TEXTCOLOR)
    pressKeyRect.center = (int(WINWIDTH / 2), int(WINHEIGHT / 2) + 100)
    DISPLAYSURF.blit(pressKeySurf, pressKeyRect)

    while checkForKeyPress() == None:
        pygame.display.update()
        FPSCLOCK.tick()

def checkForQuit():
    for event in pygame.event.get(QUIT):
        terminate()
    for event in pygame.event.get(KEYUP):
        if event.key == K_ESCAPE:
            terminate()  # если нажата клавиша Esc, завершаем работу
        pygame.event.post(event)

def makeTextObjs(text, font, color):
    surf = font.render(text, True, color)
    return surf, surf.get_rect()

def drawHealthMeter(currentHealth):
    for i in range(currentHealth):  # рисуем красные деления, отображающие уровень здоровья
        pygame.draw.rect(DISPLAYSURF, RED,   (15, 5 + (10 * MAXHEALTH) - i * 10, 20, 10))
    for i in range(MAXHEALTH):  # рисуем белый контур
        pygame.draw.rect(DISPLAYSURF, WHITE, (15, 5 + (10 * MAXHEALTH) - i * 10, 20, 10), 1)


def terminate():
    pygame.quit()
    sys.exit()


def getJumpAmount(currentJump, jumpSpeed, jumpHeight):
    # Возвращает количество пикселей для смещения на основе отскока
    # Чем больше jumpSpeed, тем медленнее отскок
    # Чем больше jumpHeight означает более высокий отскок.
    # currentJump всегда будет меньше jumpSpeed
    return int(math.sin((math.pi / float(jumpSpeed)) * currentJump) * jumpHeight)

def getRandomSpeed():
    speed = random.randint(OBJECTMINSPEED, OBJECTMAXSPEED)
    if random.randint(0, 1) == 0:
        return speed
    else:
        return -speed


def getRandomOffCameraPos(camerax, cameray, objWidth, objHeight):
    # создадим прямоугольник обзора камеры
    cameraRect = pygame.Rect(camerax, cameray, WINWIDTH, WINHEIGHT)
    while True:
        x = random.randint(camerax - WINWIDTH, camerax + (2 * WINWIDTH))
        y = random.randint(cameray - WINHEIGHT, cameray + (2 * WINHEIGHT))
        # создаем объект Rect со случайными координатами и используем colliderect()
        # чтобы правый край не попал в поле зрения камеры
        objRect = pygame.Rect(x, y, objWidth, objHeight)
        if not objRect.colliderect(cameraRect):
            return x, y


def makeNewObject(camerax, cameray):
    sq = {}
    sq['width'] = 65
    sq['height'] = 65
    sq['x'], sq['y'] = getRandomOffCameraPos(camerax, cameray, sq['width'], sq['height'])
    sq['movex'] = getRandomSpeed()
    sq['movey'] = getRandomSpeed()
    a = random.randint(0, 1)
    if a == 1:    # персонаж игрока смотрит влево
        img = pygame.image.load(random.choice(EAT_IMG))
        sq['surface'] = pygame.transform.scale(img, (sq['width'], sq['height']))  # * *
        sq['view'] = 'eatable'
    else:  # персонаж игрока смотрит вправо
        img = pygame.image.load(random.choice(UNEAT_IMG))
        sq['surface'] = pygame.transform.scale(img, (sq['width'], sq['height']))  # * *
        sq['view'] = 'uneatable'
    sq['jump'] = 0
    sq['jumpspeed'] = random.randint(10, 18)
    sq['jumpheight'] = random.randint(10, 50)
    return sq


def makeNewGrass(camerax, cameray):
    gr = {}
    gr['grassImage'] = random.randint(0, len(GRASSIMAGES) - 1)
    gr['width'] = GRASSIMAGES[0].get_width()
    gr['height'] = GRASSIMAGES[0].get_height()
    gr['x'], gr['y'] = getRandomOffCameraPos(camerax, cameray, gr['width'], gr['height'])
    gr['rect'] = pygame.Rect((gr['x'], gr['y'], gr['width'], gr['height']))
    return gr


def isOutsideActiveArea(camerax, cameray, obj):
    # Возвращаем False, если camerax и cameray больше чем
    # длина половины окна за краем окна
    jumpLeftBorder = camerax - WINWIDTH
    jumpTopBorder = cameray - WINHEIGHT
    jumpRect = pygame.Rect(jumpLeftBorder, jumpTopBorder, WINWIDTH * 3, WINHEIGHT * 3)
    objRect = pygame.Rect(obj['x'], obj['y'], obj['width'], obj['height'])
    return not jumpRect.colliderect(objRect)


if __name__ == '__main__':
    pygame.init()
    FPSCLOCK = pygame.time.Clock()
    pygame.display.set_icon(pygame.image.load('gameicon.png'))
    DISPLAYSURF = pygame.display.set_mode((WINWIDTH, WINHEIGHT))
    pygame.display.set_caption("Handmade games")
    BASICFONT = pygame.font.Font('freesansbold.ttf', 32)
    BIGFONT = pygame.font.Font('freesansbold.ttf', 100)
    # загружаем изображения
    EAT_IMG = ['donut.png', 'sweet.png', 'apple.png', 'tomato.png', 'grape.png', 'banana.png', 'icecream.png']
    UNEAT_IMG = ['paper.png', 'bag.png', 'disk.png', 'shoe.png', 'socks.png', 'lamp.png']
    LEFT_IMG = pygame.image.load('luntik.png')
    RIGHT_IMG = pygame.transform.flip(LEFT_IMG, True, False)
    GRASSIMAGES = []
    for i in range(1, 5):
        img = pygame.image.load('grass%s.png' % i)
        GRASSIMAGES.append(img)
    showTextScreen("Luntik's lunch")
    while True:
        runGame()
