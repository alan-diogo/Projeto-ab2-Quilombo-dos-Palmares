# =====================================================================
# PRIMITIVAS — as peças básicas com que TODA a cena é modelada.
# =====================================================================
# Cada função desenha uma forma em volta da ORIGEM do sistema de coordenadas atual.
# Quem chama posiciona a peça antes com glTranslate / glRotate / glScale
# (as 3 transformações geométricas), entre glPushMatrix / glPopMatrix.
#
# Também ficam aqui: carregar texturas e definir materiais (glMaterial).

import math
import os
from OpenGL.GL import *
from OpenGL.GLU import *
from PIL import Image

PASTA = os.path.dirname(os.path.abspath(__file__))
_texturas = {}
_quad = None


def quadrica():
    """Objeto do GLU que desenha cilindros, esferas e discos com normais e coordenadas de textura."""
    global _quad
    if _quad is None:
        _quad = gluNewQuadric()
        gluQuadricNormals(_quad, GLU_SMOOTH)   # normal em cada vértice (pra iluminação)
        gluQuadricTexture(_quad, GL_TRUE)      # gera coordenadas (u, v) de textura
    return _quad


# ---------------------------------------------------------------------
# TEXTURAS
# ---------------------------------------------------------------------
def textura(nome):
    """Carrega texturas/<nome>.jpg na placa de vídeo (uma vez só) e devolve o id."""
    if nome in _texturas:
        return _texturas[nome]
    img = Image.open(os.path.join(PASTA, "texturas", nome + ".jpg")).convert("RGB")
    img = img.transpose(Image.FLIP_TOP_BOTTOM)          # OpenGL lê a imagem de baixo pra cima
    dados = img.tobytes()
    tid = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, tid)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)   # repete além de 0..1
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
    # mipmaps: versões menores da imagem, usadas de longe (evita "chiado")
    gluBuild2DMipmaps(GL_TEXTURE_2D, GL_RGB, img.width, img.height, GL_RGB, GL_UNSIGNED_BYTE, dados)
    _texturas[nome] = tid
    return tid


def usar_textura(nome, rep_u=1.0, rep_v=1.0):
    """Liga a textura e define quantas vezes ela se repete (pela MATRIZ DE TEXTURA)."""
    if nome is None:
        glDisable(GL_TEXTURE_2D)
        return
    glEnable(GL_TEXTURE_2D)
    glBindTexture(GL_TEXTURE_2D, textura(nome))
    glMatrixMode(GL_TEXTURE)
    glLoadIdentity()
    glScalef(rep_u, rep_v, 1)          # ESCALA nas coordenadas de textura = repetição
    glMatrixMode(GL_MODELVIEW)


# ---------------------------------------------------------------------
# MATERIAIS — como cada superfície reage à luz (modelo de Phong)
# ---------------------------------------------------------------------
def material(difusa, especular=(0, 0, 0), brilho=1, emissao=(0, 0, 0)):
    """difusa: cor sob luz direta | especular: cor do brilho | brilho: 1 (fosco) a 128 (polido)."""
    d = list(difusa) + [1.0] if len(difusa) == 3 else list(difusa)
    amb = [d[0] * 0.6, d[1] * 0.6, d[2] * 0.6, d[3]]
    glMaterialfv(GL_FRONT_AND_BACK, GL_AMBIENT, amb)
    glMaterialfv(GL_FRONT_AND_BACK, GL_DIFFUSE, d)
    glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, list(especular) + [1.0])
    glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, brilho)
    glMaterialfv(GL_FRONT_AND_BACK, GL_EMISSION, list(emissao) + [1.0])

# Materiais do projeto (cada objeto usa o seu)
def mat_palha():   material((0.95, 0.85, 0.65))                                  # fosca
def mat_reboco():  material((1.0, 0.95, 0.85), (0.05, 0.05, 0.05), 4)
def mat_madeira(): material((0.9, 0.8, 0.7), (0.15, 0.12, 0.1), 12)
def mat_pedra():   material((0.85, 0.85, 0.85), (0.25, 0.25, 0.25), 20)
def mat_folhas():  material((0.75, 0.9, 0.7), (0.05, 0.08, 0.05), 6)
def mat_chao():    material((0.9, 0.9, 0.9))
def mat_agua():    material((0.55, 0.75, 0.85, 0.75), (1.0, 1.0, 1.0), 90)      # brilhante e transparente


# ---------------------------------------------------------------------
# FORMAS (todas em pé no eixo Y, com a base em y = 0)
# ---------------------------------------------------------------------
def cilindro(r_base, r_topo, altura, lados=16, tampa=True):
    """Cilindro em pé. r_topo = 0 vira CONE; lados = 4 vira PIRÂMIDE."""
    q = quadrica()
    glPushMatrix()
    glRotatef(-90, 1, 0, 0)            # o GLU desenha ao longo de Z: ROTAÇÃO pra ficar em pé (Y)
    gluCylinder(q, r_base, r_topo, altura, lados, 1)
    if tampa and r_topo > 0:
        glTranslatef(0, 0, altura)
        gluDisk(q, 0, r_topo, lados, 1)
    glPopMatrix()


def esfera(raio, lados=16):
    gluSphere(quadrica(), raio, lados, lados // 2 + 2)


def disco(raio, lados=32, aneis=1):
    """Disco deitado no chão (normal pra cima)."""
    glPushMatrix()
    glRotatef(-90, 1, 0, 0)
    gluDisk(quadrica(), 0, raio, lados, aneis)
    glPopMatrix()


def caixa(sx, sy, sz, rep=1.0):
    """Caixa com a BASE em y = 0. Cada face tem sua normal e suas coordenadas de textura."""
    x, z = sx / 2, sz / 2
    faces = [
        ((0, 0, 1),  [(-x, 0, z), (x, 0, z), (x, sy, z), (-x, sy, z)]),
        ((0, 0, -1), [(x, 0, -z), (-x, 0, -z), (-x, sy, -z), (x, sy, -z)]),
        ((1, 0, 0),  [(x, 0, z), (x, 0, -z), (x, sy, -z), (x, sy, z)]),
        ((-1, 0, 0), [(-x, 0, -z), (-x, 0, z), (-x, sy, z), (-x, sy, -z)]),
        ((0, 1, 0),  [(-x, sy, z), (x, sy, z), (x, sy, -z), (-x, sy, -z)]),
        ((0, -1, 0), [(-x, 0, -z), (x, 0, -z), (x, 0, z), (-x, 0, z)]),
    ]
    uv = [(0, 0), (rep, 0), (rep, rep), (0, rep)]
    glBegin(GL_QUADS)
    for normal, vs in faces:
        glNormal3f(*normal)
        for (u, v), p in zip(uv, vs):
            glTexCoord2f(u, v)
            glVertex3f(*p)
    glEnd()


def cupula_com_porta(raio, esticar_y, meia_porta, altura_porta, fatias=32, aneis=12, rep_u=6, rep_v=3):
    """Meia esfera (cúpula) feita VÉRTICE A VÉRTICE, deixando um vão de porta no lado +Z.
    Cada ponto: x = r·cosθ·senφ, y = r·senθ·esticar, z = r·cosθ·cosφ
      φ = ângulo em volta do eixo Y (0 = frente, +Z)   θ = altura (0 = chão, 90° = topo)
    Os quadriláteros cujo φ está dentro da porta e cuja altura é menor que a da porta são pulados."""
    def ponto(i, j):
        phi = 2 * math.pi * i / fatias - math.pi          # de -180° a +180° (0 = frente)
        th = (math.pi / 2) * j / aneis
        c, s = math.cos(th), math.sin(th)
        p = (raio * c * math.sin(phi), raio * s * esticar_y, raio * c * math.cos(phi))
        n = (c * math.sin(phi), s / esticar_y, c * math.cos(phi))   # normal da elipsoide
        uv = (rep_u * i / fatias, rep_v * j / aneis)
        return p, n, uv, phi
    glBegin(GL_QUADS)
    for j in range(aneis):
        for i in range(fatias):
            cantos = [ponto(i, j), ponto(i + 1, j), ponto(i + 1, j + 1), ponto(i, j + 1)]
            phi_meio = (cantos[0][3] + cantos[1][3]) / 2
            y_baixo = cantos[0][0][1]
            if abs(phi_meio) < meia_porta and y_baixo < altura_porta:
                continue                                    # aqui é a porta
            for p, n, uv, _ in cantos:
                glNormal3f(*n)
                glTexCoord2f(*uv)
                glVertex3f(*p)
    glEnd()
