# -*- coding: utf-8 -*-
"""Validação independente: todo caminho devolvido deve ser um passeio legítimo."""
from passeio_cavalo import resolver, limite_superior

def valido(res):
    c = res.caminho
    assert c[0] == res.inicio
    assert len(set(c)) == len(c), "casa repetida"
    for (a, b), (x, y) in zip(c, c[1:]):
        assert sorted((abs(a - x), abs(b - y))) == [1, 2], "movimento inválido"
    assert all(0 <= r < res.linhas and 0 <= k < res.colunas for r, k in c)
    return True

n = 0
for est in ("hibrida", "warnsdorff", "forca"):
    for m in (5, 8):
        for r in range(m):
            for c in range(m):
                res = resolver(m, m, (r, c), est, 200_000)
                assert valido(res); n += 1
                if est == "hibrida":
                    assert res.visitadas == limite_superior(m, m, (r, c))
print(f"{n} execuções validadas com sucesso.")
