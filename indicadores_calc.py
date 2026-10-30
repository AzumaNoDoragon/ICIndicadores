"""
Cálculos dos indicadores coletivos do experimento (sem nada de Streamlit aqui).

Ideia central: em vez de vários laços aninhados, montamos UMA tabela "longa"
(1 linha = 1 resposta de 1 participante a 1 imagem). Todos os indicadores
saem dela com groupby/pivot, então o número de cada tela vem sempre da
mesma fonte.
"""

import numpy as np
import pandas as pd

ETAPA_SIZE = 12
ETAPAS = ["Etapa 1", "Etapa 2", "Etapa 3"]
DIF_NOMES = {"f": "Fácil", "m": "Média", "d": "Difícil"}
CATEGORIAS = ["Real", "Fácil", "Média", "Difícil"]
INCERTO = "Não tenho certeza"
RESPOSTAS = ["Real", "Sintetizada", INCERTO]

# Gabarito oficial (R = real, F/M/D = sintética fácil/média/difícil),
# na ordem em que as imagens aparecem no formulário.
GABARITO_OFICIAL = "RFMMFRRRRRRR" + "RRRRRRFFMMDD" + "RMRRRDRFDRMR"

# ----------------------------------------------------------------------
# Leitura e validação
# ----------------------------------------------------------------------
def remover_identificadores(df):
    """Tira qualquer coluna de e-mail logo na entrada."""
    cols = [c for c in df.columns if "mail" in str(c).lower()]
    return df.drop(columns=cols)

def localizar_colunas_imagens(df, n_esperado):
    """Acha as colunas 'Para você, esta imagem é' pelo NOME (não por posição)
    e confere se são exatamente n_esperado."""
    cols = [c for c in df.columns if "para você, esta imagem é" in str(c).lower()]
    if len(cols) != n_esperado:
        raise ValueError(
            f"Encontrei {len(cols)} colunas de imagem no CSV, mas o IMG tem {n_esperado}."
        )
    return cols

def _codigo_img(info):
    if info["label"] == "Real":
        return "R"
    return info["dif"].upper()  # 'f','m','d' -> F, M, D

def validar_gabarito(IMG):
    """Compara o IMG (label + dif de cada imagem) com o gabarito oficial.
    Devolve a lista de divergências; lista vazia = tudo certo."""
    problemas = []
    if len(IMG) != len(GABARITO_OFICIAL):
        problemas.append(f"IMG tem {len(IMG)} imagens, o gabarito oficial tem {len(GABARITO_OFICIAL)}.")
        return problemas
    for pos, esperado in enumerate(GABARITO_OFICIAL, start=1):
        encontrado = _codigo_img(IMG[f"img_{pos}"])
        if encontrado != esperado:
            problemas.append(f"img_{pos}: esperado '{esperado}', IMG diz '{encontrado}'.")
    return problemas

# ----------------------------------------------------------------------
# Tabela longa
# ----------------------------------------------------------------------
def _categoria(info):
    return "Real" if info["label"] == "Real" else DIF_NOMES[info["dif"]]

def montar_base_longa(df, col_imagens, IMG):
    partes = []
    for pos, col in enumerate(col_imagens):
        info = IMG[f"img_{pos + 1}"]
        resp = df[col].dropna().astype(str).str.strip()
        partes.append(pd.DataFrame({
            "participante": resp.index,
            "imagem": pos + 1,
            "etapa": ETAPAS[pos // ETAPA_SIZE],
            "tipo": info["label"],
            "categoria": _categoria(info),
            "resposta": resp.values,
        }))
    longa = pd.concat(partes, ignore_index=True)
    longa = longa[longa["resposta"].isin(RESPOSTAS)].copy()
    longa["acertou"] = (longa["resposta"] == longa["tipo"]).astype(int)
    longa["incerto"] = (longa["resposta"] == INCERTO).astype(int)
    longa["disse_sintetizada"] = (longa["resposta"] == "Sintetizada").astype(int)
    return longa

# ----------------------------------------------------------------------
# Indicadores
# ----------------------------------------------------------------------
def _taxas(g):
    reais = g[g["tipo"] == "Real"]["acertou"]
    fakes = g[g["tipo"] == "Sintetizada"]["acertou"]
    t_real = reais.mean() if len(reais) else np.nan
    t_fake = fakes.mean() if len(fakes) else np.nan
    return {
        "Balanceada": np.nanmean([t_real, t_fake]),
        "Geral": g["acertou"].mean(),
        "Reais": t_real,
        "Sintetizadas": t_fake,
        "Não tenho certeza": g["incerto"].mean(),
        "Disse 'Sintetizada'": g["disse_sintetizada"].mean(),
    }

def indicadores_gerais(longa):
    return _taxas(longa)

def indicadores_por_etapa(longa):
    return pd.DataFrame({e: _taxas(longa[longa["etapa"] == e]) for e in ETAPAS}).T

def indicadores_por_categoria(longa):
    """Taxa de acerto (etapa x categoria) e quantas imagens existem em cada célula."""
    taxa = longa.pivot_table(index="etapa", columns="categoria",
                             values="acertou", aggfunc="mean")
    taxa = taxa.reindex(index=ETAPAS, columns=CATEGORIAS)
    n_img = (longa.drop_duplicates(["etapa", "imagem"])
             .pivot_table(index="etapa", columns="categoria",
                          values="imagem", aggfunc="count"))
    n_img = n_img.reindex(index=ETAPAS, columns=CATEGORIAS).fillna(0).astype(int)
    return taxa, n_img

def indicadores_por_imagem(longa):
    out = longa.groupby("imagem").agg(
        etapa=("etapa", "first"), tipo=("tipo", "first"),
        categoria=("categoria", "first"), respostas=("acertou", "size"),
        acertos=("acertou", "sum"), taxa=("acertou", "mean"),
    )
    dist = pd.crosstab(longa["imagem"], longa["resposta"], normalize="index")
    dist = dist.reindex(columns=RESPOSTAS, fill_value=0)
    out = out.join(dist)
    out["erros"] = out["respostas"] - out["acertos"]
    return out

def acertos_por_participante(longa):
    return longa.groupby("participante")["acertou"].sum()

# ----------------------------------------------------------------------
# Para o pesquisador (testes pareados)
# ----------------------------------------------------------------------
def balanceada_por_participante(longa):
    t = longa.pivot_table(index=["participante", "etapa"], columns="tipo",
                          values="acertou", aggfunc="mean")
    t["bal"] = t[["Real", "Sintetizada"]].mean(axis=1)
    return t["bal"].unstack("etapa").reindex(columns=ETAPAS)

def testes_pareados(bal):
    """Wilcoxon pareado entre etapas, sobre a acurácia balanceada de cada pessoa."""
    from scipy import stats
    linhas = []
    for a, b in [("Etapa 1", "Etapa 2"), ("Etapa 2", "Etapa 3"), ("Etapa 1", "Etapa 3")]:
        sub = bal[[a, b]].dropna()
        try:
            _, p = stats.wilcoxon(sub[a], sub[b])
        except ValueError:
            p = np.nan
        linhas.append({
            "Comparação": f"{a} → {b}", "n": len(sub),
            "Variação média (p.p.)": (sub[b] - sub[a]).mean() * 100,
            "p-valor": p,
        })
    return pd.DataFrame(linhas)