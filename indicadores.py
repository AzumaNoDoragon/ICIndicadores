import streamlit as st
import pandas as pd
from img import IMG

def resultadosCol(lista, col_imagens):
    cols = st.columns(min(3, len(lista)))
    for i, (_, row) in enumerate(lista.iterrows()):
        with cols[i]:
            num = int(row["Imagem"].split()[1])
            total = len(df[col_imagens[num-1]].dropna())
            acertos = int((df[col_imagens[num-1]] == row["Tipo"]).sum())
            st.image(IMG[f"img_{num}"]["path"], caption=row["Imagem"])
            m_a, m_e, m_t = st.columns(3)
            m_a.metric("Acertos", acertos)
            m_e.metric("Erros", total - acertos)
            m_t.metric("Taxa", f"{round(row['Taxa de acerto']*100,1)}%")

def resultado(acertoImagem, col_imagens, gabarito):
    idx_max = acertoImagem.index(max(acertoImagem))
    idx_min = acertoImagem.index(min(acertoImagem))
    img_max = f"img_{idx_max+1}"
    img_min = f"img_{idx_min+1}"
    total_max = len(df[col_imagens[idx_max]].dropna())
    acertos_max = int((df[col_imagens[idx_max]] == gabarito[idx_max]).sum())
    total_min = len(df[col_imagens[idx_min]].dropna())
    acertos_min = int((df[col_imagens[idx_min]] == gabarito[idx_min]).sum())

    st.subheader("Melhor e pior imagem")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Maior taxa de acerto")
        st.image(IMG[img_max]["path"], caption=img_max)
        m_a, m_e, m_t = st.columns(3)
        m_a.metric("Acertos", acertos_max)
        m_e.metric("Erros", total_max - acertos_max)
        m_t.metric("Taxa", f"{round(acertoImagem[idx_max]*100,1)}%")
    
    with col2:
        st.subheader("Menor taxa de acerto")
        st.image(IMG[img_min]["path"], caption=img_min)
        m_a, m_e, m_t = st.columns(3)
        m_a.metric("Acertos", acertos_min)
        m_e.metric("Erros", total_min - acertos_min)
        m_t.metric("Taxa", f"{round(acertoImagem[idx_min]*100,1)}%")

def taxaAcertoEtapa(df_imagens, col_imagens, gabarito):
    st.header("Análise por Etapas")

    etapa_size = 12

    etapas = {
        "Etapa 1": (0, etapa_size),
        "Etapa 2": (etapa_size, etapa_size * 2),
        "Etapa 3": (etapa_size * 2, etapa_size * 3),
    }

    resultados = {}

    for nome, (inicio, fim) in etapas.items():
        cols_etapa = col_imagens[inicio:fim]
        gabarito_etapa = gabarito[inicio:fim]

        total_respostas = 0
        total_acertos = 0

        total_real = 0
        acertos_real = 0

        total_fake = 0
        acertos_fake = 0

        for i, col in enumerate(cols_etapa):
            respostas = df_imagens[col].dropna()
            correto = gabarito_etapa[i]

            acertos = (respostas == correto).sum()
            total = len(respostas)

            total_respostas += total
            total_acertos += acertos

            if correto == "Real":
                total_real += total
                acertos_real += acertos
            else:
                total_fake += total
                acertos_fake += acertos

        taxa_geral = total_acertos / total_respostas if total_respostas else 0
        taxa_real = acertos_real / total_real if total_real else 0
        taxa_fake = acertos_fake / total_fake if total_fake else 0

        resultados[nome] = {
            "geral": taxa_geral,
            "real": taxa_real,
            "fake": taxa_fake
        }

    for nome in etapas.keys():
        st.subheader(nome)
        c1, c2, c3 = st.columns(3)

        c1.metric("Taxa Geral", f"{resultados[nome]['geral']*100:.1f}%")
        c2.metric("Taxa Reais", f"{resultados[nome]['real']*100:.1f}%")
        c3.metric("Taxa Sintetizadas", f"{resultados[nome]['fake']*100:.1f}%")

    st.subheader("Evolução entre Etapas")

    def delta(a, b):
        return (b - a) * 100

    e1 = resultados["Etapa 1"]
    e2 = resultados["Etapa 2"]
    e3 = resultados["Etapa 3"]

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("### Etapa 1 → Etapa 2")
        st.metric("Geral", f"{e1['geral']*100:.1f}%", f"{delta(e1['geral'], e2['geral']):+.1f}%")
        st.metric("Reais", f"{e1['real']*100:.1f}%", f"{delta(e1['real'], e2['real']):+.1f}%")
        st.metric("Sintetizadas", f"{e1['fake']*100:.1f}%", f"{delta(e1['fake'], e2['fake']):+.1f}%")

    with col2:
        st.markdown("### Etapa 2 → Etapa 3")
        st.metric("Geral", f"{e2['geral']*100:.1f}%", f"{delta(e2['geral'], e3['geral']):+.1f}%")
        st.metric("Reais", f"{e2['real']*100:.1f}%", f"{delta(e2['real'], e3['real']):+.1f}%")
        st.metric("Sintetizadas", f"{e2['fake']*100:.1f}%", f"{delta(e2['fake'], e3['fake']):+.1f}%")
    
    with col3:
        st.markdown("### Etapa 1 → Etapa 3")
        st.metric("Geral", f"{e3['geral']*100:.1f}%", f"{delta(e1['geral'], e3['geral']):+.1f}%")
        st.metric("Reais", f"{e3['real']*100:.1f}%", f"{delta(e1['real'], e3['real']):+.1f}%")
        st.metric("Sintetizadas", f"{e3['fake']*100:.1f}%", f"{delta(e1['fake'], e3['fake']):+.1f}%")

def taxaPorDificuldade(df_imagens, col_imagens, gabarito):
    st.header("Análise por Dificuldade")

    etapa_size = 12

    etapas = {
        "Etapa 1": (0, etapa_size),
        "Etapa 2": (etapa_size, etapa_size * 2),
        "Etapa 3": (etapa_size * 2, etapa_size * 3),
    }

    resultados = {}

    for nome, (inicio, fim) in etapas.items():
        cols_etapa = col_imagens[inicio:fim]

        total = {"f": 0, "m": 0, "d": 0}
        acertos = {"f": 0, "m": 0, "d": 0}

        for i, col in enumerate(cols_etapa):
            img_index = inicio + i + 1
            img_key = f"img_{img_index}"
            info = IMG[img_key]

            if info["label"] != "Sintetizada":
                continue  # ignora imagens reais

            dificuldade = info["dif"]

            respostas = df_imagens[col].dropna()
            correto = "Sintetizada"

            acertos_img = (respostas == correto).sum()
            total_img = len(respostas)

            total[dificuldade] += total_img
            acertos[dificuldade] += acertos_img

        taxas = {
            k: (acertos[k] / total[k] if total[k] > 0 else 0)
            for k in ["f", "m", "d"]
        }

        resultados[nome] = taxas

    for nome in etapas.keys():
        st.subheader(nome)
        c1, c2, c3 = st.columns(3)

        c1.metric("Fácil", f"{resultados[nome]['f']*100:.1f}%")
        c2.metric("Médio", f"{resultados[nome]['m']*100:.1f}%")
        c3.metric("Difícil", f"{resultados[nome]['d']*100:.1f}%")

    st.subheader("Evolução por Dificuldade")

    def delta(a, b):
        return (b - a) * 100

    e1 = resultados["Etapa 1"]
    e2 = resultados["Etapa 2"]
    e3 = resultados["Etapa 3"]

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("### Fácil (E1 → E3)")
        st.metric("Taxa", f"{e1['f']*100:.1f}%", f"{delta(e1['f'], e3['f']):+.1f}%")

    with col2:
        st.markdown("### Médio (E1 → E3)")
        st.metric("Taxa", f"{e2['m']*100:.1f}%", f"{delta(e1['m'], e3['m']):+.1f}%")

    with col3:
        st.markdown("### Difícil (E1 → E3)")
        st.metric("Taxa", f"{e3['d']*100:.1f}%", f"{delta(e1['d'], e3['d']):+.1f}%")

st.set_page_config(layout="wide")
st.title("Análise de Indicadores de Deepfakes")

arquivo = st.file_uploader("Envie o CSV do Google Forms", type=["csv"])

if arquivo:
    df = pd.read_csv(arquivo)

    num_imagens = len(IMG)
    primeiro_indice = next(
        (i for i, col in enumerate(df.columns) if "para você, esta imagem é" in str(col).lower()),
        None,
    )

    if primeiro_indice is None:
        st.error("Não foi possível localizar as colunas de perguntas de imagens no CSV.")
    else:
        col_start = primeiro_indice
        col_end = col_start + num_imagens
        col_imagens = df.columns[col_start:col_end]

        df_imagens = df.iloc[:, col_start:col_end].copy()

        st.subheader(f"Total de participantes: {len(df_imagens)}")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.subheader(f"Total de imagens: {num_imagens}")
        with col2:
            reais = sum(1 for img in IMG.values() if img['label'] == 'Real')
            st.subheader(f"Reais: {reais}")
        with col3:
            sintetizada = sum(1 for img in IMG.values() if img['label'] == 'Sintetizada')
            st.subheader(f"Sintetizada: {sintetizada}")
        
        gabarito = [IMG[f"img_{i+1}"]["label"] for i in range(len(col_imagens))]

        acertosUsuario = []
        for _, row in df_imagens.iterrows():
            acertos = 0
            for i, resp in enumerate(row):
                if resp == gabarito[i]:
                    acertos += 1
            acertosUsuario.append(acertos)

        df_imagens["acertos"] = acertosUsuario

        st.header("Indicadores principais")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Média de acertos", round(df_imagens["acertos"].mean(), 2))
        with col2:
            st.metric("Maior número de acertos", int(df_imagens["acertos"].max()))
        with col3:
            st.metric("Menor número de acertos", int(df_imagens["acertos"].min()))

        acertoImagem = []
        for i, col in enumerate(df_imagens.columns[:-1]):
            respostas = df_imagens[col].dropna()
            
            acertos = (respostas == gabarito[i]).sum()
            taxa = acertos / len(respostas) if len(respostas) > 0 else 0
            
            acertoImagem.append(taxa)

        df_imagem_stats = pd.DataFrame({
            "Imagem": [f"Img {i+1}" for i in range(len(col_imagens))],
            "Taxa de acerto": acertoImagem,
            "Tipo": gabarito,
        })

        resultado(acertoImagem, col_imagens, gabarito)

        df_imagem_stats["Erros"] = [
            len(df[col].dropna()) - (df[col].dropna() == gabarito[i]).sum()
            for i, col in enumerate(col_imagens)
        ]

        df_fake = df_imagem_stats[df_imagem_stats["Tipo"] == "Sintetizada"].sort_values("Erros", ascending=False).head(3)
        df_real = df_imagem_stats[df_imagem_stats["Tipo"] == "Real"].sort_values("Erros", ascending=False).head(3)
        df_fake_best = df_imagem_stats[df_imagem_stats["Tipo"] == "Sintetizada"].sort_values("Taxa de acerto", ascending=False).head(3)
        df_real_best = df_imagem_stats[df_imagem_stats["Tipo"] == "Real"].sort_values("Taxa de acerto", ascending=False).head(3)

        st.subheader("Deepfakes")
        st.subheader("Mais acertadas")
        resultadosCol(df_fake_best, col_imagens)
        st.subheader("Mais erradas")
        resultadosCol(df_fake, col_imagens)
        st.subheader("Reais")
        st.subheader("Mais acertadas")
        resultadosCol(df_real_best, col_imagens)
        st.subheader("Mais erradas")
        resultadosCol(df_real, col_imagens)

        taxaAcertoEtapa(df_imagens, col_imagens, gabarito)

        taxaPorDificuldade(df_imagens, col_imagens, gabarito)