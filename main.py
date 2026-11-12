"""
Ponto de entrada do programa (linha de comando).

    python main.py                      (sem nada: abre um menu interativo)
    python main.py converter  gramaticas/anbn.txt
    python main.py simular    gramaticas/anbn.txt "aabb" --busca profundidade
    python main.py validar    exemplos/valido.json
    python main.py painel                (painel passo a passo no navegador)

Use  python main.py <comando> -h  para ver as opções de cada comando.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

from lfa import painel
from lfa.apnd import FIM_DA_ENTRADA, APND, No, Resultado, separar_entrada, simular
from lfa.conversao import glc_para_apnd
from lfa.glc import GLC, ler_arquivo_gramatica
from lfa.validador_json import validar_json


# ---------------------------------------------------------------- impressão

def tabela(cabecalho: list[str], linhas: list[list[str]], largura_max: int = 45) -> None:
    def cortar(s: str) -> str:
        return s if len(s) <= largura_max else s[:largura_max - 1] + "…"
    linhas = [[cortar(c) for c in linha] for linha in linhas]
    larguras = [max(len(str(x)) for x in coluna) for coluna in zip(cabecalho, *linhas)]
    for linha in [cabecalho] + linhas:
        print("  " + "  ".join(c.ljust(w) for c, w in zip(linha, larguras)).rstrip())


def mostrar_glc(g: GLC) -> None:
    print("Gramática G = (V, Σ, P, S)")
    print(f"  V (variáveis): {', '.join(g.variaveis)}")
    print(f"  Σ (terminais): {', '.join(g.terminais)}")
    print(f"  S (inicial):   {g.inicial}")
    print("  P (produções):")
    for p in g.producoes:
        print(f"    {p}")
    for v in g.recursoes_a_esquerda():
        print(f"  Aviso: {v} tem recursão à esquerda; a busca em profundidade pode "
              f"não terminar (o limite de configurações interrompe a busca).")


def mostrar_apnd(m: APND) -> None:
    print("APND M = (Q, Σ, Γ, δ, q0, F)")
    print(f"  Q (estados):         {', '.join(m.estados)}")
    print(f"  Σ (entrada):         {', '.join(m.alfabeto_entrada)}")
    print(f"  Γ (pilha):           {', '.join(m.alfabeto_pilha)}")
    print(f"  q0 (inicial):        {m.inicial}")
    print(f"  F (aceitação):       {', '.join(sorted(m.aceitacao))}")
    print("  δ (transições):")
    tabela(["nº", "de", "para", "transição", "significado"],
           [[f"{t.numero}.", t.origem, t.destino, str(t), t.descricao] for t in m.transicoes],
           largura_max=60)


def texto_pilha(pilha: tuple[str, ...]) -> str:
    return " ".join(pilha) or "λ"


def mostrar_caminho(caminho: list[No], entrada: list[str]) -> None:
    print("Caminho de aceitação (o topo da pilha fica à esquerda):")
    linhas = []
    for passo, no in enumerate(caminho):
        c = no.config
        linhas.append([str(passo), c.estado, " ".join(entrada[c.posicao:]) or "λ",
                       texto_pilha(c.pilha),
                       f"{no.transicao.numero}. {no.transicao}" if no.transicao else "início"])
    tabela(["passo", "estado", "falta ler", "pilha", "transição usada"], linhas)


def mostrar_explorados(r: Resultado, entrada: list[str]) -> None:
    print("Configurações na ordem em que foram visitadas:")
    linhas = []
    for no in r.explorados:
        c = no.config
        linhas.append([f"#{no.id}", f"#{no.pai.id}" if no.pai else "-", c.estado,
                       " ".join(entrada[c.posicao:]) or "λ", texto_pilha(c.pilha)])
    tabela(["nó", "pai", "estado", "falta ler", "pilha"], linhas)


def mostrar_estatisticas(r: Resultado, estrategia: str) -> None:
    nome = "largura (BFS)" if estrategia == "largura" else "profundidade (DFS)"
    print(f"Busca em {nome}: {r.total_explorados} configurações visitadas, "
          f"fronteira máxima de {r.maior_fronteira}.")


# ---------------------------------------------------------------- comandos

def cmd_converter(args) -> int:
    g = ler_arquivo_gramatica(args.gramatica)
    mostrar_glc(g)
    print()
    mostrar_apnd(glc_para_apnd(g))
    return 0


def cmd_simular(args) -> int:
    g = ler_arquivo_gramatica(args.gramatica)
    m = glc_para_apnd(g)
    entrada = separar_entrada(args.entrada)

    desconhecidos = sorted(set(entrada) - set(g.terminais))
    if desconhecidos:
        print(f"Símbolos que não são terminais da gramática: {', '.join(desconhecidos)}")
        print(f"Terminais da gramática: {', '.join(g.terminais)}")
        if any(len(t) > 1 for t in g.terminais):
            print("Separe os símbolos com espaço, ex.: { s : n }")
        return 2

    r = simular(m, entrada, args.busca, guardar_explorados=args.explorados)
    print(f"Entrada: {' '.join(entrada) or 'λ'}")
    mostrar_estatisticas(r, args.busca)
    if args.explorados:
        print()
        mostrar_explorados(r, entrada)
    print()
    if r.aceita:
        print("Resultado: ACEITA")
        print()
        mostrar_caminho(r.caminho, entrada)
        return 0
    if r.aceita is None:
        print("Resultado: INCONCLUSIVO (limite de configurações atingido)")
        return 3
    print("Resultado: REJEITADA (nenhum caminho leva à aceitação)")
    # aspas nos símbolos: com o JSON um dos terminais é a própria vírgula
    esperados = ", ".join(s if s == FIM_DA_ENTRADA else f"'{s}'" for s in sorted(r.esperados)) or "nada"
    if r.mais_longe < len(entrada):
        print(f"Nenhum caminho conseguiu ler o símbolo {r.mais_longe + 1} "
              f"('{entrada[r.mais_longe]}'); esperava-se: {esperados}.")
    else:
        print(f"A entrada acabou antes do esperado; esperava-se: {esperados}.")
    return 1


def cmd_validar(args) -> int:
    # "utf-8-sig" ignora o BOM que o Bloco de Notas pode gravar no início do arquivo.
    with open(args.arquivo, encoding="utf-8-sig") as f:
        texto = f.read()
    rel = validar_json(texto, args.busca, guardar_explorados=args.explorados)
    entrada = [t.tipo for t in rel.tokens]

    print(f"Arquivo: {args.arquivo}")
    if rel.busca:
        print(f"Tokens: {len(rel.tokens)}")
        mostrar_estatisticas(rel.busca, args.busca)
    if args.explorados and rel.busca:
        print()
        mostrar_explorados(rel.busca, entrada)
    print()
    if rel.valido:
        print("JSON VÁLIDO")
        if args.rastro:
            print()
            mostrar_caminho(rel.busca.caminho, entrada)
        return 0
    if rel.valido is None:
        print(f"NÃO FOI POSSÍVEL CONCLUIR: {rel.mensagem}")
        return 3
    print("JSON INVÁLIDO")
    print(f"  Linha {rel.linha}, coluna {rel.coluna}: {rel.mensagem}")
    linhas = texto.replace("\r", "").split("\n")
    if rel.linha is not None and rel.linha <= len(linhas):
        print()
        # Tabs viram um espaço para o ^ ficar alinhado (a coluna conta tab como 1).
        print(f"  {rel.linha:>4} | {linhas[rel.linha - 1].replace(chr(9), ' ')}")
        print(f"       | {' ' * (rel.coluna - 1)}^")
    return 1


# ---------------------------------------------------------------- menu

def escolher(titulo: str, opcoes: list[str]) -> int:
    """Mostra opções numeradas e devolve o índice escolhido (0 = primeira)."""
    print(titulo)
    for i, opcao in enumerate(opcoes, start=1):
        print(f"  {i}. {opcao}")
    while True:
        resposta = input("> ").strip()
        if resposta.isdigit() and 1 <= int(resposta) <= len(opcoes):
            return int(resposta) - 1
        print(f"Digite um número de 1 a {len(opcoes)}.")


def escolher_arquivo(titulo: str, pasta: str, padrao: str) -> str:
    arquivos = sorted(str(p) for p in Path(pasta).glob(padrao))
    i = escolher(titulo, arquivos + ["Outro arquivo (digitar o caminho)"])
    if i < len(arquivos):
        return arquivos[i]
    # Arrastar um arquivo para o terminal cola o caminho entre aspas.
    return input("Caminho do arquivo (pode arrastar o arquivo para cá): ").strip().strip('"')


def perguntar_busca(args: argparse.Namespace) -> None:
    args.busca = ["largura", "profundidade"][
        escolher("Estratégia de busca:", ["Largura (BFS)", "Profundidade (DFS)"])]
    args.explorados = input("Listar todas as configurações visitadas? (s/N) ").strip().lower() == "s"


def menu() -> int:
    acoes = ["Converter uma gramática em APND      (atividade 1)",
             "Simular o APND em uma palavra        (atividade 2)",
             "Validar um arquivo JSON              (atividade 3)",
             "Abrir o painel no navegador          (atividade 2)",
             "Rodar os testes automáticos",
             "Sair"]
    while True:
        print()
        print("Trabalho de LFA, Tema 4: APND e GLC")
        acao = escolher("O que você quer fazer?", acoes)
        print()
        args = argparse.Namespace()
        try:
            if acao == 0:
                args.gramatica = escolher_arquivo("Qual gramática?", "gramaticas", "*.txt")
                print()
                cmd_converter(args)
            elif acao == 1:
                args.gramatica = escolher_arquivo("Qual gramática?", "gramaticas", "*.txt")
                args.entrada = input('Palavra de entrada (ex.: aabb; vazia = λ): ')
                perguntar_busca(args)
                print()
                cmd_simular(args)
            elif acao == 2:
                args.arquivo = escolher_arquivo("Qual arquivo JSON?", "exemplos", "*.json")
                perguntar_busca(args)
                args.rastro = input("Mostrar o caminho da pilha se for válido? (s/N) ").strip().lower() == "s"
                print()
                cmd_validar(args)
            elif acao == 3:
                painel.iniciar()
            elif acao == 4:
                subprocess.run([sys.executable, "-B", "-m", "unittest", "discover", "testes", "-v"])
            else:
                return 0
        except (OSError, ValueError) as e:
            print(f"Erro: {e}")
        print()
        input("Pressione Enter para voltar ao menu...")


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) == 1:      # sem argumentos: abre o menu
        os.chdir(Path(__file__).resolve().parent)   # para achar gramaticas/ e exemplos/
        try:
            return menu()
        except (KeyboardInterrupt, EOFError):
            return 0

    p = argparse.ArgumentParser(description="GLC → APND, simulação com BFS/DFS e validador de JSON.")
    sub = p.add_subparsers(dest="comando", required=True)

    busca = argparse.ArgumentParser(add_help=False)
    busca.add_argument("--busca", choices=["largura", "profundidade"], default="largura",
                       help="estratégia de busca (padrão: largura)")
    busca.add_argument("--explorados", action="store_true",
                       help="lista todas as configurações visitadas pela busca")

    c = sub.add_parser("converter", help="atividade 1: mostra a GLC e o APND equivalente")
    c.add_argument("gramatica", help="arquivo .txt com a gramática")
    c.set_defaults(funcao=cmd_converter)

    s = sub.add_parser("simular", parents=[busca], help="atividade 2: roda o APND sobre uma entrada")
    s.add_argument("gramatica", help="arquivo .txt com a gramática")
    s.add_argument("entrada", help='palavra de entrada, ex.: "aabb" ou "{s:n}"')
    s.set_defaults(funcao=cmd_simular)

    v = sub.add_parser("validar", parents=[busca], help="atividade 3: valida um arquivo JSON")
    v.add_argument("arquivo", help="arquivo .json")
    v.add_argument("--rastro", action="store_true",
                   help="mostra o caminho do APND quando o JSON é válido")
    v.set_defaults(funcao=cmd_validar)

    pn = sub.add_parser("painel", help="atividade 2: abre o painel passo a passo no navegador")
    pn.add_argument("--porta", type=int, default=8765, help="porta local (padrão: 8765)")
    pn.set_defaults(funcao=lambda a: painel.iniciar(a.porta) or 0)

    args = p.parse_args()
    try:
        return args.funcao(args)
    except (OSError, ValueError) as e:
        print(f"Erro: {e}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
