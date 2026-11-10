# =====================================================================
# QUILOMBO DOS PALMARES — AB2 de Computação Gráfica (OpenGL puro, Python)
# =====================================================================
# Execução:  python main.py
# Bibliotecas: GLFW (só a janela, teclado e mouse) + PyOpenGL (OpenGL pipeline fixo + GLU)
#              + Pillow (só pra ler as imagens das texturas e desenhar o texto do HUD).
#
# Organização:
#   primitivas.py  -> cilindro, esfera, disco, caixa, texturas e materiais
#   objetos.py     -> cada objeto da cena modelado com as primitivas + transformações
#   main.py        -> câmera, iluminação, interações, laço principal

import math
import random
import sys
import time
import glfw
from PIL import Image, ImageDraw, ImageFont
from OpenGL.GL import *
from OpenGL.GLU import *

import objetos as obj
from historias import HISTORIAS
from primitivas import textura, PASTA

LARGURA, ALTURA = 1280, 720
ALTURA_OLHOS = 1.7
# No macOS Retina o framebuffer tem mais pixels que a janela (ex.: 2×).
# UI_SCALE / FB_* são preenchidos ao abrir a janela e usados no HUD.
UI_SCALE = 1.0
FB_W, FB_H = LARGURA, ALTURA

# ---------------------------------------------------------------------
# DISPOSIÇÃO DA CENA (x, z) — o portão fica em +Z, a Muxima no fundo (-Z)
# ---------------------------------------------------------------------
MUXIMA = (0.0, -10.0)
OCAS = [(-13.0, -4.0), (-9.0, -16.0)]
CASA_FARINHA = (12.0, -6.0)
FOGUEIRA = (4.0, 6.0)
LAGOA = (-12.0, 10.0)
POCO = (12.0, 9.0)
ATALAIA = (16.0, -16.0)
ARVORES = [(7.0, -18.0), (-4.0, 18.0), (18.0, 4.0),
           (32.0, 5.0), (-30.0, -12.0), (20.0, 32.0), (-25.0, 30.0), (35.0, -25.0),
           (0.0, -40.0), (-42.0, 10.0), (28.0, -42.0), (-20.0, -38.0), (45.0, 20.0)]
COQUEIROS = [(-17.0, 4.0), (15.0, 17.0), (-6.0, -21.0), (29.0, 17.0), (-35.0, -2.0), (8.0, 36.0)]


def virado_pro_centro(x, z):
    """Ângulo (graus, em Y) que faz o +Z local de um objeto apontar para o centro da praça."""
    return math.degrees(math.atan2(-x, -z))


def local_para_mundo(centro, giro_graus, lx, lz):
    """Converte um ponto das coordenadas LOCAIS de um objeto para o MUNDO:
    primeiro gira (rotação em Y), depois translada até o centro do objeto."""
    g = math.radians(giro_graus)
    return (centro[0] + lx * math.cos(g) + lz * math.sin(g),
            centro[1] - lx * math.sin(g) + lz * math.cos(g))


# ---------------------------------------------------------------------
# COLISÃO (simples: círculos no plano XZ)
# ---------------------------------------------------------------------
OBSTACULOS = [(FOGUEIRA[0], FOGUEIRA[1], 1.3), (POCO[0], POCO[1], 1.4), (ATALAIA[0], ATALAIA[1], 2.5)]
# casas: parede em ANEL com um vão de porta (dá pra entrar). (x, z, raio, direção da porta em graus, meia porta em rad)
CASAS = [(MUXIMA[0], MUXIMA[1], 4.0, 0.0, 0.17)]
CASAS += [(x, z, obj.OCA_RAIO, None, obj.OCA_MEIA_PORTA - 0.08) for x, z in OCAS]
OBSTACULOS += [(x, z, 0.6) for x, z in ARVORES + COQUEIROS]
OBSTACULOS += [(CASA_FARINHA[0] - 1.5 * 0.7, CASA_FARINHA[1] - 0.5, 1.4)]   # forno (aprox.)


# a parte mais clara da foto do céu (u = 0,70) fica na direção do sol (azimute atan2(0.35, 0.45))
GIRO_CEU = 0.70 - math.atan2(0.35, 0.45) / (2 * math.pi)


def pode_ficar(x, z, portao_aberto):
    r = math.hypot(x, z)
    if r > 150:
        return False
    # paliçada: uma faixa em volta do raio 25. Só passa pelo vão, com o portão aberto.
    if abs(r - obj.RAIO_MURO) < 0.7:
        no_vao = z > 0 and abs(x) < obj.MEIA_ABERTURA - 0.35
        if not (no_vao and portao_aberto):
            return False
    for ox, oz, orr in OBSTACULOS:
        if math.hypot(x - ox, z - oz) < orr:
            return False
    for cx, cz, raio, giro, meia_porta in CASAS:
        dx, dz = x - cx, z - cz
        d = math.hypot(dx, dz)
        if abs(d - raio) < 0.45:                       # encostado na parede?
            g = math.radians(virado_pro_centro(cx, cz) if giro is None else giro)
            porta = (math.sin(g), math.cos(g))         # direção da porta (o +Z local girado)
            cos_ang = (dx * porta[0] + dz * porta[1]) / max(d, 1e-6)
            if math.acos(max(-1, min(1, cos_ang))) > meia_porta:
                return False                           # parede (fora do vão da porta)
    # lagoa: dentro da elipse (x/a)² + (z/b)² < 1
    dx, dz = x - LAGOA[0], z - LAGOA[1]
    if (dx / (obj.LAGOA_RX + 0.3)) ** 2 + (dz / (obj.LAGOA_RZ + 0.3)) ** 2 < 1:
        return False
    return True


# ---------------------------------------------------------------------
# CÂMERA EM PRIMEIRA PESSOA
# ---------------------------------------------------------------------
class Camera:
    def __init__(self):
        self.x, self.z = 0.0, 38.0          # começa do lado de fora, de frente pro portão
        self.yaw = 0.0                      # azimute (0 = olhando para -Z)
        self.pitch = -0.05                  # elevação
        self.fov = 65.0
        self.altura = ALTURA_OLHOS          # muda quando sobe na atalaia
        self.orto = False
        self.tam_orto = 40.0

    def direcao(self):
        return (math.sin(self.yaw) * math.cos(self.pitch), math.sin(self.pitch),
                -math.cos(self.yaw) * math.cos(self.pitch))

    def projecao(self):
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        aspecto = LARGURA / ALTURA
        if self.orto:
            s = self.tam_orto
            glOrtho(-s * aspecto, s * aspecto, -s, s, 1.0, 400.0)    # PROJEÇÃO ORTOGRÁFICA
        else:
            gluPerspective(self.fov, aspecto, 0.1, 400.0)            # PROJEÇÃO PERSPECTIVA (fov, aspecto, near, far)
        glMatrixMode(GL_MODELVIEW)

    def aplicar(self):
        glLoadIdentity()
        if self.orto:
            gluLookAt(0, 150, 0, 0, 0, 0, 0, 0, -1)                  # vista de planta: olhando reto pra baixo
        else:
            d = self.direcao()
            eye = (self.x, self.altura, self.z)
            gluLookAt(eye[0], eye[1], eye[2], eye[0] + d[0], eye[1] + d[1], eye[2] + d[2], 0, 1, 0)

    def mover(self, frente, lado, dt, correr, portao_aberto):
        vel = (9.0 if correr else 5.0) * dt
        fx, fz = math.sin(self.yaw), -math.cos(self.yaw)          # frente (só no plano XZ)
        lx, lz = -fz, fx                                           # lado direito
        nx = self.x + (fx * frente + lx * lado) * vel
        nz = self.z + (fz * frente + lz * lado) * vel
        # testa X e Z separadamente: o jogador "desliza" ao encostar numa parede
        if pode_ficar(nx, self.z, portao_aberto):
            self.x = nx
        if pode_ficar(self.x, nz, portao_aberto):
            self.z = nz


# ---------------------------------------------------------------------
# HUD (texto na tela): o Pillow desenha o texto numa imagem e o OpenGL copia os pixels
# ---------------------------------------------------------------------
_cache_txt = {}


def carregar_fonte(tamanho, negrito=False):
    """Carrega TTF do sistema. No Mac, 'arial.ttf' minúsculo falha e caía no bitmap minúsculo do Pillow."""
    if negrito:
        nomes = [
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
            "/Library/Fonts/Arial Bold.ttf",
            "C:/Windows/Fonts/arialbd.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "Arial Bold.ttf", "arialbd.ttf", "DejaVuSans-Bold.ttf",
        ]
    else:
        nomes = [
            "/System/Library/Fonts/Supplemental/Arial.ttf",
            "/Library/Fonts/Arial.ttf",
            "C:/Windows/Fonts/arial.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "Arial.ttf", "arial.ttf", "DejaVuSans.ttf",
        ]
    for nome in nomes:
        try:
            return ImageFont.truetype(nome, tamanho)
        except OSError:
            continue
    return ImageFont.load_default()


def texto(x, y, s, fonte, cor=(255, 255, 255)):
    """x, y em coordenadas da janela lógica (1280×720). Converte pro framebuffer (Retina)."""
    chave = (s, cor, id(fonte), UI_SCALE)
    if chave not in _cache_txt:
        x0, y0, x1, y1 = fonte.getbbox(s)
        img = Image.new("RGBA", (x1 + 4, y1 + 6), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        d.text((2, 2), s, font=fonte, fill=(0, 0, 0, 255))          # sombra
        d.text((0, 0), s, font=fonte, fill=tuple(cor) + (255,))
        img = img.transpose(Image.FLIP_TOP_BOTTOM)                  # OpenGL conta as linhas de baixo pra cima
        _cache_txt[chave] = (img.tobytes(), img.width, img.height)
        if len(_cache_txt) > 200:
            _cache_txt.clear()
    dados, w, h = _cache_txt[chave]
    # glWindowPos / glDrawPixels usam pixels do framebuffer (2× no Retina)
    glWindowPos2d(x * UI_SCALE, FB_H - y * UI_SCALE - h)
    glDrawPixels(w, h, GL_RGBA, GL_UNSIGNED_BYTE, dados)


_cache_painel = {}


def quebrar_linhas(s, fonte, largura):
    """Quebra o texto em linhas que cabem na largura (em pixels), palavra por palavra."""
    linhas, atual = [], ""
    for palavra in s.split():
        teste = (atual + " " + palavra).strip()
        if fonte.getlength(teste) <= largura:
            atual = teste
        else:
            linhas.append(atual)
            atual = palavra
    linhas.append(atual)
    return linhas


def painel_historia(i, fonte_titulo, fonte):
    """Monta (uma vez só) a imagem do painel da história i: caixa escura, título e texto."""
    chave = (i, UI_SCALE)
    if chave not in _cache_painel:
        titulo, corpo = HISTORIAS[i][0], HISTORIAS[i][1]
        tipo = HISTORIAS[i][2]                                              # História, Lenda ou Folclore
        s = UI_SCALE
        W = int(760 * s)
        pad, lh = int(30 * s), int(26 * s)
        linhas = quebrar_linhas(corpo, fonte, W - 2 * pad)
        H = int(110 * s) + len(linhas) * lh
        img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        d.rounded_rectangle([0, 0, W - 1, H - 1], radius=max(8, int(14 * s)),
                            fill=(20, 12, 6, 215), outline=(230, 170, 80, 255), width=max(2, int(2 * s)))
        cor_titulo = (255, 210, 120, 255) if tipo == "História" else (170, 210, 255, 255)
        d.text((pad, int(18 * s)), tipo + "  ·  " + titulo, font=fonte_titulo, fill=cor_titulo)
        for k, linha in enumerate(linhas):
            d.text((pad, int(58 * s) + k * lh), linha, font=fonte, fill=(245, 235, 215, 255))
        rodape = "H: próxima história   (%d/%d)" % (i + 1, len(HISTORIAS)) if i + 1 < len(HISTORIAS) \
            else "H: fechar   (%d/%d)" % (i + 1, len(HISTORIAS))
        d.text((pad, H - int(36 * s)), rodape, font=fonte, fill=(200, 180, 140, 255))
        img = img.transpose(Image.FLIP_TOP_BOTTOM)
        _cache_painel[chave] = (img.tobytes(), W, H)
    return _cache_painel[chave]


_ilustracoes = {}


def ilustracao(nome):
    """Carrega a ilustração de uma história como TEXTURA (sem mipmap, no tamanho original,
    pra o texto desenhado nela ficar nítido). Devolve (id, largura, altura)."""
    if nome not in _ilustracoes:
        img = Image.open("%s/texturas/%s.jpg" % (PASTA, nome)).convert("RGB").transpose(Image.FLIP_TOP_BOTTOM)
        tid = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, tid)
        glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, img.width, img.height, 0, GL_RGB, GL_UNSIGNED_BYTE, img.tobytes())
        _ilustracoes[nome] = (tid, img.width, img.height)
    return _ilustracoes[nome]


def desenhar_ilustracao(nome):
    """Escurece a tela e desenha a ilustração num retângulo com textura (projeção ortográfica em pixels)."""
    tid, w, h = ilustracao(nome)
    larg = LARGURA - 100
    alt = larg * h / w
    x0, y0 = (LARGURA - larg) / 2, (ALTURA - alt) / 2 + 12
    glMatrixMode(GL_PROJECTION); glPushMatrix(); glLoadIdentity()
    glOrtho(0, LARGURA, 0, ALTURA, -1, 1)               # 1 unidade = 1 pixel
    glMatrixMode(GL_MODELVIEW); glPushMatrix(); glLoadIdentity()
    glMatrixMode(GL_TEXTURE); glLoadIdentity(); glMatrixMode(GL_MODELVIEW)
    glDisable(GL_TEXTURE_2D)
    glColor4f(0, 0, 0, 0.65)                            # véu escuro sobre o jogo
    glBegin(GL_QUADS)
    glVertex2f(0, 0); glVertex2f(LARGURA, 0); glVertex2f(LARGURA, ALTURA); glVertex2f(0, ALTURA)
    glEnd()
    glEnable(GL_TEXTURE_2D)
    glBindTexture(GL_TEXTURE_2D, tid)
    glColor4f(1, 1, 1, 1)
    glBegin(GL_QUADS)
    glTexCoord2f(0, 0); glVertex2f(x0, y0)
    glTexCoord2f(1, 0); glVertex2f(x0 + larg, y0)
    glTexCoord2f(1, 1); glVertex2f(x0 + larg, y0 + alt)
    glTexCoord2f(0, 1); glVertex2f(x0, y0 + alt)
    glEnd()
    glDisable(GL_TEXTURE_2D)
    glPopMatrix(); glMatrixMode(GL_PROJECTION); glPopMatrix(); glMatrixMode(GL_MODELVIEW)


# ---------------------------------------------------------------------
# PROGRAMA
# ---------------------------------------------------------------------
def lerp(a, b, t):
    return a + (b - a) * t


def lerp3(a, b, t):
    return [lerp(a[i], b[i], t) for i in range(3)]


def iniciar_gl():
    glEnable(GL_DEPTH_TEST)                   # z-buffer
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)                       # sol
    glEnable(GL_NORMALIZE)                    # normais continuam com tamanho 1 após glScale
    glShadeModel(GL_SMOOTH)                   # sombreamento de Gouraud (cor interpolada)
    glLightModeli(GL_LIGHT_MODEL_TWO_SIDE, GL_TRUE)              # o lado de dentro das casas também é iluminado
    glLightModeli(GL_LIGHT_MODEL_LOCAL_VIEWER, GL_TRUE)          # brilho especular depende de onde está o olho
    glLightModeli(GL_LIGHT_MODEL_COLOR_CONTROL, GL_SEPARATE_SPECULAR_COLOR)  # brilho branco por cima da textura
    glTexEnvi(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE)  # cor final = textura × iluminação
    glEnable(GL_FOG)
    glFogi(GL_FOG_MODE, GL_EXP)
    glFogf(GL_FOG_DENSITY, 0.011)
    glHint(GL_PERSPECTIVE_CORRECTION_HINT, GL_NICEST)
    glEnable(GL_POINT_SMOOTH)


def compilar_cena():
    """Tudo que não se mexe vai pra DISPLAY LISTS: os comandos ficam gravados na placa de vídeo.
    São duas listas: o TERRENO (recebe sombra) e os OBJETOS (projetam sombra)."""
    terreno = glGenLists(1)
    glNewList(terreno, GL_COMPILE)
    obj.chao()
    obj.morros()
    glEndList()

    lista = glGenLists(1)
    glNewList(lista, GL_COMPILE)
    obj.palicada()

    def colocar(pos, desenho, escala=1.0, giro=None):
        glPushMatrix()
        glTranslatef(pos[0], 0, pos[1])                                          # TRANSLAÇÃO
        glRotatef(virado_pro_centro(*pos) if giro is None else giro, 0, 1, 0)    # ROTAÇÃO
        glScalef(escala, escala, escala)                                         # ESCALA
        desenho()
        glPopMatrix()

    obj.placa()                     # placa de entrada, já na posição do portão
    colocar(MUXIMA, obj.muxima, giro=0)
    for p in OCAS:
        colocar(p, obj.oca)
    colocar(CASA_FARINHA, obj.casa_farinha)
    colocar(POCO, obj.poco)
    colocar(ATALAIA, obj.atalaia)
    colocar(FOGUEIRA, obj.fogueira_base, giro=0)
    colocar(LAGOA, obj.lagoa_margem, giro=0)
    rnd = random.Random(7)
    for p in ARVORES:
        colocar(p, obj.arvore, rnd.uniform(0.85, 1.35), rnd.uniform(0, 360))
    for p in COQUEIROS:
        colocar(p, obj.coqueiro, rnd.uniform(0.9, 1.15), rnd.uniform(0, 360))
    glEndList()
    return terreno, lista


# ---------------------------------------------------------------------
# SOMBRA PLANAR: uma matriz que "achata" o objeto no chão na direção do sol
# ---------------------------------------------------------------------
ALTURA_SOMBRA = 0.03       # um pouco acima da terra (0.02) pra não dar z-fighting

def matriz_sombra(luz, h=ALTURA_SOMBRA):
    """Projeta cada ponto P no plano y = h, andando na direção dos raios do sol.
    Raio que passa por P: P - k·L. Ele toca o plano quando P.y - k·L.y = h  ->  k = (P.y - h) / L.y
      x' = x - (Lx/Ly)·(y - h)      y' = h      z' = z - (Lz/Ly)·(y - h)
    Escrito como matriz 4x4 (o OpenGL guarda por COLUNAS):"""
    lx, ly, lz = luz
    a, b = lx / ly, lz / ly
    return [1, 0, 0, 0,          # coluna do x
            -a, 0, -b, 0,        # coluna do y: o y vira deslocamento em x e z, e some do y
            0, 0, 1, 0,          # coluna do z
            a * h, h, b * h, 1]  # coluna da translação


def desenhar_sombras(objetos, desenhar_animados, luz, forca):
    """1) desenha os objetos ACHATADOS só no STENCIL (sem cor): marca os pixels de sombra;
    2) pinta um retângulo preto transparente na tela inteira, mas só onde o stencil marcou.
    Assim cada pixel escurece UMA vez só, mesmo onde duas sombras se cruzam."""
    glClear(GL_STENCIL_BUFFER_BIT)
    glEnable(GL_STENCIL_TEST)
    glStencilFunc(GL_ALWAYS, 1, 0xFF)
    glStencilOp(GL_KEEP, GL_KEEP, GL_REPLACE)       # passou no teste de profundidade -> marca 1
    glColorMask(GL_FALSE, GL_FALSE, GL_FALSE, GL_FALSE)
    glDepthMask(GL_FALSE)
    glDisable(GL_LIGHTING)
    glEnable(GL_POLYGON_OFFSET_FILL)
    glPolygonOffset(-1, -1)                          # puxa a sombra um pouquinho pra frente do chão
    glPushMatrix()
    glMultMatrixf(matriz_sombra(luz))                # <- a transformação que achata tudo
    glCallList(objetos)
    desenhar_animados()
    glPopMatrix()
    glDisable(GL_POLYGON_OFFSET_FILL)
    glColorMask(GL_TRUE, GL_TRUE, GL_TRUE, GL_TRUE)

    # retângulo na tela inteira, só onde stencil == 1
    glStencilFunc(GL_EQUAL, 1, 0xFF)
    glStencilOp(GL_KEEP, GL_KEEP, GL_KEEP)
    glDisable(GL_TEXTURE_2D); glDisable(GL_DEPTH_TEST); glDisable(GL_FOG)
    glEnable(GL_BLEND); glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glMatrixMode(GL_PROJECTION); glPushMatrix(); glLoadIdentity()
    glMatrixMode(GL_MODELVIEW); glPushMatrix(); glLoadIdentity()
    glColor4f(0, 0, 0, forca)
    glBegin(GL_QUADS)
    glVertex2f(-1, -1); glVertex2f(1, -1); glVertex2f(1, 1); glVertex2f(-1, 1)
    glEnd()
    glPopMatrix(); glMatrixMode(GL_PROJECTION); glPopMatrix(); glMatrixMode(GL_MODELVIEW)
    glColor4f(1, 1, 1, 1)
    glDisable(GL_BLEND); glDisable(GL_STENCIL_TEST)
    glEnable(GL_DEPTH_TEST); glDepthMask(GL_TRUE); glEnable(GL_LIGHTING); glEnable(GL_FOG)


# Roteiro do modo demonstração (python main.py --demo): câmera e teclas automáticas
ROTEIRO_CAMERA = [  # (tempo s, x, z, yaw em graus, pitch)
    (0, 0, 40, 0, -0.04), (3.5, 0, 31, 0, -0.04), (6, 0, 31, 0, -0.04), (9, 0, 21, 0, -0.04),
    (12, 10, 15, 25, -0.15), (13.5, 12, 12.6, 0, -0.45), (20.5, 12, 12.6, 0, -0.45),
    (23, 7, 12, -20, -0.1), (30, 7, 12, -32, -0.06), (33, 9, 4, 14, -0.05), (36, 20, -3, 57, -0.05),
    (39, 13.67, -13.67, 45, 0.15), (41.5, 13.67, -13.67, 45, 0.1), (45, 13.67, -13.67, -135, -0.35),
    (50, 13.67, -13.67, -165, -0.3), (52, 13.67, -13.67, -165, -0.3)]
ROTEIRO_TECLAS = [(4.0, "E"), (14.0, "F"), (23.5, "N"), (26.0, "L"), (39.3, "T"), (46.0, "D")]


def camera_do_roteiro(t):
    for (t0, *a), (t1, *b) in zip(ROTEIRO_CAMERA, ROTEIRO_CAMERA[1:]):
        if t0 <= t <= t1:
            k = (t - t0) / (t1 - t0)
            k = k * k * (3 - 2 * k)                    # suaviza o começo e o fim de cada trecho
            return [lerp(a[i], b[i], k) for i in range(4)]
    return ROTEIRO_CAMERA[-1][1:]


def main():
    teste = "--teste" in sys.argv
    demo = "--demo" in sys.argv
    # ---------- janela (GLFW) ----------
    if not glfw.init():
        print("Não foi possível iniciar o GLFW"); return
    glfw.window_hint(glfw.RESIZABLE, glfw.FALSE)
    glfw.window_hint(glfw.STENCIL_BITS, 8)      # stencil buffer: usado pras sombras
    janela = glfw.create_window(LARGURA, ALTURA, "Quilombo dos Palmares - OpenGL", None, None)
    glfw.make_context_current(janela)
    glfw.swap_interval(1)                       # sincroniza com o monitor (~60 quadros/s)

    # Retina / HiDPI: framebuffer pode ser 2× a janela; o HUD precisa desenhar nesse tamanho
    global UI_SCALE, FB_W, FB_H
    ww, wh = glfw.get_window_size(janela)
    FB_W, FB_H = glfw.get_framebuffer_size(janela)
    UI_SCALE = FB_W / float(ww) if ww else 1.0
    glViewport(0, 0, FB_W, FB_H)

    # Teclado e mouse chegam por CALLBACKS: o GLFW chama essas funções a cada evento,
    # e elas guardam o evento numa fila que o laço principal processa.
    eventos = []
    glfw.set_key_callback(janela, lambda w, tecla, sc, acao, mods:
                          eventos.append(("tecla", tecla)) if acao == glfw.PRESS else None)
    glfw.set_scroll_callback(janela, lambda w, dx, dy: eventos.append(("roda", dy)))
    mouse_ant = [None]

    def mouse_moveu(w, mx, my):
        if mouse_ant[0] is not None:
            eventos.append(("mouse", mx - mouse_ant[0][0], my - mouse_ant[0][1]))
        mouse_ant[0] = (mx, my)
    glfw.set_cursor_pos_callback(janela, mouse_moveu)

    # Tamanhos lógicos um pouco maiores (bom pra vídeo); × UI_SCALE no Retina
    fonte = carregar_fonte(max(18, int(round(22 * UI_SCALE))))
    fonte_grande = carregar_fonte(max(22, int(round(30 * UI_SCALE))), negrito=True)
    iniciar_gl()
    for nome in ("grama", "terra", "palha", "reboco", "casca", "madeira", "folhas", "pedra", "agua"):
        textura(nome)
    terreno, cena = compilar_cena()

    cam = Camera()
    if not teste and not demo:
        glfw.set_input_mode(janela, glfw.CURSOR, glfw.CURSOR_DISABLED)   # esconde e prende o mouse
    t_anterior = time.perf_counter()
    t = 0.0

    # estados das interações
    angulo_portao, portao_alvo = 0.0, 0.0      # E
    fogo, fogo_alvo = 0.0, 0.0                 # L
    dia, dia_alvo = 1.0, 1.0                   # N
    # POÇO (F): máquina de estados do balde
    #   em_cima_vazio → descendo → enchendo → subindo → em_cima_cheio → despejando → em_cima_vazio
    poco_estado, balde_h, balde_cheio, balde_incl, poco_tempo = "em_cima_vazio", 1.0, False, 0.0, 0.0
    ondas, gotas = [], []
    historia = None                            # índice da história aberta (None = fechada)
    proxima_historia = 0
    subida, subida_alvo = 0.0, 0.0             # E na escada da atalaia (0 = embaixo, 1 = em cima)
    giro_atalaia = virado_pro_centro(*ATALAIA)
    pe_escada = local_para_mundo(ATALAIA, giro_atalaia, *obj.ATALAIA_PE)
    topo_atalaia = local_para_mundo(ATALAIA, giro_atalaia, *obj.ATALAIA_TOPO)

    # MISSÃO "Um dia no Quilombo": tarefas que vão sendo marcadas
    tarefas = ["Abrir o portão e entrar no quilombo (E)",
               "Buscar água no poço (F)",
               "Esperar anoitecer (N)",
               "Acender a fogueira à noite (L)",
               "Subir na atalaia e vigiar o quilombo (E)"]
    feito = [False] * len(tarefas)
    tempo_fim = None
    faiscas = []
    rnd = random.Random()
    estrelas = [(math.cos(a) * math.cos(e) * 180, math.sin(e) * 180, math.sin(a) * math.cos(e) * 180)
                for a, e in ((rnd.uniform(0, 6.283), rnd.uniform(0.08, 1.5)) for _ in range(400))]

    quadros_teste = [
        dict(x=0, z=38, yaw=0, pitch=-0.05),
        dict(x=8, z=18, yaw=math.radians(-24), pitch=-0.06, portao=100, fogo=1),
        dict(x=4, z=13, yaw=0, pitch=-0.12, portao=100, fogo=1, dia=0),
        dict(x=-6, z=12, yaw=math.radians(-120), pitch=-0.15, portao=100),
        dict(x=12, z=12.4, yaw=0, pitch=-0.5, portao=100, balde=1),
        dict(x=-7.3, z=-2.2, yaw=math.radians(-73), pitch=-0.05, portao=100),
        dict(x=-11.8, z=-3.6, yaw=math.radians(-73), pitch=0.1, portao=100),
        dict(x=0, z=-7.5, yaw=0, pitch=0.05, portao=100),
        dict(x=12.5, z=-11.5, yaw=math.radians(40), pitch=0.25, portao=100),
        dict(x=16, z=-16, yaw=math.radians(-140), pitch=-0.3, portao=100, fogo=1, altura=7.7),
        dict(x=0, z=31, yaw=0, pitch=0.3),
        dict(x=0, z=19, yaw=math.pi, pitch=0.25, portao=100),
        dict(x=5, z=30, yaw=math.radians(-35), pitch=0.2),
        dict(x=0, z=28, yaw=0, pitch=0.35, portao=100),
        dict(x=-17, z=13.5, yaw=0, pitch=0.3, portao=100),
        dict(x=4, z=11, yaw=0, pitch=-0.1, portao=100, fogo=1, dia=0, historia=7),
        dict(orto=True, portao=100),
    ]
    quadro = 0

    while True:
        agora = time.perf_counter()
        dt = 1 / 25 if demo else min(agora - t_anterior, 0.05)
        t_anterior = agora
        t += dt
        perto_portao = math.hypot(cam.x, cam.z - obj.RAIO_MURO) < 7
        perto_fogo = math.hypot(cam.x - FOGUEIRA[0], cam.z - FOGUEIRA[1]) < 6
        perto_poco = math.hypot(cam.x - POCO[0], cam.z - POCO[1]) < 4
        # roda de histórias: perto da fogueira acesa, de noite
        na_roda = perto_fogo and fogo_alvo > 0 and dia_alvo < 0.5 and not cam.orto
        if not na_roda:
            historia = None
        perto_escada = math.hypot(cam.x - pe_escada[0], cam.z - pe_escada[1]) < 2.5 or subida_alvo > 0

        glfw.poll_events()
        if glfw.window_should_close(janela):
            glfw.terminate(); return
        for ev in eventos:
            if ev[0] == "tecla":
                tecla = ev[1]
                if tecla == glfw.KEY_ESCAPE:
                    glfw.terminate(); return
                if tecla == glfw.KEY_E and perto_escada and not cam.orto:
                    subida_alvo = 0.0 if subida_alvo > 0 else 1.0          # sobe/desce a atalaia
                elif tecla == glfw.KEY_E and perto_portao:
                    portao_alvo = 0.0 if portao_alvo > 0 else 100.0        # abre/fecha o portão
                if tecla == glfw.KEY_L and perto_fogo:
                    fogo_alvo = 0.0 if fogo_alvo > 0 else 1.0              # acende/apaga a fogueira
                if tecla == glfw.KEY_H and na_roda:                        # histórias da fogueira
                    if historia is None:
                        historia = proxima_historia
                    elif historia + 1 < len(HISTORIAS):
                        historia += 1
                    else:
                        historia = None                                    # acabou: fecha
                    proxima_historia = 0 if historia is None else (historia + 1) % len(HISTORIAS)
                if tecla == glfw.KEY_F and perto_poco:
                    if poco_estado == "em_cima_vazio":
                        poco_estado = "descendo"                           # solta o balde
                    elif poco_estado == "em_cima_cheio":
                        poco_estado, poco_tempo = "despejando", 0.0        # despeja a água
                if tecla == glfw.KEY_N:
                    dia_alvo = 0.0 if dia_alvo > 0.5 else 1.0              # dia/noite
                if tecla == glfw.KEY_P:
                    cam.orto = not cam.orto                                 # perspectiva/ortográfica
            elif ev[0] == "mouse" and not cam.orto and not demo and not teste:
                dx, dy = ev[1], ev[2]
                cam.yaw += dx * 0.0025                                      # azimute
                cam.pitch = max(-1.4, min(1.4, cam.pitch - dy * 0.0025))   # elevação, com limite
            elif ev[0] == "roda":
                if cam.orto:
                    cam.tam_orto = max(12, min(90, cam.tam_orto - ev[1] * 4))
                else:
                    cam.fov = max(25, min(100, cam.fov - ev[1] * 4))      # zoom = muda o ângulo de visão
        eventos.clear()

        if demo:
            cam.x, cam.z, yaw, cam.pitch = camera_do_roteiro(t)
            cam.yaw = math.radians(yaw)
            for (tt, tecla) in ROTEIRO_TECLAS:
                if tt <= t < tt + dt:
                    if tecla == "E": portao_alvo = 100.0
                    if tecla == "F": poco_estado = "descendo"
                    if tecla == "N": dia_alvo = 0.0
                    if tecla == "L": fogo_alvo = 1.0
                    if tecla == "T": subida_alvo = 1.0
                    if tecla == "D": dia_alvo = 1.0

        apertada = lambda k: 1 if glfw.get_key(janela, k) == glfw.PRESS else 0
        frente = apertada(glfw.KEY_W) - apertada(glfw.KEY_S)
        lado = apertada(glfw.KEY_D) - apertada(glfw.KEY_A)
        correr = apertada(glfw.KEY_LEFT_SHIFT)
        if not cam.orto and (frente or lado) and subida == 0 and subida_alvo == 0:
            cam.mover(frente, lado, dt, correr, angulo_portao > 80)

        if teste:                                   # modo de teste: posições fixas e captura de tela
            q = quadros_teste[quadro]
            cam.orto = q.get("orto", False)
            if not cam.orto:
                cam.x, cam.z, cam.yaw, cam.pitch = q["x"], q["z"], q["yaw"], q["pitch"]
            angulo_portao = portao_alvo = q.get("portao", 0)
            fogo = fogo_alvo = q.get("fogo", 0)
            dia = dia_alvo = q.get("dia", 1)
            historia = q.get("historia")
            if q.get("balde"):
                poco_estado, balde_h, balde_cheio = "em_cima_cheio", 1.0, True
            if "altura" in q:
                subida = subida_alvo = 1.0
                pe_escada = topo_atalaia = (q["x"], q["z"])
            else:
                subida = subida_alvo = 0.0

        # animações suaves (aproximação exponencial do valor alvo)
        angulo_portao += (portao_alvo - angulo_portao) * min(1, dt * 2.5)
        fogo += (fogo_alvo - fogo) * min(1, dt * 3)
        dia += (dia_alvo - dia) * min(1, dt * 1.2)
        # poço: cada estado anima uma coisa
        poco_tempo += dt
        if poco_estado == "descendo":
            balde_h = max(0.0, balde_h - dt * 0.5)                         # desce em 2 s
            if balde_h == 0.0:
                poco_estado, poco_tempo = "enchendo", 0.0
                ondas.append(t)                                            # tchibum: primeira onda
        elif poco_estado == "enchendo":
            if poco_tempo > 0.3 and len(ondas) < 3:
                ondas.append(t)
            if poco_tempo > 1.0:
                poco_estado, balde_cheio = "subindo", True
        elif poco_estado == "subindo":
            balde_h = min(1.0, balde_h + dt * 0.4)                         # sobe mais devagar (está pesado)
            if rnd.random() < dt * 6:                                      # pinga água do fundo
                gotas.append([rnd.uniform(-0.12, 0.12), obj.altura_balde(balde_h), rnd.uniform(-0.12, 0.12), 0.0])
            if balde_h == 1.0:
                poco_estado = "em_cima_cheio"
        elif poco_estado == "despejando":
            balde_incl = min(110.0, poco_tempo * 160) if poco_tempo < 1.4 else max(0.0, 110 - (poco_tempo - 1.4) * 160)
            if 0.5 < poco_tempo < 1.4:                                     # água caindo pra fora
                for _ in range(3):
                    gotas.append([-0.3 + rnd.uniform(-0.05, 0.05), obj.altura_balde(1.0) + 0.3,
                                  rnd.uniform(-0.1, 0.1), 0.0, -1.2])   # 5º valor: velocidade em x
            if poco_tempo > 1.0:
                balde_cheio = False
            if poco_tempo > 2.1:
                poco_estado, balde_incl = "em_cima_vazio", 0.0
        ondas = [o for o in ondas if t - o < 1.2]
        for g in gotas:                                                    # queda livre: v += g·dt, y += v·dt
            g[3] -= 9.8 * dt
            g[1] += g[3] * dt
            if len(g) > 4:
                g[0] += g[4] * dt
        gotas = [g for g in gotas if g[1] > (obj.POCO_AGUA if math.hypot(g[0], g[2]) < 0.95 else 0.9)]

        # subir/descer a escada: velocidade constante (≈ 1,7 s), e a câmera é TRANSLADADA
        # do pé da escada até a plataforma (x, z e altura interpolados)
        if subida != subida_alvo:
            passo = dt * 0.6
            subida = min(subida + passo, 1.0) if subida_alvo > subida else max(subida - passo, 0.0)
        if subida > 0:
            cam.x = lerp(pe_escada[0], topo_atalaia[0], subida)
            cam.z = lerp(pe_escada[1], topo_atalaia[1], subida)
            cam.altura = lerp(ALTURA_OLHOS, obj.ATALAIA_ALTURA + ALTURA_OLHOS, subida)
        else:
            cam.altura = ALTURA_OLHOS

        # verifica as tarefas
        if angulo_portao > 80 and math.hypot(cam.x, cam.z) < obj.RAIO_MURO - 2:
            feito[0] = True
        if poco_estado == "em_cima_cheio":
            feito[1] = True
        if dia_alvo < 0.5:
            feito[2] = True
        if fogo_alvo > 0.5 and dia < 0.3:
            feito[3] = True
        if subida > 0.98:
            feito[4] = True
        if all(feito) and tempo_fim is None:
            tempo_fim = t

        # ---------- céu, neblina e luzes dependem do "dia" ----------
        ceu = lerp3((0.04, 0.05, 0.09), (0.66, 0.72, 0.80), dia)   # cor do horizonte (neblina)
        glClearColor(ceu[0], ceu[1], ceu[2], 1)
        glFogfv(GL_FOG_COLOR, ceu + [1])
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT | GL_STENCIL_BUFFER_BIT)

        cam.projecao()
        cam.aplicar()

        # SOL: luz DIRECIONAL (w = 0 → raios paralelos, vindo dessa direção)
        sol_dir = (0.45, lerp(0.35, 0.8, dia), 0.35)
        glLightfv(GL_LIGHT0, GL_POSITION, list(sol_dir) + [0.0])
        glLightfv(GL_LIGHT0, GL_DIFFUSE, lerp3((0.10, 0.12, 0.25), (1.0, 0.95, 0.85), dia) + [1])
        glLightfv(GL_LIGHT0, GL_SPECULAR, lerp3((0.1, 0.1, 0.2), (1.0, 1.0, 0.95), dia) + [1])
        glLightModelfv(GL_LIGHT_MODEL_AMBIENT, lerp3((0.09, 0.10, 0.18), (0.35, 0.38, 0.42), dia) + [1])

        # FOGUEIRA: luz PONTUAL (w = 1), que enfraquece com a distância (atenuação)
        if fogo > 0.02:
            glEnable(GL_LIGHT1)
            tremor = 0.85 + 0.15 * math.sin(t * 13) * math.sin(t * 7.3)
            i = fogo * tremor * 2.2
            glLightfv(GL_LIGHT1, GL_POSITION, [FOGUEIRA[0], 1.2, FOGUEIRA[1], 1.0])
            glLightfv(GL_LIGHT1, GL_DIFFUSE, [1.0 * i, 0.55 * i, 0.2 * i, 1])
            glLightfv(GL_LIGHT1, GL_SPECULAR, [0.6 * i, 0.4 * i, 0.2 * i, 1])
            glLightf(GL_LIGHT1, GL_CONSTANT_ATTENUATION, 1.0)
            glLightf(GL_LIGHT1, GL_LINEAR_ATTENUATION, 0.08)
            glLightf(GL_LIGHT1, GL_QUADRATIC_ATTENUATION, 0.02)
        else:
            glDisable(GL_LIGHT1)

        # ---------- estrelas e sol/lua (sem neblina, bem longe) ----------
        glDisable(GL_FOG)
        glDisable(GL_LIGHTING)
        glDisable(GL_TEXTURE_2D)
        glDepthMask(GL_FALSE)
        # céu com foto (sky dome), centrado na câmera e girado pra claridade da foto ficar do lado do sol
        glPushMatrix()
        glTranslatef(cam.x, 0, cam.z)
        obj.abobada_celeste(dia, ceu, GIRO_CEU)
        glPopMatrix()
        glDisable(GL_TEXTURE_2D)
        if dia < 0.9:
            glEnable(GL_BLEND)
            glPointSize(2)
            glColor4f(1, 1, 1, 1 - dia)
            glBegin(GL_POINTS)
            for e in estrelas:
                glVertex3f(cam.x + e[0], e[1], cam.z + e[2])
            glEnd()
            glDisable(GL_BLEND)
        if dia < 0.6:                    # lua (de dia o sol já está na foto do céu)
            glPushMatrix()
            n = math.sqrt(sum(c * c for c in sol_dir))
            glTranslatef(cam.x + sol_dir[0] / n * 200, sol_dir[1] / n * 200, cam.z + sol_dir[2] / n * 200)
            glEnable(GL_BLEND)
            glColor4f(0.88, 0.9, 0.97, min(1.0, (0.6 - dia) * 3))
            obj.esfera(6, 16)
            glDisable(GL_BLEND)
            glPopMatrix()
        glColor3f(1, 1, 1)
        glDepthMask(GL_TRUE)
        glEnable(GL_LIGHTING)
        glEnable(GL_FOG)

        # ---------- cena ----------
        if cam.orto:
            glDisable(GL_FOG)          # vista de cima a 150 m: com neblina ficaria tudo branco
        glCallList(terreno)
        # sombras do sol no chão (mais fortes de dia, quase somem à noite)
        desenhar_sombras(cena, lambda: obj.portao(angulo_portao), sol_dir, 0.08 + 0.3 * dia)
        if cam.orto:
            glDisable(GL_FOG)
        glCallList(cena)
        obj.portao(angulo_portao)
        glPushMatrix()                                  # partes animadas do poço: mesma transformação do poço
        glTranslatef(POCO[0], 0, POCO[1])
        glRotatef(virado_pro_centro(*POCO), 0, 1, 0)
        # o sarilho gira o quanto a corda desenrola: ângulo = comprimento / raio (arco s = r·θ)
        corda = (1.0 - balde_h) * 0.95
        obj.sarilho(math.degrees(corda / obj.RAIO_SARILHO))
        obj.balde(balde_h, balde_cheio, balde_incl)
        obj.ondas_e_gotas(ondas, gotas, t)
        glPopMatrix()
        glPushMatrix()
        glTranslatef(LAGOA[0], 0, LAGOA[1])
        obj.agua(t)
        glPopMatrix()
        glMatrixMode(GL_TEXTURE); glLoadIdentity(); glMatrixMode(GL_MODELVIEW)

        # chama e faíscas (partículas)
        if fogo > 0.02:
            glPushMatrix()
            glTranslatef(FOGUEIRA[0], 0, FOGUEIRA[1])
            obj.chama(t, fogo)
            glPopMatrix()
            for _ in range(2):
                faiscas.append([FOGUEIRA[0] + rnd.uniform(-0.3, 0.3), 0.6, FOGUEIRA[1] + rnd.uniform(-0.3, 0.3),
                                rnd.uniform(-0.3, 0.3), rnd.uniform(1.5, 3.0), rnd.uniform(-0.3, 0.3), 1.2])
        for f in faiscas:                       # movimento: posição += velocidade × dt
            f[0] += f[3] * dt; f[1] += f[4] * dt; f[2] += f[5] * dt; f[6] -= dt
        faiscas = [f for f in faiscas if f[6] > 0]
        if faiscas:
            glDisable(GL_LIGHTING); glDisable(GL_TEXTURE_2D)
            glEnable(GL_BLEND); glBlendFunc(GL_SRC_ALPHA, GL_ONE); glDepthMask(GL_FALSE)
            glPointSize(3)
            glBegin(GL_POINTS)
            for f in faiscas:
                glColor4f(1.0, 0.6, 0.15, f[6] / 1.2)
                glVertex3f(f[0], f[1], f[2])
            glEnd()
            glDepthMask(GL_TRUE); glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA); glDisable(GL_BLEND)
            glColor4f(1, 1, 1, 1); glEnable(GL_LIGHTING)

        # ---------- HUD ----------
        glDisable(GL_LIGHTING); glDisable(GL_TEXTURE_2D); glDisable(GL_DEPTH_TEST); glDisable(GL_FOG)
        glEnable(GL_BLEND)
        texto(16, 14, "Quilombo dos Palmares", fonte_grande, (255, 225, 140))
        linhas = ["WASD andar | Shift correr | Mouse olhar | Roda zoom",
                  "E portão | F poço | L fogueira | H história | N dia/noite | P projeção | ESC sair",
                  "Projeção: %s   %s" % ("ORTOGRÁFICA (tamanho %d m)" % cam.tam_orto if cam.orto
                                          else "PERSPECTIVA (fov %d°)" % cam.fov,
                                          "Noite" if dia_alvo < 0.5 else "Dia")]
        lh = 28  # espaçamento lógico das linhas do HUD
        for k, s in enumerate(linhas):
            texto(16, 48 + k * lh, s, fonte)
        aviso = ""
        if perto_portao and not cam.orto:
            aviso = "Aperte E para %s o portão" % ("fechar" if portao_alvo > 0 else "abrir")
        elif na_roda:
            aviso = "" if historia is not None else "Aperte H para ouvir uma história  |  L apaga"
        elif perto_fogo and not cam.orto:
            aviso = "Aperte L para %s a fogueira" % ("apagar" if fogo_alvo > 0 else "acender")
            if dia_alvo > 0.5:
                aviso += "  (à noite tem história!)"
        elif perto_escada and not cam.orto:
            aviso = ("Atalaia: vigiando o quilombo  |  E para descer" if subida_alvo > 0
                     else "Aperte E para subir na atalaia")
        elif perto_poco and not cam.orto:
            aviso = {"em_cima_vazio": "Aperte F para descer o balde",
                     "descendo": "Descendo o balde...", "enchendo": "Enchendo de água...",
                     "subindo": "Puxando o balde...", "em_cima_cheio": "Balde cheio! F para despejar",
                     "despejando": "Despejando..."}[poco_estado]
        if aviso:
            # getlength já está em pixels da fonte (escalada); converter de volta pra coords lógicas
            texto(LARGURA // 2 - fonte_grande.getlength(aviso) / (2 * UI_SCALE),
                  ALTURA - 90, aviso, fonte_grande, (255, 240, 180))
        # lista de tarefas (canto direito)
        texto(LARGURA - 420, 14, "Um dia no Quilombo", fonte_grande, (255, 225, 140))
        for k, s in enumerate(tarefas):
            if feito[k]:
                texto(LARGURA - 420, 48 + k * lh, "[x] " + s, fonte, (150, 230, 150))
            else:
                texto(LARGURA - 420, 48 + k * lh, "[  ] " + s, fonte)
        if t < 7 and not teste:
            texto(LARGURA // 2 - 260, ALTURA // 2 - 60, "Chegue ao quilombo e cumpra as tarefas do dia",
                  fonte_grande, (255, 240, 180))
        if tempo_fim is not None and t - tempo_fim < 10:
            texto(LARGURA // 2 - 190, ALTURA // 2 - 60,
                  "Missão cumprida em %d min %02d s!" % (tempo_fim // 60, tempo_fim % 60),
                  fonte_grande, (150, 240, 150))
        if historia is not None:
            imagem = HISTORIAS[historia][3]
            if imagem:                                   # história ilustrada: a imagem já tem o texto
                desenhar_ilustracao(imagem)
                n = len(HISTORIAS)
                rodape = ("H: próxima   (%d/%d)" if historia + 1 < n else "H: fechar   (%d/%d)") % (historia + 1, n)
                texto(LARGURA // 2 - fonte.getlength(rodape) / (2 * UI_SCALE),
                      ALTURA - 30, rodape, fonte, (255, 225, 160))
            else:                                        # sem ilustração: painel de texto
                dados, w, h = painel_historia(historia, fonte_grande, fonte)
                glWindowPos2d((FB_W - w) // 2, int(40 * UI_SCALE))
                glDrawPixels(w, h, GL_RGBA, GL_UNSIGNED_BYTE, dados)
        glDisable(GL_BLEND); glEnable(GL_DEPTH_TEST); glEnable(GL_LIGHTING); glEnable(GL_FOG)

        glfw.swap_buffers(janela)          # double buffering: mostra o quadro pronto

        if demo:                                    # grava cada quadro (depois vira vídeo com ffmpeg)
            dados = glReadPixels(0, 0, FB_W, FB_H, GL_RGB, GL_UNSIGNED_BYTE)
            img = Image.frombytes("RGB", (FB_W, FB_H), dados).transpose(Image.FLIP_TOP_BOTTOM)
            img.save("demo_%05d.png" % int(round(t * 25)))
            if t > 51.5:
                glfw.terminate(); return

        if teste:
            dados = glReadPixels(0, 0, FB_W, FB_H, GL_RGB, GL_UNSIGNED_BYTE)
            img = Image.frombytes("RGB", (FB_W, FB_H), dados).transpose(Image.FLIP_TOP_BOTTOM)
            img.save("teste_%d.png" % quadro)
            quadro += 1
            if quadro >= len(quadros_teste):
                glfw.terminate(); return


if __name__ == "__main__":
    main()
