import streamlit as st
import pandas as pd
import img

st.set_page_config(layout="wide")
st.title("Análise de Indicadores de Deepfakes")

arquivo = st.file_uploader("Envie o CSV do Google Forms", type=["csv"])

if arquivo:
    df = pd.read_csv(arquivo)

    def normalize_answer(resp):
        if pd.isna(resp):
            return resp
        resp_norm = str(resp).strip().lower()
        if resp_norm == "real":
            return "Real"
        if resp_norm in {"sintética", "sintetica", "sintetizada"}:
            return "Sintética"
        return resp

    num_imagens = len(img.IMG)
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
        df_imagens_clean = df_imagens.dropna(how="all")
        df = df.loc[df_imagens_clean.index].reset_index(drop=True)
        df_imagens = df_imagens_clean.reset_index(drop=True)

        st.subheader(f"Total de participantes: {len(df)}")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.subheader(f"Total de imagens: {len(col_imagens)}")
        with col2:
            st.subheader("Reais: 21")
        with col3:
            st.subheader("Sintéticas: 15")
        
        gabarito = [img.IMG[f"img_{i+1}"]["label"] for i in range(len(col_imagens))]

        acertos_por_usuario = []
        for _, row in df_imagens.iterrows():
            acertos = 0
            for i, resp in enumerate(row):
                if pd.notna(resp) and normalize_answer(resp) == gabarito[i]:
                    acertos += 1
            acertos_por_usuario.append(acertos)

        df["acertos"] = acertos_por_usuario

        st.header("Indicadores principais")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Média de acertos", round(df["acertos"].mean(), 2))
        with col2:
            st.metric("Maior número de acertos", int(df["acertos"].max()))
        with col3:
            st.metric("Menor número de acertos", int(df["acertos"].min()))

        acerto_por_imagem = []
        for i, col in enumerate(col_imagens):
            respostas_validas = df[col].dropna()
            if len(respostas_validas) > 0:
                acertos = (respostas_validas.map(normalize_answer) == gabarito[i]).sum()
                taxa = acertos / len(respostas_validas)
            else:
                taxa = 0
            acerto_por_imagem.append(taxa)

        df_imagem_stats = pd.DataFrame({
            "Imagem": [f"Img {i+1}" for i in range(len(col_imagens))],
            "Taxa de acerto": acerto_por_imagem,
            "Tipo": gabarito,
        })

        idx_max = acerto_por_imagem.index(max(acerto_por_imagem))
        idx_min = acerto_por_imagem.index(min(acerto_por_imagem))
        img_max = f"img_{idx_max+1}"
        img_min = f"img_{idx_min+1}"

        st.subheader("Melhor e pior imagem")
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Maior taxa de acerto")
            st.image(img.IMG[img_max]["path"], caption=img_max)
            # Adicionado os 3 dados solicitados
            total_max = len(df[col_imagens[idx_max]].dropna())
            acertos_max = int((df[col_imagens[idx_max]].map(normalize_answer) == gabarito[idx_max]).sum())
            m_a, m_e, m_t = st.columns(3)
            m_a.metric("Acertos", acertos_max)
            m_e.metric("Erros", total_max - acertos_max)
            m_t.metric("Taxa", f"{round(acerto_por_imagem[idx_max]*100,1)}%")

        with col2:
            st.subheader("Menor taxa de acerto")
            st.image(img.IMG[img_min]["path"], caption=img_min)
            # Adicionado os 3 dados solicitados
            total_min = len(df[col_imagens[idx_min]].dropna())
            acertos_min = int((df[col_imagens[idx_min]].map(normalize_answer) == gabarito[idx_min]).sum())
            m_a, m_e, m_t = st.columns(3)
            m_a.metric("Acertos", acertos_min)
            m_e.metric("Erros", total_min - acertos_min)
            m_t.metric("Taxa", f"{round(acerto_por_imagem[idx_min]*100,1)}%")

        df_imagem_stats["Erros"] = [
            len(df[col].dropna()) - (df[col].dropna().map(normalize_answer) == gabarito[i]).sum()
            for i, col in enumerate(col_imagens)
        ]

        df_fake = df_imagem_stats[df_imagem_stats["Tipo"] == "Sintética"].sort_values("Erros", ascending=False).head(3)
        df_real = df_imagem_stats[df_imagem_stats["Tipo"] == "Real"].sort_values("Erros", ascending=False).head(3)
        df_fake_best = df_imagem_stats[df_imagem_stats["Tipo"] == "Sintética"].sort_values("Taxa de acerto", ascending=False).head(3)
        df_real_best = df_imagem_stats[df_imagem_stats["Tipo"] == "Real"].sort_values("Taxa de acerto", ascending=False).head(3)

        if not df_fake.empty or not df_fake_best.empty:
            st.subheader("Deepfakes")
            
            st.subheader("Mais acertadas")
            if not df_fake_best.empty:
                cols = st.columns(min(3, len(df_fake_best)))
                for i, (_, row) in enumerate(df_fake_best.iterrows()):
                    with cols[i]:
                        num = int(row["Imagem"].split()[1])
                        total = len(df[col_imagens[num-1]].dropna())
                        acertos = int((df[col_imagens[num-1]].map(normalize_answer) == row["Tipo"]).sum())
                        st.image(img.IMG[f"img_{num}"]["path"], caption=row["Imagem"])
                        m_a, m_e, m_t = st.columns(3)
                        m_a.metric("Acertos", acertos)
                        m_e.metric("Erros", total - acertos)
                        m_t.metric("Taxa", f"{round(row['Taxa de acerto']*100,1)}%")

            st.subheader("Mais erradas")
            if not df_fake.empty:
                cols = st.columns(min(3, len(df_fake)))
                for i, (_, row) in enumerate(df_fake.iterrows()):
                    with cols[i]:
                        num = int(row["Imagem"].split()[1])
                        total = len(df[col_imagens[num-1]].dropna())
                        acertos = int((df[col_imagens[num-1]].map(normalize_answer) == row["Tipo"]).sum())
                        st.image(img.IMG[f"img_{num}"]["path"], caption=row["Imagem"])
                        m_a, m_e, m_t = st.columns(3)
                        m_a.metric("Acertos", acertos)
                        m_e.metric("Erros", total - acertos)
                        m_t.metric("Taxa", f"{round(row['Taxa de acerto']*100,1)}%")

        if not df_real.empty or not df_real_best.empty:
            st.subheader("Reais")

            st.subheader("Mais acertadas")
            if not df_real_best.empty:
                cols = st.columns(min(3, len(df_real_best)))
                for i, (_, row) in enumerate(df_real_best.iterrows()):
                    with cols[i]:
                        num = int(row["Imagem"].split()[1])
                        total = len(df[col_imagens[num-1]].dropna())
                        acertos = int((df[col_imagens[num-1]].map(normalize_answer) == row["Tipo"]).sum())
                        st.image(img.IMG[f"img_{num}"]["path"], caption=row["Imagem"])
                        m_a, m_e, m_t = st.columns(3)
                        m_a.metric("Acertos", acertos)
                        m_e.metric("Erros", total - acertos)
                        m_t.metric("Taxa", f"{round(row['Taxa de acerto']*100,1)}%")

            st.subheader("Mais erradas")
            if not df_real.empty:
                cols = st.columns(min(3, len(df_real)))
                for i, (_, row) in enumerate(df_real.iterrows()):
                    with cols[i]:
                        num = int(row["Imagem"].split()[1])
                        total = len(df[col_imagens[num-1]].dropna())
                        acertos = int((df[col_imagens[num-1]].map(normalize_answer) == row["Tipo"]).sum())
                        st.image(img.IMG[f"img_{num}"]["path"], caption=row["Imagem"])
                        m_a, m_e, m_t = st.columns(3)
                        m_a.metric("Acertos", acertos)
                        m_e.metric("Erros", total - acertos)
                        m_t.metric("Taxa", f"{round(row['Taxa de acerto']*100,1)}%")