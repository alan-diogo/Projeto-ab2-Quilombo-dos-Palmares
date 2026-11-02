# =====================================================================
# OBJETOS DA CENA — cada função modela UM objeto a partir das primitivas.
# =====================================================================
# Regra de todas as funções: o objeto é montado em volta da origem (coordenadas
# LOCAIS) e quem chama coloca ele no mundo com glTranslate / glRotate / glScale.
# glPushMatrix() salva a matriz atual; glPopMatrix() volta pra ela. Assim a
# transformação de uma peça não "vaza" pra próxima.

import math
import random
from OpenGL.GL import *
from primitivas import *

RAIO_MURO = 25.0        # raio da paliçada (metros)
MEIA_ABERTURA = 2.2     # meia largura do vão do portão (metros)


# ---------------------------------------------------------------------
# 1. CHÃO
# ---------------------------------------------------------------------
def chao():
    mat_chao()
    usar_textura("grama", 60, 60)              # textura repetida 60x: não fica esticada
    disco(160, 48, 4)
    glPushMatrix()
    glTranslatef(0, 0.02, 0)                   # 2 cm acima: sem z-fighting com a grama
    usar_textura("terra", 12, 12)
    disco(RAIO_MURO, 48, 4)
    glPopMatrix()


def morros():
    """Morros ao longe: esferas ACHATADAS (escala não uniforme) meio enterradas."""
    mat_folhas()
    usar_textura("grama", 6, 3)
    rnd = random.Random(5)
    for i in range(14):
        a = 2 * math.pi * i / 14 + rnd.uniform(-0.1, 0.1)
        r = rnd.uniform(85, 110)
        glPushMatrix()
        glTranslatef(math.cos(a) * r, -6, math.sin(a) * r)
        glScalef(rnd.uniform(1.5, 2.5), rnd.uniform(0.5, 0.8), rnd.uniform(1.2, 2.0))
        esfera(14, 20)
        glPopMatrix()


# ---------------------------------------------------------------------
# 2. PALIÇADA — muro de varas em círculo, com o vão do portão no lado +Z
# ---------------------------------------------------------------------
def palicada():
    rnd = random.Random(11)
    mat_madeira()
    usar_textura("casca", 1, 2)
    meio_vao = MEIA_ABERTURA / RAIO_MURO                 # meio vão em radianos
    n = int(2 * math.pi * RAIO_MURO / 0.28)              # uma vara a cada 28 cm
    for i in range(n):
        a = 2 * math.pi * i / n
        if abs(math.atan2(math.sin(a - math.pi / 2), math.cos(a - math.pi / 2))) < meio_vao:
            continue                                     # aqui é o portão
        h = rnd.uniform(2.6, 3.2)
        glPushMatrix()
        glTranslatef(math.cos(a) * RAIO_MURO, 0, math.sin(a) * RAIO_MURO)   # TRANSLAÇÃO pro círculo
        glRotatef(rnd.uniform(-3, 3), 1, 0, 0)                              # ROTAÇÃO: leve inclinação
        cilindro(0.11, 0.08, h, 6)
        glTranslatef(0, h, 0)
        cilindro(0.08, 0.0, 0.3, 6, tampa=False)                            # ponta afiada (cone)
        glPopMatrix()
    # travessas horizontais (por dentro), em trechos retos de 10 graus
    usar_textura("madeira", 2, 1)
    passos = 36
    for j in range(passos):
        a0 = 2 * math.pi * j / passos
        a1 = a0 + 2 * math.pi / passos
        meio = (a0 + a1) / 2
        if abs(math.atan2(math.sin(meio - math.pi / 2), math.cos(meio - math.pi / 2))) < meio_vao + 0.1:
            continue
        comp = 2 * RAIO_MURO * math.sin(math.pi / passos)               # corda do trecho
        r = RAIO_MURO - 0.2
        for y in (0.8, 2.0):
            glPushMatrix()
            glTranslatef(math.cos(meio) * r, y, math.sin(meio) * r)
            glRotatef(-math.degrees(meio) - 90, 0, 1, 0)                # tangente ao círculo
            caixa(comp, 0.12, 0.12)
            glPopMatrix()


# ---------------------------------------------------------------------
# 3. PORTÃO — duas folhas, cada uma gira presa no seu PIVÔ (a dobradiça)
# ---------------------------------------------------------------------
def _folha(largura):
    """Uma folha do portão. Origem = dobradiça; a folha se estende para +X."""
    mat_madeira()
    usar_textura("casca", 1, 2)
    n = 8
    for i in range(n):
        x = 0.15 + i * (largura - 0.3) / (n - 1)
        glPushMatrix()
        glTranslatef(x, 0, 0)
        cilindro(0.11, 0.1, 2.9 + (i % 2) * 0.15, 8)
        glPopMatrix()
    usar_textura("madeira", 2, 1)
    for y in (0.6, 2.2):
        glPushMatrix()
        glTranslatef(largura / 2, y, 0.15)
        caixa(largura, 0.15, 0.1)
        glPopMatrix()
    # diagonal: comprimento por PITÁGORAS, inclinação por atan2
    dx, dy = largura - 0.4, 1.6
    glPushMatrix()
    glTranslatef(largura / 2, 1.45, 0.16)
    glRotatef(math.degrees(math.atan2(dy, dx)), 0, 0, 1)
    glTranslatef(0, -0.07, 0)
    caixa(math.hypot(dx, dy), 0.14, 0.1)
    glPopMatrix()


def placa():
    """Placa de entrada em cima do portão: \"QUILOMBO DOS PALMARES\".
    Dois postes sobem dos pilares do portão e seguram uma tábua. A frente da tábua
    é um quadrilátero com a textura placa.jpg (letras entalhadas na madeira)."""
    z = RAIO_MURO
    larg, alt, esp = 5.6, 0.95, 0.14
    y0 = 3.75
    mat_madeira()
    usar_textura("casca", 1, 2)
    for x in (-(larg / 2 + 0.1), larg / 2 + 0.1):   # dois postes do chão até o telhadinho
        glPushMatrix()
        glTranslatef(x, 0, z + 0.3)
        cilindro(0.15, 0.13, y0 + alt + 0.05, 10)
        glPopMatrix()
    glPushMatrix()                                   # tábua (caixa de madeira)
    glTranslatef(0, y0, z + 0.3)
    usar_textura("madeira", 2, 1)
    caixa(larg, alt, esp)
    glPopMatrix()
    # frente (+Z, quem chega de fora) e verso (-Z, quem está dentro): mesma imagem;
    # no verso o u vai de 1 a 0 para o texto não aparecer espelhado
    material((1.0, 0.95, 0.9), (0.15, 0.12, 0.1), 10)
    usar_textura("placa")
    x, y1, y2 = larg / 2 - 0.08, y0 + 0.06, y0 + alt - 0.06
    zf, zt = z + 0.3 + esp / 2 + 0.005, z + 0.3 - esp / 2 - 0.005
    glBegin(GL_QUADS)
    glNormal3f(0, 0, 1)
    glTexCoord2f(0, 0); glVertex3f(-x, y1, zf)
    glTexCoord2f(1, 0); glVertex3f(x, y1, zf)
    glTexCoord2f(1, 1); glVertex3f(x, y2, zf)
    glTexCoord2f(0, 1); glVertex3f(-x, y2, zf)
    glNormal3f(0, 0, -1)
    glTexCoord2f(0, 0); glVertex3f(x, y1, zt)
    glTexCoord2f(1, 0); glVertex3f(-x, y1, zt)
    glTexCoord2f(1, 1); glVertex3f(-x, y2, zt)
    glTexCoord2f(0, 1); glVertex3f(x, y2, zt)
    glEnd()
    # telhadinho de proteção
    mat_palha()
    usar_textura("palha", 3, 1)
    glPushMatrix()
    glTranslatef(0, y0 + alt + 0.02, z + 0.3)
    caixa(larg + 0.8, 0.12, 0.8)
    glPopMatrix()


def portao(angulo):
    """angulo: 0 = fechado, 100 = aberto (graus). Abre para dentro do quilombo (-Z)."""
    z = RAIO_MURO
    larg = MEIA_ABERTURA
    # pilares grossos
    mat_madeira()
    usar_textura("casca", 1, 2)
    for x in (-larg - 0.2, larg + 0.2):
        glPushMatrix()
        glTranslatef(x, 0, z)
        cilindro(0.25, 0.22, 3.6, 10)
        glPopMatrix()
    # folha esquerda: pivô na dobradiça (x = -larg), gira +angulo em Y
    glPushMatrix()
    glTranslatef(-larg, 0, z)
    glRotatef(angulo, 0, 1, 0)
    _folha(larg)
    glPopMatrix()
    # folha direita: mesma folha, pivô em x = +larg, girada 180° (espelhada) e abrindo ao contrário
    glPushMatrix()
    glTranslatef(larg, 0, z)
    glRotatef(180 - angulo, 0, 1, 0)
    _folha(larg)
    glPopMatrix()


# ---------------------------------------------------------------------
# 4. MUXIMA — casa redonda: parede de reboco em anel + teto cônico de palha
# ---------------------------------------------------------------------
def muxima():
    r, h = 4.0, 2.4
    n = 24
    mat_reboco()
    usar_textura("reboco", 1, 1)
    for i in range(n):
        a = 2 * math.pi * (i + 0.5) / n
        if abs(math.atan2(math.sin(a - math.pi / 2), math.cos(a - math.pi / 2))) < 0.2:
            continue                                         # porta virada para +Z
        comp = 2 * r * math.sin(math.pi / n) + 0.05
        glPushMatrix()
        glTranslatef(math.cos(a) * r, 0, math.sin(a) * r)    # TRANSLAÇÃO até a borda
        glRotatef(-math.degrees(a) - 90, 0, 1, 0)            # ROTAÇÃO: tangente ao círculo
        caixa(comp, h, 0.3)
        glPopMatrix()
    # moldura da porta
    mat_madeira()
    usar_textura("casca", 1, 2)
    for x in (-0.85, 0.85):
        glPushMatrix()
        glTranslatef(x, 0, r)
        cilindro(0.12, 0.12, h + 0.2, 8)
        glPopMatrix()
    # teto: CONE (cilindro com raio de cima 0), passando da parede (beiral)
    mat_palha()
    usar_textura("palha", 8, 2)
    glPushMatrix()
    glTranslatef(0, h - 0.1, 0)
    cilindro(r + 1.3, 0.0, 3.4, 32, tampa=False)
    glPopMatrix()
    # piso interno de terra
    mat_chao()
    usar_textura("terra", 2, 2)
    glPushMatrix()
    glTranslatef(0, 0.04, 0)
    disco(r, 24)
    glPopMatrix()
    # dentro: bancos de madeira em roda (local de reunião) e uma esteira no centro
    mat_madeira()
    usar_textura("madeira", 1, 1)
    for k in range(5):
        a = math.radians(200 + k * 35)                       # só no fundo, longe da porta
        glPushMatrix()
        glTranslatef(math.cos(a) * 2.9, 0, math.sin(a) * 2.9)
        glRotatef(-math.degrees(a) - 90, 0, 1, 0)
        caixa(1.4, 0.45, 0.4)
        glPopMatrix()
    mat_palha()
    usar_textura("palha", 2, 2)
    glPushMatrix()
    glTranslatef(0, 0.05, -0.5)
    caixa(2.2, 0.03, 1.6)
    glPopMatrix()


# ---------------------------------------------------------------------
# 5. OCA — esfera de palha ESTICADA em Y (escala não uniforme)
# ---------------------------------------------------------------------
OCA_RAIO = 3.0
OCA_MEIA_PORTA = 0.3          # meia largura da porta, em radianos (≈ 1,8 m de vão)


def oca():
    # casca: cúpula esticada em Y (forma de colmeia), com o vão da porta virado para +Z
    mat_palha()
    usar_textura(None)
    glEnable(GL_TEXTURE_2D)
    glBindTexture(GL_TEXTURE_2D, textura("palha"))
    glMatrixMode(GL_TEXTURE); glLoadIdentity(); glMatrixMode(GL_MODELVIEW)
    cupula_com_porta(OCA_RAIO, 1.25, OCA_MEIA_PORTA, 2.1)
    glPushMatrix()
    glTranslatef(0, OCA_RAIO * 1.25 - 0.1, 0)
    cilindro(0.35, 0.0, 0.7, 10, tampa=False)
    glPopMatrix()
    # moldura da porta (dois paus + travessa)
    mat_madeira()
    usar_textura("casca", 1, 2)
    for lado in (-1, 1):
        a = lado * OCA_MEIA_PORTA
        glPushMatrix()
        glTranslatef(math.sin(a) * OCA_RAIO, 0, math.cos(a) * OCA_RAIO)
        cilindro(0.08, 0.08, 2.15, 6)
        glPopMatrix()
    # dentro: chão de terra, esteira de palha e um pote de barro
    mat_chao()
    usar_textura("terra", 2, 2)
    glPushMatrix()
    glTranslatef(0, 0.04, 0)
    disco(OCA_RAIO - 0.05, 24)
    glPopMatrix()
    mat_palha()
    usar_textura("palha", 1, 1)
    glPushMatrix()
    glTranslatef(0.6, 0.05, -1.2)
    glRotatef(20, 0, 1, 0)
    caixa(1.0, 0.04, 1.9)
    glPopMatrix()
    usar_textura(None)
    material((0.55, 0.32, 0.2), (0.2, 0.15, 0.1), 15)       # barro
    glPushMatrix()
    glTranslatef(-1.3, 0, -0.9)
    glScalef(1, 1.3, 1)
    esfera(0.3, 12)
    glPopMatrix()


# ---------------------------------------------------------------------
# 6. CASA DE FARINHA — galpão aberto: postes + telhado de 4 águas
# ---------------------------------------------------------------------
def casa_farinha():
    cx, cz, hp = 4.0, 2.5, 2.4
    mat_madeira()
    usar_textura("casca", 1, 2)
    for x in (-cx, 0, cx):
        for z in (-cz, cz):
            glPushMatrix()
            glTranslatef(x, 0, z)
            cilindro(0.15, 0.15, hp, 8)
            glPopMatrix()
    # telhado de 4 águas = PIRÂMIDE (cilindro de 4 lados com topo 0)
    #   ROTAÇÃO de 45° alinha os lados aos eixos; ESCALA não uniforme vira retângulo
    mat_palha()
    usar_textura("palha", 4, 2)
    glPushMatrix()
    glTranslatef(0, hp, 0)
    glScalef(cx + 1.0, 1, cz + 1.0)
    glRotatef(45, 0, 1, 0)
    cilindro(math.sqrt(2), 0.0, 2.4, 4, tampa=False)
    glPopMatrix()
    # forno de barro com o tacho de torrar farinha
    mat_reboco()
    usar_textura("reboco", 1, 1)
    glPushMatrix()
    glTranslatef(-1.5, 0, -0.5)
    caixa(2.2, 0.8, 1.4)
    glPopMatrix()
    usar_textura(None)
    material((0.15, 0.15, 0.15), (0.6, 0.6, 0.6), 40)          # tacho de metal: brilha
    glPushMatrix()
    glTranslatef(-1.5, 0.8, -0.5)
    cilindro(0.6, 0.6, 0.08, 20)
    glPopMatrix()
    # cestos de palha
    mat_palha()
    usar_textura("palha", 2, 1)
    for x, z in ((1.6, 1.0), (2.4, -0.8), (1.2, -1.4)):
        glPushMatrix()
        glTranslatef(x, 0, z)
        cilindro(0.3, 0.38, 0.5, 12)
        glPopMatrix()


# ---------------------------------------------------------------------
# 7. ÁRVORE — tronco (cilindro) + copa (esferas achatadas)
# ---------------------------------------------------------------------
def arvore():
    mat_madeira()
    usar_textura("casca", 1, 2)
    cilindro(0.35, 0.22, 3.2, 10)
    mat_folhas()
    usar_textura("folhas", 3, 3)
    for (x, y, z, r) in ((0, 3.8, 0, 1.9), (0.9, 4.4, 0.3, 1.3), (-0.8, 4.2, -0.4, 1.4)):
        glPushMatrix()
        glTranslatef(x, y, z)
        glScalef(1.15, 0.8, 1.15)
        esfera(r, 14)
        glPopMatrix()


# ---------------------------------------------------------------------
# 8. COQUEIRO — tronco alto + folhas (caixas finas) giradas em volta do topo
# ---------------------------------------------------------------------
def _fronde(comp, elev, queda, verde):
    """Uma folha de coqueiro (fronde). Ela nasce no topo e aponta para +Z.
    O TALO é uma curva: sobe com ângulo `elev` e vai caindo (parábola, como um galho pesado):
        z(s) = s·cos(elev)        y(s) = s·sen(elev) − queda·s²
    De cada ponto do talo saem dois FOLÍOLOS (as tirinhas), um pra cada lado, inclinados pra baixo.
    Cada folíolo é um quadrilátero fino desenhado vértice a vértice."""
    n = 22
    ce, se = math.cos(elev), math.sin(elev)
    material(verde, (0.08, 0.1, 0.05), 8)
    glBegin(GL_QUADS)
    for k in range(2, n):
        s = comp * k / n
        z, y = s * ce, s * se - queda * s * s
        dz = ce                                             # derivada da curva: direção do talo
        dy = se - 2 * queda * s
        m = math.hypot(dz, dy)
        dz, dy = dz / m, dy / m
        frac = k / n
        tam = 0.95 * math.sin(math.pi * min(1.0, frac * 1.15)) + 0.12   # folíolos maiores no meio
        larg = 0.07
        for lado in (-1, 1):
            # ponta do folíolo: para o lado (x), um pouco pra frente e caindo
            px = lado * tam * 0.85
            py = y - tam * 0.45
            pz = z + tam * 0.35
            glNormal3f(0, 1, 0.2)
            glTexCoord2f(0, 0); glVertex3f(0, y, z)
            glTexCoord2f(1, 0); glVertex3f(0, y + dy * larg, z + dz * larg)
            glTexCoord2f(1, 1); glVertex3f(px, py + dy * larg * 0.5, pz + dz * larg * 0.5)
            glTexCoord2f(0, 1); glVertex3f(px, py, pz)
    glEnd()
    # o talo (nervura central): fileira de quadradinhos finos
    material((0.45, 0.42, 0.2))
    glBegin(GL_QUAD_STRIP)
    for k in range(n + 1):
        s = comp * k / n
        z, y = s * ce, s * se - queda * s * s
        w = 0.05 * (1 - k / n) + 0.01
        glNormal3f(0, 1, 0)
        glVertex3f(-w, y, z)
        glVertex3f(w, y, z)
    glEnd()


def coqueiro():
    """Coqueiro: tronco CURVO + copa de frondes + cachos de coco.
    O tronco é feito de 12 pedaços de cilindro. Depois de cada pedaço: TRANSLAÇÃO até o topo dele
    e uma ROTAÇÃO pequena (3°). As rotações se ACUMULAM na matriz, então o tronco vai entortando
    aos poucos, como um coqueiro de verdade. A copa é desenhada já nesse sistema entortado."""
    segs, h_seg = 12, 0.62
    mat_madeira()
    usar_textura("casca", 1, 1)
    glPushMatrix()
    for k in range(segs):
        r0 = 0.24 - 0.09 * k / segs
        r1 = 0.24 - 0.09 * (k + 1) / segs
        cilindro(r0 * 1.12, r1, h_seg, 10, tampa=False)      # base um pouco mais larga: "anéis" no tronco
        glTranslatef(0, h_seg, 0)                             # TRANSLAÇÃO até o topo do pedaço
        glRotatef(3.0, 1, 0, 0)                               # ROTAÇÃO acumulada: o tronco curva
    # topo do tronco (onde nascem as folhas)
    material((0.45, 0.38, 0.2))
    esfera(0.2, 10)
    usar_textura("folhas", 1, 1)
    # frondes: 12 em volta; as de cima mais em pé, as de baixo caídas; 2 secas, marrons, penduradas
    for k in range(12):
        glPushMatrix()
        glRotatef(360 * k / 12 + (k % 3) * 9, 0, 1, 0)       # ROTAÇÃO em Y: direção da folha
        alta = k % 2 == 0
        elev = math.radians(48 if alta else 22)
        queda = 0.11 if alta else 0.16
        verde = (0.42, 0.62, 0.22) if alta else (0.36, 0.55, 0.2)
        _fronde(3.2 if alta else 3.6, elev, queda, verde)
        glPopMatrix()
    for ang in (70, 250):
        glPushMatrix()
        glRotatef(ang, 0, 1, 0)
        _fronde(2.6, math.radians(-50), 0.02, (0.55, 0.42, 0.22))   # folhas secas, caídas
        glPopMatrix()
    # cachos de coco embaixo da copa
    usar_textura(None)
    material((0.38, 0.3, 0.1), (0.15, 0.15, 0.1), 20)
    for k in range(5):
        a = 2 * math.pi * k / 5 + 0.4
        glPushMatrix()
        glTranslatef(math.cos(a) * 0.26, -0.3 - (k % 2) * 0.12, math.sin(a) * 0.26)
        glScalef(1, 1.15, 1)                                  # ESCALA: coco um pouco oval
        esfera(0.15, 10)
        glPopMatrix()
    glPopMatrix()


# ---------------------------------------------------------------------
# 9. POÇO — mureta de pedra + estrutura de madeira + telhadinho
# ---------------------------------------------------------------------
def poco():
    mat_pedra()
    usar_textura("pedra", 4, 1)
    cilindro(1.15, 1.15, 0.9, 24, tampa=False)               # parede de fora
    cilindro(0.95, 0.95, 0.9, 24, tampa=False)               # parede de dentro (espessura de 20 cm)
    glPushMatrix()                                           # borda de cima: anel (disco com furo)
    glTranslatef(0, 0.9, 0)
    glRotatef(-90, 1, 0, 0)
    gluDisk(quadrica(), 0.95, 1.2, 24, 1)
    glPopMatrix()
    mat_agua()                                                 # água lá dentro (y = POCO_AGUA)
    material((0.25, 0.4, 0.5), (1, 1, 1), 90)
    usar_textura("agua", 2, 2)
    glPushMatrix()
    glTranslatef(0, POCO_AGUA, 0)
    disco(0.95, 24)
    glPopMatrix()
    mat_madeira()
    usar_textura("casca", 1, 2)
    for x in (-1.0, 1.0):
        glPushMatrix()
        glTranslatef(x, 0, 0)
        cilindro(0.08, 0.08, 2.3, 8)
        glPopMatrix()
    mat_palha()
    usar_textura("palha", 2, 1)
    glPushMatrix()
    glTranslatef(0, 2.3, 0)
    glScalef(1.4, 1, 1.0)
    glRotatef(45, 0, 1, 0)
    cilindro(math.sqrt(2), 0, 0.8, 4, tampa=False)
    glPopMatrix()


POCO_AGUA = 0.5            # altura da superfície da água dentro do poço
POCO_SARILHO = 1.7         # altura do eixo do sarilho
RAIO_SARILHO = 0.07


def altura_balde(h):
    """h = 1: balde pendurado em cima; h = 0: balde mergulhado na água."""
    return 0.3 + h * 0.95


def sarilho(angulo):
    """Eixo de madeira que enrola a corda + manivela. Gira em volta do eixo X."""
    glPushMatrix()
    glTranslatef(0, POCO_SARILHO, 0)
    glRotatef(angulo, 1, 0, 0)                     # ROTAÇÃO do sarilho (gira enquanto a corda enrola)
    mat_madeira()
    usar_textura("casca", 2, 1)
    glPushMatrix()
    glTranslatef(-1.05, 0, 0)
    glRotatef(-90, 0, 0, 1)                        # deita o cilindro no eixo X
    cilindro(RAIO_SARILHO, RAIO_SARILHO, 2.1, 10)
    glPopMatrix()
    # corda enrolada no meio (cilindro mais grosso, cor de corda)
    usar_textura(None)
    material((0.6, 0.5, 0.35))
    glPushMatrix()
    glTranslatef(-0.2, 0, 0)
    glRotatef(-90, 0, 0, 1)
    cilindro(RAIO_SARILHO + 0.03, RAIO_SARILHO + 0.03, 0.4, 10)
    glPopMatrix()
    # manivela: braço (caixa) + pegador (cilindro), girando junto com o eixo
    mat_madeira()
    usar_textura("madeira", 1, 1)
    glPushMatrix()
    glTranslatef(1.12, 0, 0)
    caixa(0.06, 0.38, 0.08)                        # braço: vai do eixo até 0,38 m
    glTranslatef(0, 0.34, 0)
    glRotatef(-90, 0, 0, 1)
    cilindro(0.035, 0.035, 0.25, 6)                # pegador pra fora
    glPopMatrix()
    glPopMatrix()


def balde(h, cheio, inclinacao):
    """Balde: TRANSLAÇÃO vertical (h), ROTAÇÃO pra despejar (inclinacao) e corda ESTICADA com escala."""
    y = altura_balde(h)
    glPushMatrix()
    glTranslatef(0, y, 0)
    glTranslatef(0, 0.42, 0)                       # gira em volta da alça (pivô no alto do balde)
    glRotatef(inclinacao, 0, 0, 1)
    glTranslatef(0, -0.42, 0)
    mat_madeira()
    usar_textura("madeira", 2, 1)
    cilindro(0.18, 0.22, 0.32, 14, tampa=False)    # corpo aberto em cima
    disco(0.18, 14)                                # fundo
    usar_textura(None)
    material((0.25, 0.25, 0.25), (0.6, 0.6, 0.6), 40)
    for yy in (0.05, 0.27):                        # aros de ferro
        glPushMatrix()
        glTranslatef(0, yy, 0)
        cilindro(0.19 + yy * 0.12, 0.19 + yy * 0.12, 0.03, 14, tampa=False)
        glPopMatrix()
    glPushMatrix()                                 # alça
    glTranslatef(0, 0.42, 0)
    caixa(0.46, 0.025, 0.025)
    glPopMatrix()
    for x in (-0.22, 0.22):
        glPushMatrix()
        glTranslatef(x, 0.3, 0)
        cilindro(0.012, 0.012, 0.13, 4)
        glPopMatrix()
    if cheio:                                      # água dentro do balde
        material((0.25, 0.45, 0.6), (1, 1, 1), 90)
        usar_textura("agua", 1, 1)
        glPushMatrix()
        glTranslatef(0, 0.26, 0)
        disco(0.205, 14)
        glPopMatrix()
    glPopMatrix()
    # corda: um cilindro de altura 1 ESCALADO em Y até o tamanho certo
    usar_textura(None)
    material((0.6, 0.5, 0.35))
    topo = POCO_SARILHO - RAIO_SARILHO
    base = y + 0.42
    glPushMatrix()
    glTranslatef(0, base, 0)
    glScalef(1, max(topo - base, 0.01), 1)
    cilindro(0.015, 0.015, 1.0, 4, tampa=False)
    glPopMatrix()


def ondas_e_gotas(ondas, gotas, t):
    """Ondas (círculos que crescem e somem) na água do poço e gotas caindo. Sem iluminação."""
    glDisable(GL_LIGHTING)
    glDisable(GL_TEXTURE_2D)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    for t0 in ondas:
        idade = t - t0
        r = 0.15 + idade * 0.7
        if r > 0.93:
            continue
        glColor4f(0.85, 0.95, 1.0, max(0.0, 1 - idade / 1.0))
        glBegin(GL_LINE_LOOP)
        for k in range(28):
            a = 2 * math.pi * k / 28
            glVertex3f(math.cos(a) * r, POCO_AGUA + 0.01, math.sin(a) * r)   # círculo paramétrico
        glEnd()
    glPointSize(4)
    glBegin(GL_POINTS)
    for g in gotas:
        glColor4f(0.6, 0.8, 1.0, 0.9)
        glVertex3f(g[0], g[1], g[2])
    glEnd()
    glColor4f(1, 1, 1, 1)
    glDisable(GL_BLEND)
    glEnable(GL_LIGHTING)


# ---------------------------------------------------------------------
# 11. ATALAIA — torre de vigia de madeira com escada (dá pra subir com E)
# ---------------------------------------------------------------------
ATALAIA_ALTURA = 6.0          # altura do piso da plataforma
ATALAIA_PE = (0.0, 3.3)       # (x, z) local: onde o jogador fica ao pé da escada
ATALAIA_TOPO = (0.0, 0.7)     # (x, z) local: na plataforma, perto da frente (vista pra aldeia)


def atalaia():
    h = ATALAIA_ALTURA
    s = 1.3                                   # meia largura da torre
    mat_madeira()
    usar_textura("casca", 1, 4)
    for x in (-s, s):                         # 4 postes (vão até o telhado)
        for z in (-s, s):
            glPushMatrix()
            glTranslatef(x, 0, z)
            cilindro(0.16, 0.13, h + 2.0, 8)
            glPopMatrix()
    # travamento em X nas laterais: caixa girada em Z (ângulo por atan2, comprimento por Pitágoras)
    usar_textura("madeira", 2, 1)
    diag = math.hypot(2 * s, h * 0.5)
    ang = math.degrees(math.atan2(h * 0.5, 2 * s))
    for giro in (0, 90, 180, 270):
        if giro == 0:
            continue                          # a frente (+Z) fica livre pra escada
        glPushMatrix()
        glRotatef(giro, 0, 1, 0)
        glTranslatef(0, h * 0.25, s)
        for sinal in (1, -1):
            glPushMatrix()
            glRotatef(sinal * ang, 0, 0, 1)
            glTranslatef(0, -0.06, 0)
            caixa(diag, 0.12, 0.1)
            glPopMatrix()
        glPopMatrix()
    # plataforma
    usar_textura("madeira", 3, 3)
    glPushMatrix()
    glTranslatef(0, h - 0.15, 0)
    caixa(2 * s + 0.4, 0.15, 2 * s + 0.4)
    glPopMatrix()
    # parapeito: corrimãos nos 4 lados, com abertura na frente pra escada
    for giro in (0, 90, 180, 270):
        for y in (0.55, 1.05):
            glPushMatrix()
            glRotatef(giro, 0, 1, 0)
            if giro == 0:                     # frente: duas metades, sobra o vão da escada
                for lado in (-1, 1):
                    glPushMatrix()
                    glTranslatef(lado * (s + 0.5) / 2, h + y, s + 0.15)
                    caixa(s - 0.5, 0.08, 0.08)
                    glPopMatrix()
            else:
                glTranslatef(0, h + y, s + 0.15)
                caixa(2 * s + 0.3, 0.08, 0.08)
            glPopMatrix()
    # telhado de palha: pirâmide (cilindro de 4 lados) girada 45°
    mat_palha()
    usar_textura("palha", 3, 1)
    glPushMatrix()
    glTranslatef(0, h + 2.0, 0)
    glScalef(s + 0.6, 1, s + 0.6)
    glRotatef(45, 0, 1, 0)
    cilindro(math.sqrt(2), 0.0, 1.4, 4, tampa=False)
    glPopMatrix()
    # ESCADA: dois trilhos INCLINADOS (rotação em X) + degraus
    mat_madeira()
    usar_textura("casca", 1, 3)
    z_pe, z_topo = 2.4, s + 0.05
    comp = math.hypot(h, z_pe - z_topo)                       # comprimento: Pitágoras
    incl = math.degrees(math.atan2(z_pe - z_topo, h))         # inclinação
    for x in (-0.32, 0.32):
        glPushMatrix()
        glTranslatef(x, 0, z_pe)
        glRotatef(-incl, 1, 0, 0)                             # ROTAÇÃO: encosta a escada na torre
        cilindro(0.05, 0.05, comp, 6)
        glPopMatrix()
    usar_textura("madeira", 1, 1)
    d = 0.35
    while d < comp:
        k = d / comp
        glPushMatrix()
        glTranslatef(0, k * h, z_pe + k * (z_topo - z_pe))    # degrau ao longo da escada (interpolação)
        caixa(0.7, 0.05, 0.06)
        glPopMatrix()
        d += 0.4


# ---------------------------------------------------------------------
# 10. FOGUEIRA — pedras em anel + lenha (parte fixa). A chama é animada (main.py).
# ---------------------------------------------------------------------
def fogueira_base():
    mat_pedra()
    usar_textura("pedra", 1, 1)
    for k in range(12):
        a = 2 * math.pi * k / 12
        glPushMatrix()
        glTranslatef(math.cos(a) * 1.0, 0.05, math.sin(a) * 1.0)
        glScalef(1.0, 0.6, 1.0)
        esfera(0.25, 10)
        glPopMatrix()
    mat_madeira()
    usar_textura("casca", 1, 1)
    for k in range(6):
        glPushMatrix()
        glRotatef(60 * k, 0, 1, 0)        # cada tora numa direção
        glTranslatef(0, 0, 0.55)
        glRotatef(-35, 1, 0, 0)           # encosta no centro (forma de tenda)
        cilindro(0.08, 0.07, 1.0, 6)
        glPopMatrix()


def chama(t, intensidade):
    """Chama: cones emissivos que tremem (ESCALA variando com o tempo). Sem iluminação: ela É a luz."""
    glDisable(GL_LIGHTING)
    glDisable(GL_TEXTURE_2D)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE)     # mistura ADITIVA: soma cor (fogo brilha)
    glDepthMask(GL_FALSE)
    camadas = ((0.55, 1.3, (1.0, 0.35, 0.05, 0.7)), (0.38, 1.0, (1.0, 0.65, 0.1, 0.8)),
               (0.2, 0.7, (1.0, 0.95, 0.5, 0.9)))
    for i, (r, h, cor) in enumerate(camadas):
        tremor = 1 + 0.18 * math.sin(t * 11 + i * 2.1) + 0.1 * math.sin(t * 23 + i)
        glColor4f(cor[0], cor[1], cor[2], cor[3] * intensidade)
        glPushMatrix()
        glTranslatef(0, 0.15, 0)
        glRotatef(t * 40 * (i + 1), 0, 1, 0)
        glScalef(1, tremor * intensidade, 1)
        cilindro(r, 0.0, h, 8, tampa=False)
        glPopMatrix()
    glDepthMask(GL_TRUE)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glColor4f(1, 1, 1, 1)
    glEnable(GL_LIGHTING)


# ---------------------------------------------------------------------
# LAGOA — elipse (disco com escala não uniforme). A água é desenhada a cada quadro.
# ---------------------------------------------------------------------
LAGOA_RX, LAGOA_RZ = 6.5, 3.2


def lagoa_margem():
    mat_chao()
    usar_textura("terra", 3, 3)
    glPushMatrix()
    glTranslatef(0, 0.03, 0)
    glScalef(LAGOA_RX + 1.0, 1, LAGOA_RZ + 1.0)
    disco(1, 40)
    glPopMatrix()
    mat_pedra()
    usar_textura("pedra", 1, 1)
    for k in range(18):
        a = 2 * math.pi * k / 18
        glPushMatrix()
        glTranslatef(math.cos(a) * (LAGOA_RX + 0.8), 0.05, math.sin(a) * (LAGOA_RZ + 0.8))  # elipse paramétrica
        glScalef(1, 0.55, 1)
        esfera(0.35, 8)
        glPopMatrix()


def abobada_celeste(dia, cor_horizonte, giro_u=0.0, raio=300.0):
    """CÉU: meia esfera ENORME em volta da câmera, com a foto do céu colada POR DENTRO (sky dome).
    A foto é equiretangular (panorâmica 360°): u = ângulo em volta (azimute), v = altura (elevação).
    De dia usa ceu_dia.jpg; de noite a ceu_noite.jpg vai aparecendo por cima (transparência = 1 - dia).
    Sem luz, sem neblina e sem gravar profundidade: fica sempre "no fundo", atrás de tudo."""
    fatias, aneis = 48, 16
    el_min = -0.15                                   # desce um pouco abaixo do horizonte (sem buraco)

    def cupula(nome, r, g, b, a):
        usar_textura(nome)
        glColor4f(r, g, b, a)
        for j in range(aneis):
            glBegin(GL_QUAD_STRIP)
            for i in range(fatias + 1):
                az = 2 * math.pi * i / fatias
                for jj in (j + 1, j):
                    el = el_min + (math.pi / 2 - el_min) * jj / aneis
                    glTexCoord2f(i / fatias + giro_u, max(0.0, el) / (math.pi / 2))   # (u, v) da foto
                    glVertex3f(raio * math.cos(el) * math.cos(az), raio * math.sin(el),
                               raio * math.cos(el) * math.sin(az))
            glEnd()

    claro = 0.35 + 0.65 * dia
    cupula("ceu_dia", claro, claro, claro, 1.0)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    if dia < 0.99:
        cupula("ceu_noite", 1, 1, 1, 1.0 - dia)
    # faixa do horizonte: cor da neblina, opaca embaixo e sumindo pra cima (junta céu e chão sem emenda)
    glDisable(GL_TEXTURE_2D)
    c = cor_horizonte
    for el_a, al_a, el_b, al_b in ((el_min, 1.0, 0.02, 0.9), (0.02, 0.9, 0.28, 0.0)):
        glBegin(GL_QUAD_STRIP)
        for i in range(fatias + 1):
            az = 2 * math.pi * i / fatias
            for el, al in ((el_b, al_b), (el_a, al_a)):
                glColor4f(c[0], c[1], c[2], al)
                glVertex3f(raio * 0.98 * math.cos(el) * math.cos(az), raio * 0.98 * math.sin(el),
                           raio * 0.98 * math.cos(el) * math.sin(az))
        glEnd()
    glDisable(GL_BLEND)
    glColor4f(1, 1, 1, 1)


def agua(t):
    """Água transparente e brilhante. A textura DESLIZA: translação na matriz de textura."""
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glDepthMask(GL_FALSE)
    mat_agua()
    glEnable(GL_TEXTURE_2D)
    glBindTexture(GL_TEXTURE_2D, textura("agua"))
    glMatrixMode(GL_TEXTURE)
    glLoadIdentity()
    glTranslatef(t * 0.03, t * 0.018, 0)      # TRANSLAÇÃO da textura com o tempo
    glScalef(3, 1.5, 1)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glTranslatef(0, 0.08, 0)
    glScalef(LAGOA_RX, 1, LAGOA_RZ)
    disco(1, 48, 12)                          # muitos anéis: o brilho especular fica suave
    glPopMatrix()
    glDepthMask(GL_TRUE)
    glDisable(GL_BLEND)
