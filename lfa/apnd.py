"""
Autômato com Pilha Não Determinístico (APND) e sua simulação.

Um APND é a sêxtupla M = (Q, Σ, Γ, δ, q0, F):
    Q   estados
    Σ   alfabeto de entrada
    Γ   alfabeto da pilha
    δ   transições:  δ(estado, lê, desempilha) → (novo estado, empilha)
    q0  estado inicial
    F   estados de aceitação

"Não determinístico" quer dizer que, a partir de uma mesma situação, várias
transições podem ser possíveis ao mesmo tempo. Para simular isso no
computador, exploramos TODAS as possibilidades como uma árvore de busca:

- cada nó da árvore é uma CONFIGURAÇÃO (estado, posição na entrada, pilha);
- os filhos de um nó são as configurações alcançáveis com uma transição;
- a entrada é aceita se ALGUM caminho chega a um estado de aceitação
  depois de ler a entrada inteira.

A ordem em que os nós são visitados define a estratégia:
- busca em LARGURA (BFS): fila  — visita nível por nível;
- busca em PROFUNDIDADE (DFS): pilha — segue um caminho até o fim antes
  de voltar e tentar o próximo.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field

FIM_DA_ENTRADA = "fim da entrada"


def separar_entrada(texto: str) -> list[str]:
    """Com espaços, cada palavra é um símbolo ("{ string : numero }");
    sem espaços, cada caractere é um símbolo ("aabb")."""
    texto = texto.strip()
    if texto == "λ":                   # λ sozinho é a cadeia vazia
        return []
    return texto.split() if " " in texto else list(texto)


@dataclass(frozen=True)
class Transicao:
    numero: int
    origem: str
    le: str                    # símbolo de entrada lido ("" = λ, não lê nada)
    desempilha: str            # símbolo retirado do topo ("" = λ, não retira nada)
    destino: str
    empilha: tuple[str, ...]   # símbolos colocados na pilha; o 1º fica no topo
    descricao: str = ""

    def __str__(self) -> str:
        empilha = " ".join(self.empilha) or "λ"
        return (f"δ({self.origem}, {self.le or 'λ'}, {self.desempilha or 'λ'})"
                f" → ({self.destino}, {empilha})")


@dataclass(frozen=True)
class Configuracao:
    """Situação instantânea do autômato. A pilha é uma tupla: índice 0 = topo."""
    estado: str
    posicao: int               # quantos símbolos da entrada já foram lidos
    pilha: tuple[str, ...]


@dataclass
class No:
    """Nó da árvore de busca: a configuração e como chegamos nela."""
    id: int
    config: Configuracao
    pai: "No | None"
    transicao: "Transicao | None"


@dataclass
class APND:
    estados: list[str]
    alfabeto_entrada: list[str]
    alfabeto_pilha: list[str]
    transicoes: list[Transicao]
    inicial: str
    aceitacao: set[str]

    def transicoes_possiveis(self, config: Configuracao, entrada: list[str]):
        """Todas as transições que podem ser usadas a partir de `config`."""
        proximo = entrada[config.posicao] if config.posicao < len(entrada) else None
        topo = config.pilha[0] if config.pilha else None
        for t in self.transicoes:
            if t.origem != config.estado:
                continue
            if t.le and t.le != proximo:
                continue
            if t.desempilha and t.desempilha != topo:
                continue
            yield t

    def aplicar(self, config: Configuracao, t: Transicao) -> Configuracao:
        """Executa a transição `t` e devolve a nova configuração."""
        resto = config.pilha[1:] if t.desempilha else config.pilha
        return Configuracao(
            estado=t.destino,
            posicao=config.posicao + (1 if t.le else 0),
            pilha=t.empilha + resto,
        )


@dataclass
class Resultado:
    aceita: bool | None            # None = limite atingido, sem conclusão
    caminho: list[No]              # da raiz até a aceitação (vazio se rejeitou)
    explorados: list[No]           # nós na ordem em que foram visitados
    total_explorados: int
    maior_fronteira: int           # maior tamanho da fila/pilha de busca
    mais_longe: int                # maior posição da entrada que algum caminho alcançou
    esperados: set[str] = field(default_factory=set)  # o que se esperava ler lá


def simular(apnd: APND, entrada: list[str], estrategia: str = "largura",
            limite: int | None = None, guardar_explorados: bool = False) -> Resultado:
    """
    Procura um caminho de aceitação para `entrada`.

    estrategia: "largura" (BFS) ou "profundidade" (DFS).
    limite: número máximo de configurações visitadas. Algumas gramáticas
            (ex.: com recursão à esquerda) geram caminhos infinitos; o limite
            impede que o programa trave. O padrão cresce com o tamanho da
            entrada, porque entradas maiores precisam de mais passos.
    """
    if estrategia not in ("largura", "profundidade"):
        raise ValueError("estratégia deve ser 'largura' ou 'profundidade'")
    if limite is None:
        limite = 100_000 + 50 * len(entrada)

    raiz = No(0, Configuracao(apnd.inicial, 0, ()), None, None)
    fronteira: deque[No] = deque([raiz])   # nós gerados e ainda não visitados
    vistos = {raiz.config}                 # evita visitar a mesma configuração 2 vezes
    explorados: list[No] = []
    total = 0
    maior_fronteira = 1
    proximo_id = 1

    # Para relatar erros: o ponto mais distante da entrada que algum caminho
    # alcançou e quais símbolos os caminhos que chegaram lá esperavam ler.
    mais_longe = 0
    esperados: set[str] = set()

    while fronteira:
        # A ÚNICA diferença entre BFS e DFS está nesta linha:
        no = fronteira.popleft() if estrategia == "largura" else fronteira.pop()
        config = no.config
        total += 1
        if guardar_explorados:
            explorados.append(no)

        # Aceita: estado de aceitação e entrada toda lida.
        if config.estado in apnd.aceitacao and config.posicao == len(entrada):
            caminho = []
            while no is not None:
                caminho.append(no)
                no = no.pai
            return Resultado(True, caminho[::-1], explorados, total,
                             maior_fronteira, len(entrada))

        if total >= limite:
            return Resultado(None, [], explorados, total, maior_fronteira,
                             mais_longe, esperados)

        transicoes = list(apnd.transicoes_possiveis(config, entrada))

        # Registro do ponto mais distante (usado nas mensagens de erro).
        if config.posicao > mais_longe:
            mais_longe, esperados = config.posicao, set()
        if config.posicao == mais_longe:
            for t in apnd.transicoes:      # o que este caminho conseguiria ler
                if (t.origem == config.estado and t.le
                        and (not t.desempilha or config.pilha[:1] == (t.desempilha,))):
                    esperados.add(t.le)
            if config.estado in apnd.aceitacao:
                esperados.add(FIM_DA_ENTRADA)

        # Na DFS a fronteira é uma pilha: empilhamos ao contrário para que a
        # primeira transição seja a primeira a ser tentada.
        if estrategia == "profundidade":
            transicoes.reverse()

        for t in transicoes:
            nova = apnd.aplicar(config, t)
            if nova in vistos:
                continue
            vistos.add(nova)
            fronteira.append(No(proximo_id, nova, no, t))
            proximo_id += 1
        maior_fronteira = max(maior_fronteira, len(fronteira))

    return Resultado(False, [], explorados, total, maior_fronteira,
                     mais_longe, esperados)
