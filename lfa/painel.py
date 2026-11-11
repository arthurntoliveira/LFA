"""
Painel de controle no navegador para a atividade 2.

Um servidor HTTP local, só com a biblioteca padrão. A página (painel/index.html)
pede ao Python a conversão e a simulação; nenhuma lógica é refeita em JavaScript,
então o painel mostra exatamente o que os testes validam.

    GET  /                 a página
    GET  /api/gramaticas   os arquivos de gramaticas/ com o texto de cada um
    POST /api/simular      {"gramatica": texto, "entrada": "aabb", "busca": "largura"}
"""

from __future__ import annotations

import json
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from .apnd import separar_entrada, simular
from .conversao import glc_para_apnd
from .glc import ler_gramatica

RAIZ = Path(__file__).resolve().parent.parent
PAGINA = RAIZ / "painel" / "index.html"
PASTA_GRAMATICAS = RAIZ / "gramaticas"

# shortcut: limite baixo para o navegador aguentar a lista de passos; aumentar
# se uma entrada legítima der inconclusivo no painel.
LIMITE = 5000
CORPO_MAX = 100_000   # bytes aceitos no POST


def listar_gramaticas() -> list[dict]:
    return [{"nome": p.name, "texto": p.read_text(encoding="utf-8-sig")}
            for p in sorted(PASTA_GRAMATICAS.glob("*.txt"))]


def simular_para_painel(texto_gramatica: str, texto_entrada: str,
                        busca: str = "largura") -> dict:
    """Converte, simula e devolve tudo o que a página precisa, em JSON."""
    g = ler_gramatica(texto_gramatica)
    m = glc_para_apnd(g)
    entrada = separar_entrada(texto_entrada)
    desconhecidos = sorted(set(entrada) - set(g.terminais))
    if desconhecidos:
        raise ValueError(f"símbolos que não são terminais da gramática: "
                         f"{', '.join(desconhecidos)} (terminais: {', '.join(g.terminais)})")

    r = simular(m, entrada, busca, limite=LIMITE, guardar_explorados=True)
    return {
        "glc": {"variaveis": g.variaveis, "terminais": g.terminais, "inicial": g.inicial,
                "producoes": [str(p) for p in g.producoes],
                "recursoes_a_esquerda": g.recursoes_a_esquerda()},
        "apnd": {"estados": m.estados, "inicial": m.inicial,
                 "aceitacao": sorted(m.aceitacao), "alfabeto_pilha": m.alfabeto_pilha,
                 "transicoes": [{"numero": t.numero, "origem": t.origem, "le": t.le,
                                 "desempilha": t.desempilha, "destino": t.destino,
                                 "empilha": list(t.empilha), "texto": str(t),
                                 "descricao": t.descricao} for t in m.transicoes]},
        "entrada": entrada,
        "busca": busca,
        "limite": LIMITE,
        "aceita": r.aceita,
        "total_explorados": r.total_explorados,
        "maior_fronteira": r.maior_fronteira,
        "mais_longe": r.mais_longe,
        "esperados": sorted(r.esperados),
        "caminho": [no.id for no in r.caminho],
        "explorados": [{"id": no.id, "pai": no.pai.id if no.pai else None,
                        "estado": no.config.estado, "posicao": no.config.posicao,
                        "pilha": list(no.config.pilha),
                        "transicao": no.transicao.numero if no.transicao else None}
                       for no in r.explorados],
    }


class _Pedido(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self._enviar(200, PAGINA.read_bytes(), "text/html; charset=utf-8")
        elif self.path == "/api/gramaticas":
            self._json(200, listar_gramaticas())
        else:
            self._json(404, {"erro": "não encontrado"})

    def do_POST(self):
        if self.path != "/api/simular":
            return self._json(404, {"erro": "não encontrado"})
        try:
            tamanho = int(self.headers.get("Content-Length", 0))
            if tamanho > CORPO_MAX:
                raise ValueError("requisição grande demais")
            dados = json.loads(self.rfile.read(tamanho))
            resposta = simular_para_painel(str(dados["gramatica"]),
                                           str(dados.get("entrada", "")),
                                           str(dados.get("busca", "largura")))
        except KeyError as e:
            return self._json(400, {"erro": f"campo obrigatório ausente: {e}"})
        except (ValueError, TypeError, AttributeError) as e:
            return self._json(400, {"erro": str(e)})
        self._json(200, resposta)

    def _json(self, codigo: int, dados) -> None:
        self._enviar(codigo, json.dumps(dados, ensure_ascii=False).encode("utf-8"),
                     "application/json; charset=utf-8")

    def _enviar(self, codigo: int, corpo: bytes, tipo: str) -> None:
        self.send_response(codigo)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)

    def log_message(self, *args):   # não polui o terminal a cada pedido
        pass


def criar_servidor(porta: int = 8765) -> ThreadingHTTPServer:
    """Só escuta em 127.0.0.1 (o painel não fica visível na rede)."""
    try:
        return ThreadingHTTPServer(("127.0.0.1", porta), _Pedido)
    except OSError:     # porta ocupada: usa qualquer uma livre
        return ThreadingHTTPServer(("127.0.0.1", 0), _Pedido)


def iniciar(porta: int = 8765, abrir_navegador: bool = True) -> None:
    servidor = criar_servidor(porta)
    url = f"http://127.0.0.1:{servidor.server_port}/"
    print(f"Painel aberto em {url}  (Ctrl+C para encerrar)")
    if abrir_navegador:
        webbrowser.open(url)
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        servidor.server_close()
        print("Painel encerrado.")
