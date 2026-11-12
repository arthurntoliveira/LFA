# Autômato com Pilha Não Determinístico e Gramáticas Livres de Contexto

Trabalho da disciplina de Linguagens Formais e Autômatos, **Tema 4**.

**Integrantes:** _(preencher)_

## Enunciado

1. Receber uma GLC e realizar a conversão para o APND.
2. Implementar um APND com busca em largura (BFS) ou profundidade (DFS) para
   rastrear os caminhos da pilha.
3. Construir um validador de linguagens marcadas (XML/HTML simples ou JSON),
   validando o fechamento correto de tags aninhadas e identificando erros de
   sintaxe (linha/coluna) onde a estrutura falhou.

O grupo escolheu **JSON** para a atividade 3. Em JSON, o papel das "tags
aninhadas" é feito pelos pares `{ }` (objetos) e `[ ]` (listas): cada abertura
precisa ser fechada pelo símbolo certo, na ordem inversa.

### Onde cada item do enunciado é atendido

| Item do enunciado | Onde está | Como conferir |
|---|---|---|
| 1. Receber uma GLC e converter para APND | `lfa/glc.py` (lê a GLC de um arquivo .txt), `lfa/conversao.py` (construção GLC → APND) | `python main.py converter gramaticas/anbn.txt` |
| 2. APND com BFS ou DFS rastreando os caminhos da pilha | `lfa/apnd.py`, função `simular` (as duas estratégias) | `python main.py simular gramaticas/anbn.txt aabb --busca profundidade --explorados` ou o painel |
| 3. Validador de JSON: fechamento de `{ }`/`[ ]` aninhados e erro com linha/coluna | `lfa/lexico_json.py` + `lfa/validador_json.py`, que usam a GLC `gramaticas/json.txt` convertida pelo item 1 e simulada pelo item 2 | `python main.py validar exemplos/erro_fechamento.json` |

## Resumo da solução

As três atividades formam um único fluxo. A atividade 3 não tem um validador
escrito à mão: ela usa as atividades 1 e 2.

```
 gramaticas/json.txt ──(1) conversão GLC → APND──▶ APND do JSON
                                                         │
 arquivo .json ──análise léxica──▶ tokens ──(2) simulação BFS/DFS──▶ válido
                 (linha/coluna)                                     ou erro em linha/coluna
```

- **Atividade 1**: lê qualquer gramática de um arquivo texto e constrói o APND
  equivalente.
- **Atividade 2**: simula qualquer APND explorando a árvore de configurações
  por largura ou por profundidade e devolve o caminho de aceitação, com o
  conteúdo da pilha em cada passo.
- **Atividade 3**: escreve a gramática do JSON como um arquivo da atividade 1,
  converte para APND e roda a simulação da atividade 2 sobre os tokens do
  arquivo. Quando o JSON é inválido, o erro é localizado pelo ponto mais
  distante que algum caminho do autômato conseguiu ler.

## Como executar

É preciso ter o Python 3.9 ou mais novo. O projeto não usa bibliotecas externas.

A forma mais simples é abrir o **menu interativo**, executando o programa sem
argumentos. O menu permite escolher a atividade, a gramática e o arquivo pelo
número:

```
python main.py
```

Também é possível chamar cada atividade direto pela linha de comando:

```
python main.py converter gramaticas/anbn.txt                       # atividade 1
python main.py simular   gramaticas/anbn.txt aabb                  # atividade 2 (BFS)
python main.py simular   gramaticas/palindromos.txt abba --busca profundidade --explorados
python main.py validar   exemplos/valido.json                      # atividade 3
python main.py validar   exemplos/erro_fechamento.json
python main.py painel                                              # painel no navegador
python -m unittest discover testes -v                              # testes
```

| Opção | Comandos | Efeito |
|---|---|---|
| `--busca largura` / `--busca profundidade` | `simular`, `validar` | estratégia de busca (padrão: largura) |
| `--explorados` | `simular`, `validar` | lista todas as configurações na ordem em que foram visitadas |
| `--rastro` | `validar` | mostra o caminho de aceitação do APND quando o JSON é válido |

### Painel no navegador

`python main.py painel` (ou a opção 4 do menu) sobe um servidor local, só com a
biblioteca padrão, e abre o painel no navegador. Ele usa a mesma conversão e a
mesma busca do Python; nenhuma lógica é refeita em JavaScript.

- escolha ou edite a gramática, digite a cadeia e escolha BFS ou DFS;
- percorra os passos com Início, Voltar, Avançar, Fim, Reproduzir, o slider ou as setas do teclado;
- alterne entre o **caminho de aceitação** e a **busca completa** (todas as
  configurações na ordem em que foram visitadas, inclusive os ramos que falharam);
- acompanhe a fita, o estado, a transição usada e a pilha, que anima cada
  empilhamento e desempilhamento e mostra o tamanho antes → depois;
- leia, a cada passo, **qual das 4 regras** da construção foi usada (com a
  mesma cor na legenda, na tabela δ e no passo atual) e uma **explicação em
  português** do que aconteceu: qual variável foi trocada, quais eram as outras
  produções possíveis (o não determinismo), qual terminal foi casado com a fita;
- veja a **derivação mais à esquerda** sendo construída (`S ⇒ a S b ⇒ a a S b b ⇒ a a b b`):
  o que já foi lido + a pilha sem o `$` é sempre uma forma sentencial;
- na busca completa, veja o **nível do nó na árvore**, quem é o pai, se ele faz
  parte do caminho de aceitação e quando um ramo é um **beco sem saída**;
- com `json.txt`, digite um JSON de verdade (`{"nota": [8.5, 9]}`): a fita mostra
  o tipo de cada token com o texto original embaixo, e a rejeição informa a
  linha e a coluna do erro.

O painel limita a busca a 5000 configurações. Encerre com Ctrl+C no terminal.

Na entrada do `simular`, uma palavra sem espaços é lida caractere a caractere
(`aabb`). Com espaços, cada palavra é um símbolo (`"A b C"`).

## Estrutura do projeto

```
main.py                 menu interativo e linha de comando (tabelas e mensagens)
lfa/
  glc.py                atividade 1: representação e leitura da GLC
  conversao.py          atividade 1: construção GLC → APND
  apnd.py               atividade 2: APND, configurações e busca BFS/DFS
  lexico_json.py        atividade 3: tokens do JSON com linha e coluna
  validador_json.py     atividade 3: une léxico + APND e monta a mensagem de erro
  painel.py             servidor local do painel (atividade 2)
painel/index.html       página do painel: passo a passo e pilha animada
gramaticas/
  anbn.txt              { aⁿbⁿ | n ≥ 0 }
  palindromos.txt       palíndromos sobre {a, b}
  json.txt              gramática do JSON usada pelo validador
exemplos/               arquivos .json válidos e com erros
testes/test_trabalho.py testes automáticos
```

### Roteiro para estudar o código

Os arquivos foram escritos para serem lidos nesta ordem; cada um começa com um
comentário explicando a teoria que ele implementa.

1. `lfa/glc.py`: como uma gramática `G = (V, Σ, P, S)` vira dados (`Producao`, `GLC`).
2. `lfa/conversao.py`: as 4 regras da construção, uma chamada `nova(...)` por regra.
3. `lfa/apnd.py`: `Transicao`, `Configuracao` e a função `simular`. O laço da
   busca está dividido em 4 passos numerados (escolher o nó, testar a aceitação,
   checar o limite, expandir); a única diferença entre BFS e DFS é a linha do passo 1.
4. `lfa/lexico_json.py`: como o texto vira tokens (`{ s : n }`), com linha e coluna.
5. `lfa/validador_json.py`: junta tudo e transforma o "ponto mais distante" da
   busca em uma mensagem de erro.
6. `main.py` e `lfa/painel.py`: só apresentação (terminal e navegador); não
   têm lógica de autômato.

---

## Atividade 1: conversão de GLC para APND

### Fundamentação

Uma **GLC** é uma quádrupla `G = (V, Σ, P, S)`: variáveis, terminais, produções
`A → w` e variável inicial. Um **APND** é uma sêxtupla `M = (Q, Σ, Γ, δ, q0, F)`.
Ele é um autômato finito com uma pilha, e a função de transição
`δ(estado, símbolo lido ou λ, topo desempilhado ou λ)` devolve um **conjunto**
de pares `(novo estado, símbolos empilhados)`. O não determinismo é justamente
poder ter mais de uma opção ao mesmo tempo.

Pelo teorema de equivalência, toda linguagem gerada por uma GLC é reconhecida
por algum APND, e vice-versa. A demonstração da ida é construtiva, e foi ela
que implementamos (Sipser, *Introdução à Teoria da Computação*, seção 2.2).

### Construção

O APND tem três estados e simula uma **derivação mais à esquerda**: a pilha
guarda a parte da forma sentencial que ainda não foi casada com a entrada.

| De → para | Transição | Quando | Papel |
|---|---|---|---|
| q0 → q1 | `λ, λ → S $` | uma vez, no início | empilha o marcador de fundo `$` e a variável inicial |
| q1 → q1 | `λ, A → w` | uma por produção `A → w` | troca a variável do topo pelo lado direito da produção |
| q1 → q1 | `a, a → λ` | uma por terminal `a` | casa o terminal do topo com o próximo símbolo da entrada |
| q1 → q2 | `λ, $ → λ` | uma vez | o fundo apareceu: tudo foi casado, vai para a aceitação |

Quando uma variável tem várias produções, existem várias transições com o
mesmo `(q1, λ, A)`. É ali que o autômato "adivinha" qual produção usar. Ao
empilhar `w`, o primeiro símbolo de `w` fica no topo, para que a derivação
continue sempre pela variável mais à esquerda.

### Formato do arquivo de gramática

```
# comentário
S -> a S b | λ
```

Os símbolos são separados por espaço. Variáveis são os símbolos que aparecem
do lado esquerdo de alguma regra, e os demais são terminais. A primeira regra
define a variável inicial. A palavra vazia pode ser escrita como `λ`, `ε`, `&`
ou `eps`. O símbolo `$` é reservado para o fundo da pilha.

### Exemplo de execução

```
> python main.py converter gramaticas/anbn.txt
Gramática G = (V, Σ, P, S)
  V (variáveis): S
  Σ (terminais): a, b
  S (inicial):   S
  P (produções):
    S → a S b
    S → λ

APND M = (Q, Σ, Γ, δ, q0, F)
  Q (estados):         q0, q1, q2
  Σ (entrada):         a, b
  Γ (pilha):           S, a, b, $
  q0 (inicial):        q0
  F (aceitação):       q2
  δ (transições):
  nº  de  para  transição     significado
  1.  q0  q1    λ, λ → S $    inicializa a pilha
  2.  q1  q1    λ, S → a S b  produção S → a S b
  3.  q1  q1    λ, S → λ      produção S → λ
  4.  q1  q1    a, a → λ      casa o terminal a
  5.  q1  q1    b, b → λ      casa o terminal b
  6.  q1  q2    λ, $ → λ      fundo da pilha: aceita
```

---

## Atividade 2: simulação do APND com BFS e DFS

### Ideia

Uma **configuração** descreve o autômato num instante:
`(estado, quanto da entrada já foi lido, conteúdo da pilha)`. A partir de uma
configuração, cada transição aplicável gera uma configuração filha. Assim, a
execução não determinística vira uma **árvore de configurações**. A entrada é
aceita se algum ramo chega a um estado de aceitação com a entrada toda lida
(aceitação por estado final).

O simulador (`lfa/apnd.py`, função `simular`) percorre essa árvore:

- **BFS** usa a fronteira como **fila** e visita a árvore nível por nível.
  Encontra o caminho de aceitação mais curto e não fica preso num ramo infinito.
- **DFS** usa a fronteira como **pilha** e segue um ramo até ele morrer antes
  de voltar (backtracking). Costuma visitar menos configurações quando a
  primeira escolha é boa, mas um ramo infinito pode prendê-la.

No código, a única diferença entre as duas é a linha que retira o próximo nó
da fronteira (`popleft()` na BFS, `pop()` na DFS).

Cada nó da árvore guarda o nó pai e a transição usada. Quando a aceitação é
encontrada, o programa sobe pelos pais e reconstrói o caminho: esse é o
**rastro da pilha** pedido no enunciado. Com `--explorados`, o programa mostra
também todos os nós visitados, na ordem da busca, o que permite comparar BFS e
DFS sobre a mesma entrada.

Dois cuidados garantem que a busca termina:

1. um conjunto de configurações já vistas evita repetir trabalho e evita
   ciclos;
2. um limite de configurações visitadas (padrão: `100 000 + 50 × tamanho da
   entrada`). Gramáticas com recursão à esquerda (`E → E + n`) geram ramos
   infinitos. Nesse caso, o resultado é **inconclusivo**, e nunca um falso
   "rejeitada". O comando `converter` avisa quando a gramática tem recursão
   direta à esquerda.

### Exemplo: aⁿbⁿ com BFS

```
> python main.py simular gramaticas/anbn.txt aabb
Entrada: a a b b
Busca em largura (BFS): 14 configurações visitadas, fronteira máxima de 3.

Resultado: ACEITA

Caminho de aceitação (o topo da pilha fica à esquerda):
  passo  estado  falta ler  pilha      transição usada
  0      q0      a a b b    λ          início
  1      q1      a a b b    S $        1. λ, λ → S $
  2      q1      a a b b    a S b $    2. λ, S → a S b
  3      q1      a b b      S b $      4. a, a → λ
  4      q1      a b b      a S b b $  2. λ, S → a S b
  5      q1      b b        S b b $    4. a, a → λ
  6      q1      b b        b b $      3. λ, S → λ
  7      q1      b          b $        5. b, b → λ
  8      q1      λ          $          5. b, b → λ
  9      q2      λ          λ          6. λ, $ → λ
```

Quando a palavra é rejeitada, o programa informa até onde os caminhos chegaram
e o que eles esperavam ler:

```
> python main.py simular gramaticas/anbn.txt aabbb
Resultado: REJEITADA (nenhum caminho leva à aceitação)
Nenhum caminho conseguiu ler o símbolo 5 ('b'); esperava-se: fim da entrada.
```

### Comparação BFS × DFS (palíndromos)

A gramática de palíndromos obriga o autômato a adivinhar onde fica o meio da
palavra, o que gera muitos ramos.

| Entrada | Estratégia | Configurações visitadas | Fronteira máxima |
|---|---|---|---|
| `aba`  | BFS | 27 | 7  |
| `aba`  | DFS | 24 | 16 |
| `abba` | DFS | 29 | 19 |

A BFS mantém a fronteira pequena porque visita os nós por nível. A DFS
acumula na pilha de busca as alternativas que ainda não testou.

---

## Atividade 3: validador de JSON

### Por que o JSON precisa de um autômato com pilha

Objetos `{ }` e listas `[ ]` podem ser aninhados sem limite de profundidade, e
cada abertura precisa ser fechada pelo símbolo correspondente, na ordem
inversa. É a mesma estrutura da linguagem de parênteses balanceados, que é
livre de contexto e **não é regular**: um autômato finito não consegue contar
aberturas sem limite. A pilha do APND faz exatamente esse controle.

### Duas fases

1. **Análise léxica** (`lfa/lexico_json.py`): transforma o texto em tokens
   (`{ } [ ] : , s n t f u`), anotando a linha e a coluna
   de cada um. Os tokens formam uma linguagem regular (o número é reconhecido
   por uma expressão regular), então essa fase não precisa de pilha. Aqui são
   detectados erros como aspas simples, string não fechada, escape inválido e
   número mal formado (`01`, `1.`).
2. **Análise sintática** (`lfa/validador_json.py`): a gramática
   `gramaticas/json.txt` é convertida pela atividade 1, e o APND resultante
   simula a sequência de tipos de token com a atividade 2.

Na notação padrão, variáveis são uma letra maiúscula e terminais são minúsculas
ou pontuação: `s` = string, `n` = número, `t` = true, `f` = false, `u` = null;
`S` = valor, `O` = objeto, `M` = membros, `A` = mais pares, `P` = par, `L` = lista,
`E` = elementos, `B` = mais valores.

```
S -> O | L | s | n | t | f | u
O -> { M }
M -> P A | λ
A -> , P A | λ
P -> s : S
L -> [ E ]
E -> S B | λ
B -> , S B | λ
```

A gramática foi escrita sem recursão à esquerda (as listas usam `A` e `B`). Assim, todo ramo errado morre poucos passos depois de ser
criado, e a busca cresce de forma proporcional ao tamanho do arquivo.

### Como o erro é localizado

Se nenhum caminho aceita, o validador usa o **ponto mais distante** que algum
caminho do APND conseguiu ler. O token nessa posição é o primeiro que nenhuma
possibilidade da gramática aceita, e a linha e a coluna vêm desse token. Os
caminhos que chegaram até lá dizem o que era **esperado**, ou seja, quais
terminais estavam no topo da pilha.

Quando o erro acontece num fechamento (aparece o fechamento errado ou o
arquivo termina), a mensagem também aponta qual `{` ou `[` ficou sem fechar.

### Exemplos

```
> python main.py validar exemplos/erro_fechamento.json
JSON INVÁLIDO
  Linha 3, coluna 25: erro sintático: encontrado '}'; esperado ',' ou ']'. O '[' aberto na linha 3, coluna 12, não foi fechado

     3 |   "notas": [8.5, 9, 7.25}
       |                         ^
```

```
> python main.py validar exemplos/erro_nao_fechado.json
JSON INVÁLIDO
  Linha 6, coluna 1: erro sintático: encontrado fim do arquivo; esperado ',' ou '}'. O '{' aberto na linha 1, coluna 1, não foi fechado
```

```
> python main.py validar exemplos/erro_virgula.json
JSON INVÁLIDO
  Linha 3, coluna 3: erro sintático: encontrado a string "idade"; esperado ',' ou '}'

     3 |   "idade": 21
       |   ^
```

```
> python main.py validar exemplos/erro_lexico.json
JSON INVÁLIDO
  Linha 2, coluna 12: erro léxico: caractere inesperado "'"

     2 |   "aluno": 'Ana'
       |            ^
```

Com `--rastro`, o validador mostra, para um JSON válido, a pilha do APND a
cada passo (derivação mais à esquerda do arquivo).

---

## Testes

`python -m unittest discover testes -v` roda 20 testes, todos passando:

- **Conversão**: leitura da gramática, transições geradas e gramáticas inválidas.
- **Simulação**: para aⁿbⁿ e palíndromos, 16 palavras em cada estratégia,
  comparadas com a definição matemática da linguagem. Também verificam que
  cada passo do caminho é uma transição válida, que BFS e DFS visitam em ordens
  diferentes e que a recursão à esquerda termina como inconclusiva.
- **Validador**: JSONs válidos (inclusive com 20 níveis de aninhamento), linha
  e coluna de erros sintáticos e léxicos, e os arquivos de `exemplos/`.
- **Teste diferencial**: 400 JSONs gerados aleatoriamente, 60% deles
  corrompidos de propósito, comparados com o `json.loads` da biblioteca padrão
  do Python. Os dois dão o mesmo veredito em todos os casos.
- **Painel**: sobe o servidor e faz pedidos de verdade (aceitação, rejeição,
  JSON digitado direto com linha/coluna do erro e pedidos inválidos).

## Limitações e decisões

- **Desempenho**: o APND é simulado de forma genérica, testando todas as
  alternativas. Um JSON de 580 KB (108 mil tokens) é validado em cerca de 8 s
  com BFS e 5 s com DFS. Um analisador determinístico (LL(1)) seria mais
  rápido, mas o objetivo do trabalho é usar o APND.
- **Memória da DFS**: a DFS guarda na fronteira as alternativas ainda não
  testadas de cada passo do caminho atual. Com JSON muito aninhado, a
  fronteira cresce junto com a profundidade.
- **Mensagem de abertura pendente**: para apontar qual `{` ou `[` ficou
  aberto, o validador faz uma varredura simples dos tokens anteriores ao erro.
  Ela serve só para a mensagem: quem decide se o JSON é válido é o APND.
- **Coluna**: um caractere de tabulação conta como uma coluna.
- Valores que o `json.loads` aceita mas que não fazem parte do padrão JSON
  (`NaN`, `Infinity`) são rejeitados, como manda a RFC 8259.

## Referências

- SIPSER, M. *Introdução à Teoria da Computação*. 2ª ed. Cengage Learning. Cap. 2.
- HOPCROFT, J.; MOTWANI, R.; ULLMAN, J. *Introdução à Teoria de Autômatos, Linguagens e Computação*. Cap. 5 e 6.
- RFC 8259: *The JavaScript Object Notation (JSON) Data Interchange Format*.
