import numpy as np
import pandas as pd
import streamlit as st

from img import IMG
import indicadores_calc as calc

MIN_PARTICIPANTES = 5

def pct(x):
    return "—" if pd.isna(x) else f"{x * 100:.1f}%"

def delta_pp(a, b):
    """Variação em pontos percentuais (b - a); None se algum lado não existe."""
    if pd.isna(a) or pd.isna(b):
        return None
    return f"{(b - a) * 100:+.1f} p.p."

def card_imagem(num, linha):
    info = IMG[f"img_{num}"]
    st.image(info["path"], caption=f"Img {num} · {linha['categoria']} · {linha['etapa']}")
    a, e, t = st.columns(3)
    a.metric("Acertos", int(linha["acertos"]))
    e.metric("Erros", int(linha["erros"]))
    t.metric("Taxa", pct(linha["taxa"]))
    st.caption(
        f"Responderam: {linha['Real'] * 100:.0f}% Real · "
        f"{linha['Sintetizada'] * 100:.0f}% Sintetizada · "
        f"{linha[calc.INCERTO] * 100:.0f}% Não tenho certeza"
    )

def grupo_de_cards(tabela):
    cols = st.columns(3)
    for col, (num, linha) in zip(cols, tabela.iterrows()):
        with col:
            card_imagem(int(num), linha)

# ----------------------------------------------------------------------
st.set_page_config(layout="wide")
st.title("Análise de Indicadores de Deepfakes")

arquivo = st.file_uploader("Envie o CSV do Google Forms", type=["csv"])
if not arquivo:
    st.stop()

df = calc.remover_identificadores(pd.read_csv(arquivo))

problemas = calc.validar_gabarito(IMG)
if problemas:
    st.error("O arquivo img.py não bate com o gabarito oficial:\n\n- " + "\n- ".join(problemas))
    st.stop()

try:
    col_imagens = calc.localizar_colunas_imagens(df, len(IMG))
except ValueError as erro:
    st.error(str(erro))
    st.stop()

longa = calc.montar_base_longa(df, col_imagens, IMG)
n_part = longa["participante"].nunique()

if n_part < MIN_PARTICIPANTES:
    st.warning(f"Só {n_part} participante(s): com grupos tão pequenos, os números coletivos "
               "podem permitir identificar pessoas. Considere não exibir em público.")

geral = calc.indicadores_gerais(longa)
por_etapa = calc.indicadores_por_etapa(longa)
taxa_cat, n_img_cat = calc.indicadores_por_categoria(longa)
por_imagem = calc.indicadores_por_imagem(longa)
acertos_part = calc.acertos_por_participante(longa)

aba_geral, aba_etapa, aba_dif, aba_img, aba_stats = st.tabs(
    ["Visão geral", "Por etapa", "Por dificuldade", "Por imagem", "Estatística (pesquisador)"]
)

# ---------------------------- VISÃO GERAL -----------------------------
with aba_geral:
    n_total = len(IMG)
    n_real = sum(1 for i in IMG.values() if i["label"] == "Real")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Participantes", n_part)
    c2.metric("Imagens", f"{n_total} ({n_real} reais · {n_total - n_real} sintetizadas)")
    c3.metric("Média de acertos do grupo", f"{acertos_part.mean():.1f} de {n_total}")
    c4.metric("Acurácia balanceada", pct(geral["Balanceada"]))
    st.caption("Acurácia balanceada = média entre a taxa de acerto em imagens reais e em "
               "sintetizadas. O acaso fica em 50%, e a medida não muda só porque uma etapa "
               "tem mais imagens reais do que outra.")

    d1, d2, d3 = st.columns(3)
    d1.metric("Acerto em imagens reais", pct(geral["Reais"]))
    d2.metric("Acerto em imagens sintetizadas", pct(geral["Sintetizadas"]))
    d3.metric("Marcaram 'Não tenho certeza'", pct(geral["Não tenho certeza"]))

    st.subheader("Como o grupo se distribuiu")
    st.caption("Quantas pessoas acertaram cada número de imagens (sem identificar ninguém).")
    dist = (acertos_part.value_counts().reindex(range(n_total + 1), fill_value=0).sort_index())
    st.bar_chart(dist.rename("Participantes"))

# ----------------------------- POR ETAPA ------------------------------
with aba_etapa:
    for etapa in calc.ETAPAS:
        r = por_etapa.loc[etapa]
        st.subheader(etapa)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Balanceada", pct(r["Balanceada"]))
        c2.metric("Reais", pct(r["Reais"]))
        c3.metric("Sintetizadas", pct(r["Sintetizadas"]))
        c4.metric("Não tenho certeza", pct(r["Não tenho certeza"]))

    st.subheader("Evolução entre etapas")
    st.caption("O valor mostrado é o da etapa de chegada; a seta é a variação em pontos percentuais.")
    pares = [("Etapa 1", "Etapa 2"), ("Etapa 2", "Etapa 3"), ("Etapa 1", "Etapa 3")]
    for col, (a, b) in zip(st.columns(3), pares):
        with col:
            st.markdown(f"### {a} → {b}")
            for rotulo, chave in [("Balanceada", "Balanceada"), ("Reais", "Reais"),
                                  ("Sintetizadas", "Sintetizadas")]:
                col.metric(rotulo, pct(por_etapa.loc[b, chave]),
                           delta_pp(por_etapa.loc[a, chave], por_etapa.loc[b, chave]))

    st.bar_chart((por_etapa[["Balanceada", "Reais", "Sintetizadas"]] * 100).round(1))

# --------------------------- POR DIFICULDADE --------------------------
with aba_dif:
    st.caption("A dificuldade das imagens muda de uma etapa para outra (a Etapa 1 não tem "
               "nenhuma imagem difícil). Por isso a comparação justa é feita categoria por "
               "categoria. '—' significa que a etapa não tem imagens daquela categoria.")
    st.subheader("Taxa de acerto por etapa e categoria")
    st.dataframe(taxa_cat.style.format("{:.1%}", na_rep="—"))
    st.subheader("Quantas imagens há em cada célula")
    st.dataframe(n_img_cat)
    st.caption("Com 1 ou 2 imagens por célula, uma única imagem muda muito a taxa: "
               "leia as diferenças como indícios, não como conclusões.")

    st.subheader("Evolução por categoria")
    evol = [("Real", "Etapa 1", "Etapa 3"), ("Fácil", "Etapa 1", "Etapa 3"),
            ("Média", "Etapa 1", "Etapa 3"), ("Difícil", "Etapa 2", "Etapa 3")]
    for col, (cat, a, b) in zip(st.columns(4), evol):
        with col:
            st.markdown(f"### {cat} ({a[-1]} → {b[-1]})")
            st.metric("Taxa", pct(taxa_cat.loc[b, cat]), delta_pp(taxa_cat.loc[a, cat], taxa_cat.loc[b, cat]))
    st.caption("Difícil é comparada da Etapa 2 para a 3 porque só aparece a partir da Etapa 2.")

# ----------------------------- POR IMAGEM -----------------------------
with aba_img:
    deep = por_imagem[por_imagem["tipo"] == "Sintetizada"]
    reais = por_imagem[por_imagem["tipo"] == "Real"]

    st.header("Deepfakes")
    st.subheader("Mais acertadas")
    grupo_de_cards(deep.sort_values("taxa", ascending=False).head(3))
    st.subheader("Mais erradas")
    grupo_de_cards(deep.sort_values("taxa").head(3))

    st.header("Imagens reais")
    st.subheader("Mais acertadas")
    grupo_de_cards(reais.sort_values("taxa", ascending=False).head(3))
    st.subheader("Mais erradas")
    grupo_de_cards(reais.sort_values("taxa").head(3))

# ------------------------ ESTATÍSTICA (PESQUISADOR) -------------------
with aba_stats:
    st.caption("Comparação pareada entre etapas (Wilcoxon) sobre a acurácia balanceada de cada "
               "pessoa. Mostra apenas o resultado do teste, sem dados individuais.")
    bal = calc.balanceada_por_participante(longa)
    try:
        st.dataframe(calc.testes_pareados(bal).style.format(
            {"Variação média (p.p.)": "{:+.1f}", "p-valor": "{:.4f}"}, na_rep="—"),
            )
    except ImportError:
        st.info("Instale o scipy (pip install scipy) para ver os testes estatísticos.")