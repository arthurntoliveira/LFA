"""
Atividade 3, parte 1: análise LÉXICA do JSON.

Transforma o texto em uma lista de TOKENS (as "palavras" do JSON), anotando a
linha e a coluna de cada um. O APND trabalha sobre tokens, não sobre
caracteres: para ele, o texto

    {"nome": "Ana", "idade": 20}

é a sequência   {  string  :  string  ,  string  :  numero  }

Os tokens formam uma linguagem REGULAR (números e strings podem ser descritos
por expressões regulares / autômatos finitos). Não é preciso pilha aqui. A
pilha só é necessária na próxima fase, para checar o aninhamento de { } e [ ],
que é livre de contexto.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# Número JSON: -?(0|[1-9][0-9]*)(.[0-9]+)?([eE][+-]?[0-9]+)?
NUMERO = re.compile(r"-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?")
PALAVRAS = ("true", "false", "null")
ESTRUTURA = "{}[]:,"
ESCAPES = '"\\/bfnrt'
HEX = "0123456789abcdefABCDEF"


@dataclass(frozen=True)
class Token:
    tipo: str      # '{', '}', '[', ']', ':', ',', 'string', 'numero', 'true', 'false', 'null'
    texto: str     # trecho original do arquivo
    linha: int
    coluna: int


class ErroLexico(Exception):
    def __init__(self, mensagem: str, linha: int, coluna: int):
        super().__init__(mensagem)
        self.mensagem, self.linha, self.coluna = mensagem, linha, coluna


def tokenizar(texto: str) -> tuple[list[Token], tuple[int, int]]:
    """Devolve os tokens e a posição (linha, coluna) do fim do arquivo."""
    tokens: list[Token] = []
    i, linha, coluna = 0, 1, 1

    while i < len(texto):
        c = texto[i]

        # Espaços em branco: só avançam a posição.
        if c in " \t\r\n":
            if c == "\n":
                linha, coluna = linha + 1, 1
            else:
                coluna += 1
            i += 1
            continue

        # Símbolos de estrutura: um caractere = um token.
        if c in ESTRUTURA:
            tokens.append(Token(c, c, linha, coluna))
            i, coluna = i + 1, coluna + 1
            continue

        # Strings: de uma aspa até a próxima aspa não escapada.
        if c == '"':
            fim = _fim_da_string(texto, i, linha, coluna)
            tokens.append(Token("string", texto[i:fim], linha, coluna))
            coluna += fim - i
            i = fim
            continue

        # Números.
        m = NUMERO.match(texto, i)
        if m and c in "-0123456789":
            fim = m.end()
            # Um número não pode vir colado a letras/dígitos (ex.: 12abc, 012).
            if fim < len(texto) and (texto[fim].isalnum() or texto[fim] in "._"):
                raise ErroLexico(f"número mal formado: {texto[i:fim + 1]!r}", linha, coluna)
            tokens.append(Token("numero", m.group(), linha, coluna))
            coluna += fim - i
            i = fim
            continue
        if c in "-0123456789":
            raise ErroLexico("número mal formado", linha, coluna)

        # true, false, null.
        if c.isalpha():
            j = i
            while j < len(texto) and (texto[j].isalnum() or texto[j] == "_"):
                j += 1
            palavra = texto[i:j]
            if palavra not in PALAVRAS:
                raise ErroLexico(f"palavra desconhecida {palavra!r} "
                                 f"(strings precisam de aspas duplas)", linha, coluna)
            tokens.append(Token(palavra, palavra, linha, coluna))
            coluna += j - i
            i = j
            continue

        raise ErroLexico(f"caractere inesperado {c!r}", linha, coluna)

    return tokens, (linha, coluna)


def _fim_da_string(texto: str, inicio: int, linha: int, coluna: int) -> int:
    """Índice logo após a aspa que fecha a string que começa em `inicio`."""
    i = inicio + 1
    while i < len(texto):
        c = texto[i]
        col = coluna + (i - inicio)
        if c == '"':
            return i + 1
        if c == "\n":
            raise ErroLexico("string não foi fechada antes do fim da linha", linha, coluna)
        if ord(c) < 0x20:
            raise ErroLexico("caractere de controle dentro da string", linha, col)
        if c == "\\":
            seguinte = texto[i + 1] if i + 1 < len(texto) else ""
            if seguinte == "u":
                digitos = texto[i + 2:i + 6]
                if len(digitos) < 4 or any(h not in HEX for h in digitos):
                    raise ErroLexico("escape \\u precisa de 4 dígitos hexadecimais", linha, col)
                i += 6
                continue
            if not seguinte or seguinte not in ESCAPES:
                raise ErroLexico(f"escape inválido '\\{seguinte}'", linha, col)
            i += 2
            continue
        i += 1
    raise ErroLexico("string não foi fechada", linha, coluna)
