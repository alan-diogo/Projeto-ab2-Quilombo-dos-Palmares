# Relatório — Quilombo dos Palmares

**Disciplina:** Computação Gráfica  
**Atividade:** Projeto Modelagem AB2 — Relatório de técnicas utilizadas  
**Professor:** Marcelo Costa Oliveira  
**Equipe:** Alan Diogo da Rocha Oliveira e Bruno Gomes de Barros Filho  

---

## Sobre o projeto

O projeto consiste em uma aplicação OpenGL em Python com GLU, sem engine. A cena consiste em uma visita em primeira pessoa ao Quilombo dos Palmares, localizado na Serra da Barriga, em Alagoas.

O jogador começa do lado de fora da paliçada e precisa cumprir as tarefas do dia, como: abrir o portão, buscar água no poço, esperar a noite, acender a fogueira e subir na atalaia.

Foram utilizadas apenas as bibliotecas PyOpenGL, GLFW e Pillow. O PyOpenGL foi utilizado para desenhar a cena, o GLFW para a janela, controles do teclado e mouse e o Pillow para ler as texturas e renderizar o texto na tela. Não foram utilizados modelos 3D externos; toda a geometria foi feita com primitivas.

## Modelagem

A modelagem foi inteira feita com primitivas. Em `primitivas.py`, estão as formas base: cilindro, esfera, disco e caixa. Em `objetos.py` cada função monta um objeto da cena por meio das peças primitivas. Segue abaixo a lista de objetos modelados:

1. **Chão**  
   Primitivas: disco (grama + praça) e esfera (morros).

2. **Paliçada**  
   Primitivas: cilindro (varas), cone = cilindro com `r_topo = 0` (pontas), caixa (travessas).

3. **Portão**  
   Primitivas: cilindro (pilares e ripas), caixa (travessas e diagonal).

4. **Muxima**  
   Primitivas: caixa (parede em anel), cilindro/cone (teto), disco (piso), cilindro (moldura da porta).

5. **Oca**  
   Primitivas: `cupula_com_porta` (malha paramétrica), cilindro (pináculo e moldura), disco, caixa, esfera (pote).

6. **Casa da farinha**  
   Primitivas: cilindro (postes, tacho, cestos), caixa (forno), pirâmide = cilindro de 4 lados com topo 0.

7. **Árvore**  
   Primitivas: cilindro (tronco), esfera (copa).

8. **Coqueiro**  
   Primitivas: cilindro (tronco em segmentos), esfera (topo e cocos), quads/`GL_QUAD_STRIP` (folhas).

9. **Poço**  
   Primitivas: cilindro (mureta, postes, balde, corda, sarilho), `gluDisk` anelar (borda), disco (água), caixa (manivela/alça), pirâmide (telhadinho).

10. **Fogueira**  
    Primitivas: esfera achatada (pedras), cilindro (lenha e chama).

11. **Lagoa**  
    Primitivas: disco (margem e água), esfera (pedras da beira).

12. **Atalaia**  
    Primitivas: cilindro (postes e trilhos), caixa (plataforma, X, parapeito, degraus), pirâmide de palha (telhado).

## Transformações

As transformações do projeto aparecem o tempo todo na cena. A translação posiciona as casas, árvores, poço, a fogueira e a atalaia. Ela também é responsável por mover a câmera no plano XZ e leva o jogador do pé da escada até o topo da torre na atalaia.

A rotação gira os objetos no eixo Y para ficarem voltados para o centro da praça. No portão, cada folha gira em torno da dobradiça. No coqueiro, pequenas rotações foram implementadas para entortarem o tronco aos poucos. Já no poço, o sarilho é rotacionado para que a corda suba ou desça.

A escala muda o tamanho das árvores e dos coqueiros. Também foi implementada para achatar esferas para formar os morros e copas. Já na casa de farinha, deixa o telhado retangular.

Utilizamos `glPushMatrix` e `glPopMatrix` para isolar as transformações e não misturar a matriz de um objeto com a do outro.

## Navegação

Implementamos câmera em primeira pessoa com navegação pelo teclado e mouse. As teclas W, A, S, D movem o personagem, o Shift acelera e o mouse controla o azimute e a elevação. A roda do mouse altera o campo de visão na perspectiva (zoom-in, zoom-out) ou o tamanho da área visível na projeção ortográfica.

Implementamos colisão simples, por círculos no plano XZ. Foi implementada na paliçada, casas, árvores, poço, fogueira e lagoa. Só é possível atravessar a paliçada pelo vão do portão, e só quando ele estiver aberto. Também dá para entrar na muxima e nas ocas pela porta.

A tecla P troca entre perspectiva (`gluPerspective`) e ortográfica (`glOrtho`). A ortográfica serve como vista da planta do quilombo.

## Interações

Foram implementadas as seguintes interações:

- **Portão (E):** abre e fecha as duas folhas, cada uma no respectivo pivô.
- **Poço (F):** desce o balde, enche na água, sobe pingando e, com o balde cheio, despeja. O sarilho gira junto com a corda.
- **Fogueira (L):** acende e apaga a chama e liga ou desliga a luz pontual.
- **Atalaia (E):** sobe e desce a escada, com a câmera interpolada do pé até a plataforma.
- **Dia e noite (N):** muda a iluminação, o céu e a neblina.
- **Histórias (H):** à noite, com a fogueira acesa, abre painéis com relatos e lendas de Palmares.

Essas ações fazem parte da missão “Um dia no Quilombo”, listada no canto da tela.

## Iluminação

Utilizamos o pipeline do OpenGL para a iluminação, com o modelo de reflexão de Phong e sombreamento Gouraud (`GL_SMOOTH`). A cor é calculada nos vértices e interpolada nas faces. As normais vêm das quádricas do GLU e das malhas desenvolvidas. Usamos `GL_NORMALIZE` para que o `glScale` (morros, copas, telhados) não deixe a normal com comprimento diferente de 1, o que causaria distorção do cálculo da luz.

Configuramos o modelo de luz com três opções importantes na inicialização:

- **`GL_LIGHT_MODEL_TWO_SIDE`:** o lado de dentro das paredes (muxima, ocas) também recebe iluminação, para quem entra nas casas não ver faces pretas.
- **`GL_LIGHT_MODEL_LOCAL_VIEWER`:** o brilho especular depende da posição real da câmera, e não de um olho “no infinito”.
- **`GL_SEPARATE_SPECULAR_COLOR`:** o termo especular é somado depois da textura, então o reflexo branco aparece por cima da madeira, da pedra ou da água, em vez de ser tingido pela textura.

A textura entra em `GL_MODULATE`, para que a cor da textura seja multiplicada pela cor da luz. Isso traz mais realismo porque uma mesma casca de árvore, por exemplo, pode ter cores diferentes dependendo do ângulo de iluminação.

### Phong na cena

Para cada luz e material, o OpenGL combina três termos: ambiente, difuso e especular.

No ambiente existe uma luz difusa de entorno sem direção. Utilizamos `GL_LIGHT_MODEL_AMBIENT` global e interpolamos entre azul escuro de noite e cinza claro de dia. Aplicamos 60% da cor difusa no material ambient.

O difuso depende do ângulo entre a normal e a direção da luz (`N · L`); é o que dá o volume aos cilindros, às esferas e às caixas.

O especular é o reflexo concentrado (`R · V` elevado à shininess). É o controle de polimento da superfície (se é fosca ou polida).

### Sol

Aplicamos `GL_LIGHT0` para o sol. A posição foi definida como `w = 0` para ser uma luz direcional. Os raios são paralelos e a distância até o objeto não importa. A direção `(0.45, y, 0.35)` sobe um pouco quando amanhece (`y` vai de 0,35 à noite para 0,8 de dia), assim a luz bate mais de cima no meio-dia.

As cores da luz também mudam com o parâmetro contínuo `dia` (0 = noite, 1 = dia) e é interpolado quando o jogador aperta **N**.

| Componente | Dia | Noite |
|---|---|---|
| Difusa | branco amarelado `(1.0, 0.95, 0.85)` | azul frio fraco `(0.10, 0.12, 0.25)` |
| Especular | quase branca | azulada e bem fraca |
| Ambiente global | cinza claro | azul escuro |

De dia, a aldeia inteira é iluminada pelo sol. De noite, a cena fica escura, preparando o papel da fogueira para iluminação.

### Fogueira

Quando acendemos a fogueira com **L**, ativamos o `GL_LIGHT1` como luz pontual (`w = 1`), posicionada um pouco acima das pedras. A cor é alaranjada: difusa `(1.0, 0.55, 0.2)` e especular um pouco mais suave. A intensidade oscila com o seno no tempo (sensação de tremor) para a luz piscar junto com a chama.

Já que é pontual, usamos uma atenuação `1 / (k_c + k_l · d + k_q · d²)`, sendo a constante 1.0, linear 0.08 e quadrática 0.02. Isso faz a luz ficar mais fraca à medida que se afasta da fogueira.

A geometria da chama é desenhada sem `GL_LIGHTING`, usando blend aditivo `GL_ONE`; dessa forma ela emite cor em vez de ser iluminada. Com isso, a chama parece fonte de luz e o `GL_LIGHT1` é o efeito que essa fonte causa no resto da cena.

### Materiais (`glMaterial`)

Cada tipo de superfície tem um material definido em `primitivas.py`.

| Material | Difusa | Especular | Shininess | Efeito |
|---|---|---|---|---|
| Palha | bege claro | quase zero | 1 | fosca (tetos, esteiras) |
| Reboco | quase branco | bem baixo | 4 | parede mate da muxima |
| Madeira | bege | moderado | 12 | paliçada, postes, portão |
| Pedra | cinza | médio | 20 | poço e pedras da fogueira |
| Folhas | verde claro | baixo | 6 | copas e morros |
| Chão | neutro | zero | 1 | grama e terra |
| Água | azul semitransparente | alto `(1,1,1)` | 90 | lagoa e poço brilham |
| Metal (tacho) | cinza escuro | alto | 40 | reflexo forte na casa de farinha |

O ambient de cada material acompanha a difusa (fator 0,6), para a cena não ficar preta nas faces que não recebem luz direta, sem “lavar” o contraste.

### Efeitos da iluminação no dia e na noite

O céu é representado por uma meia esfera (sky dome) posicionada ao redor do jogador. Sua parte interna recebe a textura do céu, ficando sempre ao fundo da cena.

A mudança entre dia e noite afeta outros elementos além da iluminação. A cor do horizonte e da neblina (`GL_FOG` exponencial), por exemplo, acompanha o mesmo parâmetro `dia`, mantendo a aparência da cena consistente. As sombras projetadas no chão também consideram a direção do sol e variam de intensidade conforme o horário: durante o dia ficam mais visíveis e, à noite, praticamente desaparecem. O sky dome também faz a transição entre as texturas do céu diurno e noturno. Já a lua acompanha a direção da `LIGHT0`, fazendo com que sua posição no céu corresponda à direção da luz utilizada na iluminação da cena.

## Mapeamento de textura

As imagens utilizadas no projeto ficam armazenadas na pasta `texturas/`. Entre elas estão as texturas de grama, terra, palha, reboco, casca, madeira, folhas, pedra, água, céu e a placa de entrada. Cada imagem é carregada uma única vez com Pillow, e os mipmaps são gerados para melhorar a exibição das texturas. Também utilizamos `glScalef` nas coordenadas UV para repetir as imagens nas superfícies maiores, evitando que texturas como grama e terra fiquem distorcidas ou esticadas.

Na placa com o nome “Quilombo dos Palmares”, a imagem é aplicada diretamente sobre a face da tábua. Durante a noite, as histórias são apresentadas na tela por meio de ilustrações utilizadas como texturas 2D.

## Água

Foram implementadas duas águas na cena, utilizando técnicas diferentes: lagoa e poço. A lagoa tem um movimento contínuo da superfície. O poço tem ondas e gotas ligadas à interação do balde.

### Lagoa

A superfície da lagoa é um disco elíptico com `glScalef` diferente em X e Z, com material de água. Tem especular alto, shininess 90 e alfa semitransparente. Desenhamos com blend e `glDepthMask(FALSE)`, assim a transparência não atravessa o z-buffer dos objetos atrás.

O movimento dela não deforma a malha. Em vez disso, a cada quadro usamos uma translação na matriz de textura (`GL_TEXTURE`): `glTranslatef(t · 0.03, t · 0.018, 0)`.

Dessa forma, as coordenadas UV da textura `agua.jpg` andam com o tempo em velocidades diferentes nos eixos u e v. Com isso, temos o resultado de uma impressão de correnteza na superfície, sem precisar recalcular os vértices. A mesma matriz ainda escala a textura (3×1,5) para ela se repetir na elipse. O disco utiliza vários anéis (`gluDisk` com vários rings) para o brilho especular mudar de forma mais suave do meio para a borda.

### Poço

No poço, a água “parada” também é um disco texturizado. O movimento aparece quando o jogador usa o balde (tecla **F**).

Quando o balde chega na superfície da água, geramos ondas: círculos paramétricos (`GL_LINE_LOOP`) onde o raio cresce com a idade (`r = 0.15 + idade · 0.7`) e a opacidade cai até sumir.

Enquanto o balde sobe cheio e durante o despejo da água, são geradas gotas utilizando `GL_POINTS`. Cada gota possui sua própria posição e velocidade vertical, que são atualizadas a cada quadro considerando a gravidade (`v += g·dt` e `y += v·dt`). Quando uma gota atinge a água dentro do poço, ela desaparece ao chegar à superfície. Caso caia fora, desaparece próximo ao chão. Durante o despejo, o balde também gira em torno do pivô da alça, e as gotas acompanham essa inclinação ao sair pela boca do balde.

As ondas e as gotas são desenhadas sobre a superfície da água, sem iluminação e utilizando blend. Esses elementos servem apenas para representar visualmente o efeito da interação com a água.

## Outras técnicas usadas

Além dos recursos exigidos pelo enunciado, implementamos algumas técnicas para melhorar a aparência da cena e o desempenho do projeto:

- **Display lists:** utilizadas no terreno e nos elementos estáticos da cena, evitando executar novamente todos os comandos de desenho a cada atualização.
- **Neblina (`GL_FOG`):** acompanha a cor do horizonte e muda conforme o período do dia.
- **Sombras planares:** projetadas no chão com o auxílio de stencil, considerando a direção do sol.
- **Sky dome:** representa o céu com texturas diferentes para o dia e a noite, incluindo estrelas e lua.
- **Partículas:** utilizadas para representar a chama e as faíscas.
- **HUD:** exibe informações na tela por meio de textos desenhados com Pillow e enviados ao OpenGL.

---

*UFAL — Computação Gráfica — Projeto AB2*
