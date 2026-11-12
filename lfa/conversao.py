"""
Atividade 1: conversão de uma GLC em um APND equivalente.

Construção clássica do livro do Sipser ("Introdução à Teoria da Computação"),
usada para provar que toda linguagem livre de contexto é reconhecida por um AP.
O APND tem só três estados e imita uma DERIVAÇÃO MAIS À ESQUERDA da gramática,
usando a pilha para guardar a parte da forma sentencial que ainda falta gerar:

    q0 ── λ, λ → S $ ──▶ q1 ── λ, $ → λ ──▶ q2 (aceitação)
                         ↺  λ, A → w   para cada produção  A → w
                         ↺  a, a → λ   para cada terminal  a

1. q0 → q1:  λ, λ → S $
   Empilha o marcador de fundo $ e, por cima dele, a variável inicial S.
2. q1 → q1:  λ, A → w          (uma para cada produção A → w)
   Se o topo é uma variável, troca-a pelo lado direito de uma produção.
   Quando A tem várias produções, há várias transições possíveis:
   é AQUI que está o não determinismo.
3. q1 → q1:  a, a → λ          (uma para cada terminal a)
   Se o topo é um terminal, ele precisa ser igual ao próximo símbolo da
   entrada: lê o símbolo e desempilha.
4. q1 → q2:  λ, $ → λ
   Se o $ voltou ao topo, tudo o que foi empilhado já foi casado com a
   entrada. Vai para o estado de aceitação.
"""

from __future__ import annotations

from .apnd import APND, Transicao
from .glc import GLC

FUNDO = "$"


def glc_para_apnd(g: GLC) -> APND:
    if FUNDO in g.variaveis or FUNDO in g.terminais:
        raise ValueError(f"o símbolo {FUNDO!r} é reservado para o fundo da pilha")

    transicoes: list[Transicao] = []

    def nova(origem, le, desempilha, destino, empilha, descricao):
        """Acrescenta uma transição numerada. "" em `le`/`desempilha` significa λ."""
        transicoes.append(Transicao(len(transicoes) + 1, origem, le, desempilha,
                                    destino, tuple(empilha), descricao))

    #   nova(origem, lê, desempilha, destino, empilha, descrição)
    # Regra 1: q0 → q1:  λ, λ → S $
    nova("q0", "", "",         "q1", (g.inicial, FUNDO), "inicializa a pilha")
    # Regra 2: q1 → q1:  λ, A → w   (uma por produção: aqui nasce o não determinismo)
    for p in g.producoes:
        nova("q1", "", p.esquerda, "q1", p.direita,          f"produção {p}")
    # Regra 3: q1 → q1:  a, a → λ   (uma por terminal)
    for a in g.terminais:
        nova("q1", a,  a,          "q1", (),                 f"casa o terminal {a}")
    # Regra 4: q1 → q2:  λ, $ → λ
    nova("q1", "", FUNDO,      "q2", (),                 "fundo da pilha: aceita")

    return APND(
        estados=["q0", "q1", "q2"],
        alfabeto_entrada=list(g.terminais),
        alfabeto_pilha=list(g.variaveis) + list(g.terminais) + [FUNDO],
        transicoes=transicoes,
        inicial="q0",
        aceitacao={"q2"},
    )
