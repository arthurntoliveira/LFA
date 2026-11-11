"""
Gramática Livre de Contexto (GLC).

Uma GLC é a quádrupla G = (V, Σ, P, S):
    V  variáveis (não terminais)
    Σ  terminais
    P  produções, na forma  A → w,  com A ∈ V e w ∈ (V ∪ Σ)*
    S  variável inicial

Formato do arquivo de gramática (uma regra por linha):

    # comentário
    S -> a S b | λ

- Os símbolos do lado direito são separados por espaço.
- Variáveis são os símbolos que aparecem do lado esquerdo de alguma regra;
  todos os outros símbolos são terminais.
- A variável inicial é o lado esquerdo da primeira regra.
- A palavra vazia pode ser escrita como  λ, ε, &  ou  eps.
"""

from __future__ import annotations

from dataclasses import dataclass

VAZIO = ("λ", "ε", "&", "eps")


@dataclass(frozen=True)
class Producao:
    esquerda: str              # A
    direita: tuple[str, ...]   # w  (tupla vazia = λ)

    def __str__(self) -> str:
        return f"{self.esquerda} → {' '.join(self.direita) or 'λ'}"


@dataclass
class GLC:
    variaveis: list[str]
    terminais: list[str]
    producoes: list[Producao]
    inicial: str

    def producoes_de(self, variavel: str) -> list[Producao]:
        return [p for p in self.producoes if p.esquerda == variavel]

    def recursoes_a_esquerda(self) -> list[str]:
        """Variáveis com recursão direta à esquerda (A → A ...)."""
        return sorted({p.esquerda for p in self.producoes
                       if p.direita and p.direita[0] == p.esquerda})


def ler_gramatica(texto: str) -> GLC:
    """Transforma o texto de uma gramática em um objeto GLC."""
    regras: list[tuple[str, list[str]]] = []   # (lado esquerdo, alternativas)

    for numero, linha in enumerate(texto.splitlines(), start=1):
        linha = linha.split("#", 1)[0].strip()
        if not linha:
            continue
        if "->" not in linha:
            raise ValueError(f"linha {numero}: falta '->' em {linha!r}")
        esquerda, direita = (parte.strip() for parte in linha.split("->", 1))
        if not esquerda or " " in esquerda:
            raise ValueError(f"linha {numero}: o lado esquerdo deve ser uma única variável")
        regras.append((esquerda, direita.split("|")))

    if not regras:
        raise ValueError("a gramática não tem nenhuma regra")

    # Variáveis: lados esquerdos, na ordem em que aparecem.
    variaveis: list[str] = []
    for esquerda, _ in regras:
        if esquerda not in variaveis:
            variaveis.append(esquerda)

    producoes: list[Producao] = []
    terminais: list[str] = []
    for esquerda, alternativas in regras:
        for alternativa in alternativas:
            simbolos = [s for s in alternativa.split() if s not in VAZIO]
            for s in simbolos:
                if s not in variaveis and s not in terminais:
                    terminais.append(s)
            producoes.append(Producao(esquerda, tuple(simbolos)))

    return GLC(variaveis, terminais, producoes, inicial=variaveis[0])


def ler_arquivo_gramatica(caminho: str) -> GLC:
    # "utf-8-sig" ignora o BOM que o Bloco de Notas pode gravar no início do arquivo.
    with open(caminho, encoding="utf-8-sig") as arquivo:
        return ler_gramatica(arquivo.read())
