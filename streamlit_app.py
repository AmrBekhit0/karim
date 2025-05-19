# streamlit_app.py
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.lines import Line2D

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

        df = df[df['Distance'] >= user_min_dist]

        # Color mapping
        def color_map(peak):
            if peak < 0.3:
                return plt.cm.Blues(peak)
            elif 0.3 <= peak <= 0.5:
                return plt.cm.Oranges(peak)
            else:
                return plt.cm.Reds(min(peak, 1))

        # Plotting
        fig, ax = plt.subplots(figsize=(18, 8))
        for _, row in df.iterrows():
            x = row['Distance']
            width = row['Length']
            height = row['Angle Span']
            y = row['Angle'] - height / 2
            color = color_map(row['Peak'])

            rect = patches.Rectangle((x, y), width, height, facecolor=color, edgecolor=color, linewidth=1)
            ax.add_patch(rect)

        ax.set_xlabel('Absolute Distance (m)')
        ax.set_ylabel('Pipe Orientation (degrees)')
        ax.set_title('Pipe Defects Visualization by Rectangles')
        ax.set_yticks(np.arange(0, 361, 15))
        ax.invert_yaxis()
        ax.grid(True, linestyle='--', linewidth=0.5)
        ax.set_xlim(df['Distance'].min(), df['Distance'].max())
        ax.set_ylim(360, 0)

        # Legend
        legend_lines = [
            Line2D([0], [0], color=plt.cm.Blues(.7), lw=6),
            Line2D([0], [0], color=plt.cm.Oranges(.7), lw=6),
            Line2D([0], [0], color=plt.cm.Reds(.7), lw=6)
        ]
        ax.legend(legend_lines, ['< 0.3', '0.3–0.5', '> 0.5'], title='Peak Depth (normalized)')

        st.pyplot(fig)

    except Exception as e:
        st.error(f"Error reading or processing file: {e}")
