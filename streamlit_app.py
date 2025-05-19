# streamlit_app.py
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px


st.title("Pipe Defects Visualization")
st.markdown("Upload an Excel file to visualize pipeline defects as colored rectangles.")

try:
    uploaded_file = st.file_uploader("Choose Excel file", type="xlsx")
except Exception as e:
    st.error(f"📛 حدث خطأ أثناء قراءة الملف: {e}")

if uploaded_file is not None:
    try:
        df = pd.read_excel(uploaded_file, engine="openpyxl")

        # Extract columns
        df['Distance'] = pd.to_numeric(df.iloc[:, 3], errors='coerce')
        df['Orientation'] = df.iloc[:, 9]
        df['Peak'] = pd.to_numeric(df.iloc[:, 5], errors='coerce')

        # Length and Width columns
        length_col = next((col for col in df.columns if 'Length' in col), None)
        width_col = next((col for col in df.columns if 'Width' in col), None)

        df['Length'] = pd.to_numeric(df[length_col], errors='coerce') / 1000
        df['Width'] = pd.to_numeric(df[width_col], errors='coerce') / 1000

        # Orientation to angle
        def time_to_deg(value):
            try:
                h, m = map(int, str(value).strip().split(":"))
                return (h % 12 + m / 60) * 30
            except:
                return np.nan

        df['Angle'] = df['Orientation'].apply(time_to_deg)
        df = df.dropna(subset=['Distance', 'Angle', 'Peak', 'Length', 'Width'])

        # Pipe specs
        pipe_diam_m = 12 * 0.0254
        pipe_circum = np.pi * pipe_diam_m
        df['Angle Span'] = (df['Width'] / pipe_circum) * 360

        # Filter distance interactively
        min_dist = float(df['Distance'].min())
        max_dist = float(df['Distance'].max())
        user_min_dist = st.slider("Minimum Distance", min_value=min_dist, max_value=max_dist, value=min_dist)
        user_max_dist = st.slider("Maximum Distance", min_value=min_dist, max_value=max_dist, value=max_dist)
        
        df = df[(df['Distance'] >= user_min_dist) & (df['Distance'] <= user_max_dist)]


        # Color mapping
        def color_map(peak):
            if peak < 0.3:
                return plt.cm.Blues(peak)
            elif 0.3 <= peak <= 0.5:
                return plt.cm.Oranges(peak)
            else:
                return plt.cm.Reds(min(peak, 1))


        # Plotting
        fig = go.Figure()

        # نحضّر بيانات الأعمدة (بار أفقي مائل يمثل المستطيلات)
        df['y_start'] = df['Angle'] - df['Angle Span'] / 2
        df['y_end'] = df['Angle'] + df['Angle Span'] / 2

        # نستخدم scatter لإنشاء أشكال مستطيلية عبر rectangles
        bars = go.Bar(
            x=df['Length'],
            y=df['Angle'],
            orientation='h',
            marker=dict(
                color=[f"rgb({int(c[0]*255)},{int(c[1]*255)},{int(c[2]*255)})" for c in df['Peak'].apply(color_map)],
                line=dict(width=0)
            ),
            width=df['Angle Span'],
            hovertext=[
                f"Distance: {d:.2f} m<br>Peak: {p:.2f}<br>Angle: {a:.1f}°"
                for d, p, a in zip(df['Distance'], df['Peak'], df['Angle'])
            ],
            hoverinfo="text"
        )

        fig = go.Figure(data=bars)

        fig.update_layout(
            title="Pipe Defects (Faster Interactive View)",
            xaxis_title="Defect Length (m)",
            yaxis_title="Orientation (°)",
            yaxis=dict(autorange='reversed', tickmode='linear', dtick=15),
            height=600,
            dragmode='pan'
        )

        st.plotly_chart(fig, use_container_width=True)


    except Exception as e:
        st.error(f"Error reading or processing file: {e}")
