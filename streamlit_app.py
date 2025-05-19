pip install numpy==1.23.5
pip install --upgrade bokeh

import streamlit as st
import pandas as pd
import numpy as np
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource
import matplotlib.pyplot as plt


st.title("Pipe Defects Visualization (Bokeh)")
st.markdown("Upload an Excel file to visualize pipeline defects as colored rectangles with interaction.")

try:
    uploaded_file = st.file_uploader("Choose Excel file", type="xlsx")
except Exception as e:
    st.error(f"\U0001F6AB حدث خطأ أثناء قراءة الملف: {e}")

if uploaded_file is not None:
    try:
        df = pd.read_excel(uploaded_file, engine="openpyxl")

        # استخراج الأعمدة المهمة
        df['Distance'] = pd.to_numeric(df.iloc[:, 3], errors='coerce')
        df['Orientation'] = df.iloc[:, 9]
        df['Peak'] = pd.to_numeric(df.iloc[:, 5], errors='coerce')

        length_col = next((col for col in df.columns if 'Length' in col), None)
        width_col = next((col for col in df.columns if 'Width' in col), None)

        df['Length'] = pd.to_numeric(df[length_col], errors='coerce') / 1000
        df['Width'] = pd.to_numeric(df[width_col], errors='coerce') / 1000

        def time_to_deg(value):
            try:
                h, m = map(int, str(value).strip().split(":"))
                return (h % 12 + m / 60) * 30
            except:
                return np.nan

        df['Angle'] = df['Orientation'].apply(time_to_deg)
        df.dropna(subset=['Distance', 'Angle', 'Peak', 'Length', 'Width'], inplace=True)

        pipe_diam_m = 12 * 0.0254
        pipe_circum = np.pi * pipe_diam_m
        df['Angle Span'] = (df['Width'] / pipe_circum) * 360

        # Sliders for min and max distance
        min_dist = float(df['Distance'].min())
        max_dist = float(df['Distance'].max())

        user_min_dist = st.slider("Minimum Distance", min_value=min_dist, max_value=max_dist, value=min_dist)
        user_max_dist = st.slider("Maximum Distance", min_value=min_dist, max_value=max_dist, value=max_dist)

        df = df[(df['Distance'] >= user_min_dist) & (df['Distance'] <= user_max_dist)]

        # Prepare color mapping
        def color_map(peak):
            if peak < 0.3:
                return plt.cm.Blues(peak)
            elif 0.3 <= peak <= 0.5:
                return plt.cm.Oranges(peak)
            else:
                return plt.cm.Reds(min(peak, 1))

        colors = [f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}" 
                  for r, g, b, _ in [color_map(p) for p in df['Peak']]]

        df['y_center'] = df['Angle']
        df['x_center'] = df['Distance']

        source = ColumnDataSource(data=dict(
            x=df['x_center'],
            y=df['y_center'],
            width=df['Length'],
            height=df['Angle Span'],
            color=colors,
            peak=df['Peak'],
        ))

        p = figure(title="Pipe Defects (Interactive - Bokeh)",
                   x_axis_label="Distance (m)",
                   y_axis_label="Orientation (°)",
                   height=600,
                   tools="pan,wheel_zoom,box_zoom,reset,save")

        p.rect(x='x', y='y', width='width', height='height', 
               color='color', line_color=None, alpha=0.8, source=source)

        p.y_range.flipped = True

        st.bokeh_chart(p, use_container_width=True)

    except Exception as e:
        st.error(f"Error reading or processing file: {e}")
