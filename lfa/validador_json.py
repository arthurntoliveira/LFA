"""
Atividade 3: validador de JSON.

Junta as três atividades:
    1. lê a gramática do JSON (gramaticas/json.txt) e a converte em APND;
    2. o texto é quebrado em tokens (lexico_json.py);
    3. o APND simula a entrada (busca em largura ou profundidade).

Se nenhum caminho do APND aceita, o erro é apontado no ponto MAIS DISTANTE
que algum caminho conseguiu ler: é o primeiro token que nenhuma
possibilidade da gramática consegue aceitar. A linha e a coluna vêm do token.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from .apnd import FIM_DA_ENTRADA, APND, Resultado, simular
from .conversao import glc_para_apnd
from .glc import ler_arquivo_gramatica
from .lexico_json import ErroLexico, Token, tokenizar

GRAMATICA_JSON = Path(__file__).resolve().parent.parent / "gramaticas" / "json.txt"

INICIOS_DE_VALOR = {"{", "[", "s", "n", "t", "f", "u"}
NOMES = {"s": "uma string", "n": "um número", "t": "true", "f": "false", "u": "null",
         FIM_DA_ENTRADA: "o fim do arquivo"}
PARES = {"{": "}", "[": "]"}


@dataclass
class Relatorio:
    valido: bool | None              # None = não foi possível concluir
    tokens: list[Token]
    mensagem: str = ""
    linha: int | None = None
    coluna: int | None = None
    busca: Resultado | None = None   # None se o erro foi léxico


@lru_cache(maxsize=1)
def apnd_do_json() -> APND:
    return glc_para_apnd(ler_arquivo_gramatica(str(GRAMATICA_JSON)))


def validar_json(texto: str, estrategia: str = "largura",
                 guardar_explorados: bool = False) -> Relatorio:
    # Fase léxica.
    try:
        tokens, (linha_fim, coluna_fim) = tokenizar(texto)
    except ErroLexico as e:
        return Relatorio(False, [], f"erro léxico: {e.mensagem}", e.linha, e.coluna)

    # Fase sintática: o APND recebe só os tipos dos tokens.
    entrada = [t.tipo for t in tokens]
    busca = simular(apnd_do_json(), entrada, estrategia,
                    guardar_explorados=guardar_explorados)

    if busca.aceita:
        return Relatorio(True, tokens, busca=busca)
    if busca.aceita is None:
        return Relatorio(None, tokens, "limite de configurações atingido", busca=busca)

    # Rejeitado: monta a mensagem a partir do ponto mais distante.
    if busca.mais_longe < len(tokens):
        token = tokens[busca.mais_longe]
        encontrado, linha, coluna = _descrever(token), token.linha, token.coluna
    else:
        encontrado, linha, coluna = "fim do arquivo", linha_fim, coluna_fim

    mensagem = (f"erro sintático: encontrado {encontrado}; "
                f"esperado {_listar_esperados(busca.esperados)}")

    # Se o erro foi no fechamento (apareceu outro fechamento, ou o arquivo
    # acabou), aponta qual abertura ficou pendente.
    falhou_no_fechamento = (busca.mais_longe == len(tokens)
                            or tokens[busca.mais_longe].tipo in ("}", "]"))
    abertura = _abertura_pendente(tokens[:busca.mais_longe])
    if falhou_no_fechamento and abertura and PARES[abertura.tipo] in busca.esperados:
        mensagem += (f". O '{abertura.tipo}' aberto na linha {abertura.linha}, "
                     f"coluna {abertura.coluna}, não foi fechado")

    return Relatorio(False, tokens, mensagem, linha, coluna, busca)


def _abertura_pendente(tokens: list[Token]) -> Token | None:
    """Último '{' ou '[' ainda não fechado (usado só para a mensagem de erro)."""
    abertos: list[Token] = []
    for t in tokens:
        if t.tipo in PARES:
            abertos.append(t)
        elif t.tipo in ("}", "]") and abertos:
            abertos.pop()
    return abertos[-1] if abertos else None


def _descrever(t: Token) -> str:
    if t.tipo == "s":
        texto = t.texto if len(t.texto) <= 20 else t.texto[:17] + '..."'
        return f"a string {texto}"
    if t.tipo == "n":
        return f"o número {t.texto}"
    return f"'{t.texto}'"


def _listar_esperados(esperados: set[str]) -> str:
    nomes = []
    resto = set(esperados)
    if INICIOS_DE_VALOR <= resto:          # todos os inícios de valor: resume
        nomes.append("um valor")
        resto -= INICIOS_DE_VALOR
    ordem = ["s", "n", "t", "f", "u", "{", "[", ":", ",", "}", "]", FIM_DA_ENTRADA]
    for s in ordem:
        if s in resto:
            nomes.append(NOMES.get(s, f"'{s}'"))
    if len(nomes) <= 1:
        return "".join(nomes) or "nada"
    return ", ".join(nomes[:-1]) + " ou " + nomes[-1]
