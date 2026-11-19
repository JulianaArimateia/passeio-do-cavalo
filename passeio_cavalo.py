#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Trabalho T3 - Complexidade de Algoritmos (NCC0234) - UERN
Estratégias computacionais para o Problema do Passeio do Cavalo.

Estratégias implementadas (todas partem da posição inicial informada):
  1. 'forca'      : backtracking com ordem fixa de movimentos (linha de base).
  2. 'warnsdorff' : guloso com a regra de Warnsdorff (menor grau), sem retrocesso.
  2b.'guloso'     : guloso simples (primeiro vizinho livre), sem retrocesso (comparação).
  3. 'hibrida'    : Warnsdorff como ordenação + backtracking com limite
                    de nós (estratégia principal do trabalho).

Métrica de esforço: número de "nós visitados" = número de vezes em que o
cavalo é colocado em uma casa (inclui a casa inicial e as recolocações após
retrocesso). Também são contados os retrocessos (backtracks).

Uso (linha de comando):
    python passeio_cavalo.py --linhas 8 --colunas 8 --inicio 0 0
    python passeio_cavalo.py -m 5 -n 5 -i 2 2 --estrategia forca
    python passeio_cavalo.py --web     # interface no navegador (recomendada)
    python passeio_cavalo.py --gui     # interface simples em tkinter
"""
import argparse
import sys
import time
from dataclasses import dataclass, field

# Os 8 movimentos em "L" do cavalo: (delta_linha, delta_coluna).
MOVIMENTOS = ((2, 1), (1, 2), (-1, 2), (-2, 1),
              (-2, -1), (-1, -2), (1, -2), (2, -1))

LIMITE_PADRAO = 5_000_000  # limite de nós visitados (condição de parada)


@dataclass
class Resultado:
    linhas: int
    colunas: int
    inicio: tuple
    estrategia: str
    caminho: list = field(default_factory=list)   # lista de (linha, coluna)
    nos: int = 0                                  # métrica de esforço
    retrocessos: int = 0
    tempo: float = 0.0                            # segundos
    completo: bool = False
    motivo_parada: str = ""                       # "completo", "limite", "esgotado", "beco"

    @property
    def visitadas(self):
        return len(self.caminho)

    @property
    def total_casas(self):
        return self.linhas * self.colunas


class _LimiteAtingido(Exception):
    pass


class _OtimoAtingido(Exception):
    pass


def limite_superior(linhas, colunas, inicio):
    """Maior percurso possível, por paridade de cores: o cavalo alterna de cor
    a cada movimento. Se a cor inicial tem a e a outra tem b casas, o caminho
    tem no máximo 2b+1 casas (a > b) ou 2a casas (a <= b), sempre limitado a m*n."""
    total = linhas * colunas
    a = sum(1 for r in range(linhas) for c in range(colunas)
            if (r + c) % 2 == (inicio[0] + inicio[1]) % 2)
    b = total - a
    return min(total, 2 * b + 1) if a > b else min(total, 2 * a)


class Tabuleiro:
    """Tabuleiro m x n com tabela de vizinhos pré-computada (grafo do cavalo)."""

    def __init__(self, linhas, colunas):
        self.m, self.n = linhas, colunas
        self.viz = [[self._vizinhos(r, c) for c in range(colunas)]
                    for r in range(linhas)]

    def _vizinhos(self, r, c):
        return [(r + dr, c + dc) for dr, dc in MOVIMENTOS
                if 0 <= r + dr < self.m and 0 <= c + dc < self.n]


# ----------------------------------------------------------------------------
# Estratégias
# ----------------------------------------------------------------------------
def resolver(linhas, colunas, inicio, estrategia="hibrida", limite=LIMITE_PADRAO):
    """Executa a estratégia escolhida e devolve um Resultado."""
    if not (0 <= inicio[0] < linhas and 0 <= inicio[1] < colunas):
        raise ValueError("Posição inicial fora do tabuleiro.")
    tab = Tabuleiro(linhas, colunas)
    res = Resultado(linhas, colunas, tuple(inicio), estrategia)
    t0 = time.perf_counter()
    if estrategia in ("warnsdorff", "guloso"):
        _guloso(tab, res, estrategia == "warnsdorff")
    elif estrategia in ("forca", "hibrida"):
        _backtracking(tab, res, estrategia == "hibrida", limite)
    else:
        raise ValueError("Estratégia desconhecida: " + estrategia)
    res.tempo = time.perf_counter() - t0
    res.completo = res.visitadas == res.total_casas
    if res.completo:
        res.motivo_parada = "completo"
    return res


def _grau(tab, visitado, casa):
    """Número de casas ainda livres alcançáveis a partir de 'casa' (grau)."""
    return sum(1 for (r, c) in tab.viz[casa[0]][casa[1]] if not visitado[r][c])


def _dist_centro(tab, casa):
    """Distância ao quadrado até o centro (critério de desempate)."""
    cr, cc = (tab.m - 1) / 2, (tab.n - 1) / 2
    return (casa[0] - cr) ** 2 + (casa[1] - cc) ** 2


def _candidatos_ordenados(tab, visitado, atual):
    """Candidatos livres ordenados por Warnsdorff: menor grau primeiro;
    empate resolvido pela maior distância ao centro (casas periféricas antes)."""
    cand = [v for v in tab.viz[atual[0]][atual[1]] if not visitado[v[0]][v[1]]]
    cand.sort(key=lambda v: (_grau(tab, visitado, v), -_dist_centro(tab, v)))
    return cand


def _guloso(tab, res, usar_warnsdorff=True):
    """Guloso sem retrocesso. Com usar_warnsdorff=True escolhe o vizinho de menor
    grau (regra de Warnsdorff); caso contrário, o primeiro vizinho livre na
    ordem fixa de MOVIMENTOS (guloso simples, sem critério de escolha)."""
    visitado = [[False] * tab.n for _ in range(tab.m)]
    atual = res.inicio
    visitado[atual[0]][atual[1]] = True
    res.caminho.append(atual)
    res.nos = 1
    while True:
        if usar_warnsdorff:
            cand = _candidatos_ordenados(tab, visitado, atual)
        else:
            cand = [v for v in tab.viz[atual[0]][atual[1]] if not visitado[v[0]][v[1]]]
        if not cand:
            break
        atual = cand[0]
        visitado[atual[0]][atual[1]] = True
        res.caminho.append(atual)
        res.nos += 1
    res.motivo_parada = "beco" if len(res.caminho) < tab.m * tab.n else "completo"


def _backtracking(tab, res, usar_warnsdorff, limite):
    """Backtracking recursivo. Guarda o melhor caminho encontrado (o mais longo).
    Se usar_warnsdorff=True, os candidatos são ordenados pela heurística;
    caso contrário usa-se a ordem fixa de MOVIMENTOS (força bruta)."""
    total = tab.m * tab.n
    sys.setrecursionlimit(max(sys.getrecursionlimit(), total + 200))  # profundidade <= m*n
    visitado = [[False] * tab.n for _ in range(tab.m)]
    caminho = []
    melhor = []
    maior = 0
    teto = limite_superior(tab.m, tab.n, res.inicio)

    def visitar(casa):
        nonlocal melhor, maior
        res.nos += 1
        if res.nos > limite:
            raise _LimiteAtingido
        visitado[casa[0]][casa[1]] = True
        caminho.append(casa)
        if len(caminho) > maior:
            maior = len(caminho)
            if maior == teto:          # atingiu o máximo possível: encerra
                melhor = caminho.copy()
                raise _OtimoAtingido
        if len(caminho) == total:
            return True
        if usar_warnsdorff:
            cand = _candidatos_ordenados(tab, visitado, casa)
        else:
            cand = [v for v in tab.viz[casa[0]][casa[1]] if not visitado[v[0]][v[1]]]
        for v in cand:
            if visitar(v):
                return True
        # retrocesso (copia o caminho só ao recuar de um novo recorde: evita O(L) por passo)
        if len(caminho) > len(melhor):
            melhor = caminho.copy()
        visitado[casa[0]][casa[1]] = False
        caminho.pop()
        res.retrocessos += 1
        return False

    try:
        achou = visitar(res.inicio)
        res.motivo_parada = "completo" if achou else "esgotado"
    except _LimiteAtingido:
        res.motivo_parada = "limite"
        if len(caminho) > len(melhor):
            melhor = caminho.copy()
    except _OtimoAtingido:
        res.motivo_parada = "completo" if len(melhor) == total else "otimo"
    res.caminho = melhor


# ----------------------------------------------------------------------------
# Saída
# ----------------------------------------------------------------------------
def tabuleiro_texto(res):
    """Tabuleiro numerado pela ordem dos movimentos (casa inicial = 1)."""
    grade = [[0] * res.colunas for _ in range(res.linhas)]
    for k, (r, c) in enumerate(res.caminho, start=1):
        grade[r][c] = k
    larg = len(str(res.total_casas))
    linhas = []
    for r in range(res.linhas):
        linhas.append(" ".join(("%*d" % (larg, x)) if x else "." * larg
                               for x in grade[r]))
    return "\n".join(linhas)


def relatorio_texto(res):
    mot = {"completo": "passeio completo encontrado",
           "limite": "encerrado pelo limite de execução (nós visitados)",
           "otimo": "maior percurso possível atingido (limite de paridade); passeio completo impossível",
           "esgotado": "espaço de busca esgotado (nenhum passeio completo existe)",
           "beco": "limitação da estratégia (sem retrocesso, ficou sem saída)"}
    return (f"Estratégia ........ {res.estrategia}\n"
            f"Tabuleiro ......... {res.linhas}x{res.colunas}\n"
            f"Posição inicial ... {res.inicio}\n"
            f"Casas visitadas ... {res.visitadas} de {res.total_casas}\n"
            f"Passeio completo .. {'SIM' if res.completo else 'NÃO'}\n"
            f"Nós visitados ..... {res.nos}\n"
            f"Retrocessos ....... {res.retrocessos}\n"
            f"Tempo ............. {res.tempo * 1000:.3f} ms\n"
            f"Parada ............ {mot.get(res.motivo_parada, res.motivo_parada)}")


# ----------------------------------------------------------------------------
# Interface gráfica (tkinter)
# ----------------------------------------------------------------------------
def abrir_gui():
    import tkinter as tk
    from tkinter import ttk, messagebox

    janela = tk.Tk()
    janela.title("Passeio do Cavalo - Complexidade de Algoritmos")
    janela.resizable(False, False)

    TAM = 64  # tamanho de cada casa em pixels
    estado = {"res": None, "passo": 0, "job": None}

    painel = ttk.Frame(janela, padding=8)
    painel.grid(row=0, column=0, sticky="n")

    ttk.Label(painel, text="Tabuleiro").grid(row=0, column=0, sticky="w")
    var_dim = tk.StringVar(value="8x8")
    ttk.Combobox(painel, textvariable=var_dim, values=["5x5", "8x8"],
                 state="readonly", width=8).grid(row=0, column=1, pady=2)

    ttk.Label(painel, text="Linha inicial").grid(row=1, column=0, sticky="w")
    var_l = tk.IntVar(value=0)
    ttk.Spinbox(painel, from_=0, to=7, textvariable=var_l, width=6).grid(row=1, column=1, pady=2)

    ttk.Label(painel, text="Coluna inicial").grid(row=2, column=0, sticky="w")
    var_c = tk.IntVar(value=0)
    ttk.Spinbox(painel, from_=0, to=7, textvariable=var_c, width=6).grid(row=2, column=1, pady=2)

    ttk.Label(painel, text="Estratégia").grid(row=3, column=0, sticky="w")
    var_est = tk.StringVar(value="hibrida")
    ttk.Combobox(painel, textvariable=var_est, values=["hibrida", "warnsdorff", "guloso", "forca"],
                 state="readonly", width=10).grid(row=3, column=1, pady=2)

    ttk.Label(painel, text="Limite de nós").grid(row=4, column=0, sticky="w")
    var_lim = tk.IntVar(value=LIMITE_PADRAO)
    ttk.Entry(painel, textvariable=var_lim, width=10).grid(row=4, column=1, pady=2)

    canvas = tk.Canvas(janela, width=8 * TAM, height=8 * TAM, highlightthickness=0)
    canvas.grid(row=0, column=1, padx=8, pady=8)
    saida = tk.Text(painel, width=40, height=11, state="disabled", font=("Courier", 9))
    saida.grid(row=7, column=0, columnspan=2, pady=6)

    def dims():
        return (5, 5) if var_dim.get() == "5x5" else (8, 8)

    def desenhar(res, ate):
        canvas.delete("all")
        m, n = dims()
        for r in range(m):
            for c in range(n):
                cor = "#f0d9b5" if (r + c) % 2 == 0 else "#b58863"
                canvas.create_rectangle(c * TAM, r * TAM, (c + 1) * TAM, (r + 1) * TAM,
                                        fill=cor, outline=cor)
        if res is None:
            return
        pts = res.caminho[:ate]
        for a, b in zip(pts, pts[1:]):
            canvas.create_line(a[1] * TAM + TAM // 2, a[0] * TAM + TAM // 2,
                               b[1] * TAM + TAM // 2, b[0] * TAM + TAM // 2,
                               fill="#2a6f97", width=2)
        for k, (r, c) in enumerate(pts, start=1):
            canvas.create_text(c * TAM + TAM // 2, r * TAM + TAM // 2, text=str(k),
                               font=("Helvetica", 14, "bold"),
                               fill="#c1121f" if k == 1 else "#1b1b1b")

    def mostrar(texto):
        saida.config(state="normal")
        saida.delete("1.0", "end")
        saida.insert("end", texto)
        saida.config(state="disabled")

    def animar():
        res = estado["res"]
        if res is None:
            return
        estado["passo"] += 1
        desenhar(res, estado["passo"])
        if estado["passo"] < res.visitadas:
            estado["job"] = janela.after(120, animar)

    def executar(animado):
        if estado["job"]:
            janela.after_cancel(estado["job"])
            estado["job"] = None
        m, n = dims()
        try:
            res = resolver(m, n, (var_l.get(), var_c.get()), var_est.get(), var_lim.get())
        except (ValueError, tk.TclError) as e:
            messagebox.showerror("Entrada inválida", str(e))
            return
        estado["res"], estado["passo"] = res, 0
        mostrar(relatorio_texto(res))
        if animado:
            animar()
        else:
            desenhar(res, res.visitadas)

    ttk.Button(painel, text="Executar", command=lambda: executar(False)).grid(row=5, column=0, pady=4)
    ttk.Button(painel, text="Animar", command=lambda: executar(True)).grid(row=5, column=1, pady=4)
    desenhar(None, 0)
    janela.mainloop()


# ----------------------------------------------------------------------------
# Interface web local (abre no navegador; usa apenas a biblioteca padrão)
# ----------------------------------------------------------------------------
def _res_json(res):
    return {"linhas": res.linhas, "colunas": res.colunas, "inicio": list(res.inicio),
            "estrategia": res.estrategia, "caminho": [list(p) for p in res.caminho],
            "visitadas": res.visitadas, "total": res.total_casas, "completo": res.completo,
            "nos": res.nos, "retrocessos": res.retrocessos,
            "tempo_ms": res.tempo * 1000, "parada": res.motivo_parada}


def servir(porta=8765, abrir=True):
    import json
    import os
    import threading
    import webbrowser
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    from urllib.parse import urlparse, parse_qs

    pasta = os.path.dirname(os.path.abspath(__file__))

    class Handler(BaseHTTPRequestHandler):
        def _enviar(self, codigo, tipo, corpo):
            self.send_response(codigo)
            self.send_header("Content-Type", tipo)
            self.send_header("Content-Length", str(len(corpo)))
            self.end_headers()
            self.wfile.write(corpo)

        def do_GET(self):
            url = urlparse(self.path)
            q = {k: v[0] for k, v in parse_qs(url.query).items()}
            if url.path in ("/", "/index.html"):
                with open(os.path.join(pasta, "interface.html"), "rb") as f:
                    return self._enviar(200, "text/html; charset=utf-8", f.read())
            if url.path in ("/api/resolver", "/api/comparar"):
                try:
                    m, n = int(q.get("m", 8)), int(q.get("n", 8))
                    ini = (int(q.get("r", 0)), int(q.get("c", 0)))
                    lim = min(int(q.get("lim", LIMITE_PADRAO)), 20_000_000)
                    if not (3 <= m <= 20 and 3 <= n <= 20):
                        raise ValueError("Dimensões permitidas: de 3 a 20.")
                    if url.path == "/api/resolver":
                        dados = _res_json(resolver(m, n, ini, q.get("est", "hibrida"), lim))
                    else:
                        lim_f = min(lim, 2_000_000)
                        dados = [_res_json(resolver(m, n, ini, e, lim_f))
                                 for e in ("hibrida", "warnsdorff", "forca")]
                    return self._enviar(200, "application/json", json.dumps(dados).encode())
                except (ValueError, KeyError) as e:
                    return self._enviar(400, "application/json",
                                        json.dumps({"erro": str(e)}).encode())
            if url.path == "/favicon.ico":
                return self._enviar(204, "image/x-icon", b"")
            self._enviar(404, "text/plain", b"nao encontrado")

        def log_message(self, *a):
            pass

    servidor = ThreadingHTTPServer(("127.0.0.1", porta), Handler)
    url = f"http://127.0.0.1:{porta}/"
    print(f"Interface disponível em {url}  (Ctrl+C para encerrar)")
    if abrir:
        threading.Timer(0.5, lambda: webbrowser.open(url)).start()
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nEncerrado.")
        servidor.server_close()


# ----------------------------------------------------------------------------
# Linha de comando
# ----------------------------------------------------------------------------
def main(argv=None):
    p = argparse.ArgumentParser(description="Passeio do Cavalo (T3 - Complexidade de Algoritmos)")
    p.add_argument("-m", "--linhas", type=int, default=8)
    p.add_argument("-n", "--colunas", type=int, default=8)
    p.add_argument("-i", "--inicio", type=int, nargs=2, default=[0, 0], metavar=("LINHA", "COLUNA"),
                   help="posição inicial, índices a partir de 0")
    p.add_argument("-e", "--estrategia", choices=["hibrida", "warnsdorff", "guloso", "forca"], default="hibrida")
    p.add_argument("-l", "--limite", type=int, default=LIMITE_PADRAO, help="limite de nós visitados")
    p.add_argument("--gui", action="store_true", help="abre a interface gráfica simples (tkinter)")
    p.add_argument("--web", action="store_true", help="abre a interface web no navegador")
    p.add_argument("--porta", type=int, default=8765, help="porta da interface web")
    a = p.parse_args(argv)
    if a.web:
        servir(a.porta)
        return 0
    if a.gui:
        abrir_gui()
        return 0
    try:
        res = resolver(a.linhas, a.colunas, tuple(a.inicio), a.estrategia, a.limite)
    except ValueError as e:
        print("Erro:", e, file=sys.stderr)
        return 1
    print(tabuleiro_texto(res))
    print()
    print(relatorio_texto(res))
    return 0


if __name__ == "__main__":
    sys.exit(main())
