"""
Testes automáticos.  Rodar na pasta do projeto com:

    python -m unittest discover testes -v
"""

import json
import random
import sys
import threading
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from lfa import painel                                # noqa: E402
from lfa.apnd import simular                          # noqa: E402
from lfa.conversao import glc_para_apnd               # noqa: E402
from lfa.glc import ler_arquivo_gramatica, ler_gramatica  # noqa: E402
from lfa.validador_json import validar_json           # noqa: E402

ESTRATEGIAS = ("largura", "profundidade")


def apnd_de(arquivo):
    return glc_para_apnd(ler_arquivo_gramatica(str(RAIZ / "gramaticas" / arquivo)))


class TestAtividade1Conversao(unittest.TestCase):
    def test_leitura_da_gramatica(self):
        g = ler_gramatica("S -> a S b | ε\n# comentário\nS -> &")   # ε e & continuam aceitos
        self.assertEqual(g.variaveis, ["S"])
        self.assertEqual(g.terminais, ["a", "b"])
        self.assertEqual(g.inicial, "S")
        self.assertEqual([p.direita for p in g.producoes], [("a", "S", "b"), (), ()])

    def test_transicoes_da_construcao(self):
        m = apnd_de("anbn.txt")
        # 1 inicial + 2 produções + 2 terminais + 1 final
        self.assertEqual(len(m.transicoes), 6)
        self.assertEqual(str(m.transicoes[0]), "δ(q0, λ, λ) → (q1, S $)")
        self.assertEqual(str(m.transicoes[1]), "δ(q1, λ, S) → (q1, a S b)")
        self.assertEqual(str(m.transicoes[-1]), "δ(q1, λ, $) → (q2, λ)")

    def test_gramatica_invalida(self):
        with self.assertRaises(ValueError):
            ler_gramatica("S a b")
        with self.assertRaises(ValueError):
            glc_para_apnd(ler_gramatica("S -> a $"))


class TestAtividade2Simulacao(unittest.TestCase):
    def verificar(self, arquivo, pertence):
        m = apnd_de(arquivo)
        for estrategia in ESTRATEGIAS:
            for palavra in ["", "a", "b", "ab", "ba", "aa", "aab", "abb", "aabb",
                            "abab", "aba", "abba", "aabbb", "aaabbb", "babab", "abaa"]:
                with self.subTest(estrategia=estrategia, palavra=palavra):
                    r = simular(m, list(palavra), estrategia)
                    self.assertEqual(r.aceita, pertence(palavra))

    def test_anbn(self):
        def pertence(w):
            n = len(w) // 2
            return w == "a" * n + "b" * n
        self.verificar("anbn.txt", pertence)

    def test_palindromos(self):
        self.verificar("palindromos.txt", lambda w: w == w[::-1])

    def test_caminho_de_aceitacao_e_valido(self):
        m = apnd_de("anbn.txt")
        r = simular(m, list("aabb"), "largura")
        self.assertEqual(r.caminho[0].config.estado, "q0")
        self.assertEqual(r.caminho[-1].config.estado, "q2")
        self.assertEqual(r.caminho[-1].config.posicao, 4)
        for anterior, atual in zip(r.caminho, r.caminho[1:]):
            self.assertIs(atual.pai, anterior)
            self.assertEqual(m.aplicar(anterior.config, atual.transicao), atual.config)

    def test_bfs_e_dfs_visitam_em_ordens_diferentes(self):
        m = apnd_de("palindromos.txt")
        bfs = simular(m, list("abba"), "largura", guardar_explorados=True)
        dfs = simular(m, list("abba"), "profundidade", guardar_explorados=True)
        self.assertNotEqual([n.config for n in bfs.explorados],
                            [n.config for n in dfs.explorados])

    def test_recursao_a_esquerda_para_no_limite(self):
        m = glc_para_apnd(ler_gramatica("E -> E + n | n"))
        self.assertTrue(simular(m, list("n+n"), "largura").aceita)
        r = simular(m, list("n+"), "profundidade", limite=2000)
        self.assertIsNone(r.aceita)


class TestAtividade3ValidadorJSON(unittest.TestCase):
    def erro(self, texto):
        rel = validar_json(texto)
        self.assertFalse(rel.valido, texto)
        return rel

    def test_exemplos_validos(self):
        for texto in ['{}', '[]', '0', '"x"', 'true', 'null', '-1.5e+10',
                      '{"a": [1, {"b": null}, []], "c": {"d": false}}',
                      '[[[[[[[[[[[[[[[[[[[[1]]]]]]]]]]]]]]]]]]]]',
                      '{"s": "aspas \\" barra \\\\ unicode \\u00e9"}']:
            for estrategia in ESTRATEGIAS:
                with self.subTest(texto=texto, estrategia=estrategia):
                    self.assertTrue(validar_json(texto, estrategia).valido)

    def test_fechamento_errado(self):
        rel = self.erro('{\n  "a": [1, 2}\n}')
        self.assertEqual((rel.linha, rel.coluna), (2, 13))
        self.assertIn("'['", rel.mensagem)          # aponta o [ que ficou aberto
        self.assertIn("linha 2, coluna 8", rel.mensagem)

    def test_nao_fechado(self):
        rel = self.erro('{"a": {"b": 1}')
        self.assertIn("fim do arquivo", rel.mensagem)
        self.assertEqual((rel.linha, rel.coluna), (1, 15))

    def test_virgula_faltando(self):
        rel = self.erro('{\n"a": 1\n"b": 2\n}')
        self.assertEqual((rel.linha, rel.coluna), (3, 1))
        self.assertIn("','", rel.mensagem)

    def test_virgula_sobrando(self):
        rel = self.erro('[1, 2,]')
        self.assertEqual((rel.linha, rel.coluna), (1, 7))
        self.assertIn("um valor", rel.mensagem)

    def test_erros_lexicos(self):
        casos = {"{'a': 1}": (1, 2), '{"a": tru}': (1, 7), '[01]': (1, 2),
                 '"abc': (1, 1), '["\\x"]': (1, 3), '[1.]': (1, 2)}
        for texto, posicao in casos.items():
            with self.subTest(texto=texto):
                rel = self.erro(texto)
                self.assertIn("léxico", rel.mensagem)
                self.assertEqual((rel.linha, rel.coluna), posicao)

    def test_arquivos_de_exemplo(self):
        pasta = RAIZ / "exemplos"
        for arquivo in sorted(pasta.glob("*.json")):
            with self.subTest(arquivo=arquivo.name):
                texto = arquivo.read_text(encoding="utf-8")
                self.assertEqual(validar_json(texto).valido, arquivo.name.startswith("valido"))

    def test_mesmo_veredito_que_json_loads(self):
        """Gera JSONs aleatórios (válidos e estragados) e compara com o Python."""
        sorteio = random.Random(2026)

        def valor(profundidade):
            tipo = sorteio.choice("ovsnb" if profundidade < 4 else "snb")
            if tipo == "o":
                pares = [f'"k{i}": {valor(profundidade + 1)}' for i in range(sorteio.randint(0, 3))]
                return "{" + ", ".join(pares) + "}"
            if tipo == "v":
                return "[" + ", ".join(valor(profundidade + 1) for _ in range(sorteio.randint(0, 3))) + "]"
            if tipo == "s":
                return '"texto"'
            if tipo == "n":
                return sorteio.choice(["0", "-12", "3.14", "1e5", "-0.5E-3"])
            return sorteio.choice(["true", "false", "null"])

        for _ in range(400):
            texto = valor(0)
            if sorteio.random() < 0.6:   # estraga o texto em 60% dos casos
                i = sorteio.randrange(len(texto) + 1)
                acao = sorteio.choice(["apaga", "insere"])
                if acao == "apaga" and texto:
                    texto = texto[:i] + texto[i + 1:]
                else:
                    texto = texto[:i] + sorteio.choice('{}[]:,"x1 ') + texto[i:]
            try:
                json.loads(texto)
                esperado = True
            except ValueError:
                esperado = False
            with self.subTest(texto=texto):
                self.assertEqual(validar_json(texto).valido, esperado)


class TestPainel(unittest.TestCase):
    """Sobe o servidor do painel numa porta livre e faz pedidos de verdade."""

    @classmethod
    def setUpClass(cls):
        cls.servidor = painel.criar_servidor(0)
        threading.Thread(target=cls.servidor.serve_forever, daemon=True).start()
        cls.url = f"http://127.0.0.1:{cls.servidor.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.servidor.shutdown()
        cls.servidor.server_close()

    def pedir(self, rota, corpo=None):
        dados = None if corpo is None else json.dumps(corpo).encode()
        try:
            with urlopen(Request(self.url + rota, dados)) as r:
                return r.status, json.loads(r.read())
        except HTTPError as e:
            return e.code, json.loads(e.read())

    def test_pagina_e_gramaticas(self):
        with urlopen(self.url + "/") as r:
            self.assertIn("Simulador de Autômato com Pilha".encode(), r.read())
        codigo, lista = self.pedir("/api/gramaticas")
        self.assertEqual(codigo, 200)
        self.assertIn("anbn.txt", [g["nome"] for g in lista])

    def test_simular_aceita_e_rejeita(self):
        anbn = "S -> a S b | λ"
        codigo, r = self.pedir("/api/simular", {"gramatica": anbn, "entrada": "aabb"})
        self.assertEqual(codigo, 200)
        self.assertTrue(r["aceita"])
        self.assertEqual(len(r["caminho"]), 10)
        # cada passo do caminho está nos explorados e aponta para o passo anterior
        nos = {n["id"]: n for n in r["explorados"]}
        for anterior, atual in zip(r["caminho"], r["caminho"][1:]):
            self.assertEqual(nos[atual]["pai"], anterior)
        self.assertEqual(nos[r["caminho"][-1]]["pilha"], [])

        codigo, r = self.pedir("/api/simular", {"gramatica": anbn, "entrada": "aab",
                                                "busca": "profundidade"})
        self.assertEqual(codigo, 200)
        self.assertFalse(r["aceita"])
        self.assertEqual(r["caminho"], [])
        self.assertEqual(r["esperados"], ["b"])

    def test_pedidos_invalidos(self):
        for corpo in ({"gramatica": "S -> a", "entrada": "x"},        # símbolo desconhecido
                      {"gramatica": "sem seta", "entrada": ""},       # gramática inválida
                      {"gramatica": "S -> a", "busca": "outra"},      # estratégia inválida
                      {"entrada": "a"},                               # falta a gramática
                      ["não é um objeto"]):
            with self.subTest(corpo=corpo):
                codigo, r = self.pedir("/api/simular", corpo)
                self.assertEqual(codigo, 400)
                self.assertIn("erro", r)


if __name__ == "__main__":
    unittest.main()
