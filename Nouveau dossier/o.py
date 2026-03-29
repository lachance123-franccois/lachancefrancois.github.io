import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import plotly.graph_objects as go
from PIL import Image
import io

st.set_page_config(page_title=“ToulouseML - Convolution Visualizer”, layout=“wide”, page_icon=“🧠”)

# Custom CSS

st.markdown(”””

<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        text-align: center;
        color: #666;
        margin-bottom: 2rem;
    }
    .formula-box {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
        margin: 1rem 0;
    }
    .footer {
        text-align: center;
        margin-top: 3rem;
        padding: 1rem;
        border-top: 1px solid #ddd;
        color: #666;
    }
</style>

“””, unsafe_allow_html=True)

st.markdown(’<div class="main-header">🧠 ToulouseML Toolkit</div>’, unsafe_allow_html=True)
st.markdown(’<div class="sub-header">Visualiseur de Convolution 2D - Comprendre step-by-step</div>’, unsafe_allow_html=True)

# Sidebar

with st.sidebar:
st.markdown(”### ⚙️ Configuration”)

```
mode = st.radio("Mode", ["Image Custom", "Matrice Simple", "Image Upload"])

st.markdown("---")
st.markdown("### 🎛️ Paramètres Kernel")

kernel_type = st.selectbox(
    "Type de kernel",
    ["Custom", "Edge Detection (Sobel X)", "Edge Detection (Sobel Y)", 
     "Blur (Moyenne)", "Sharpen", "Laplacian", "Gaussian Blur"]
)

kernel_size = st.slider("Taille du kernel", 3, 7, 3, step=2)

stride = st.slider("Stride", 1, 3, 1)
padding = st.slider("Padding", 0, 3, 0)

st.markdown("---")
animate = st.checkbox("Animation step-by-step", value=True)
if animate:
    step = st.slider("Étape", 0, 100, 0, help="Naviguer dans la convolution")
```

# Predefined kernels

def get_kernel(kernel_type, size):
if kernel_type == “Edge Detection (Sobel X)”:
return np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]], dtype=float)
elif kernel_type == “Edge Detection (Sobel Y)”:
return np.array([[-1, -2, -1], [0, 0, 0], [1, 2, 1]], dtype=float)
elif kernel_type == “Blur (Moyenne)”:
return np.ones((size, size), dtype=float) / (size * size)
elif kernel_type == “Sharpen”:
k = np.zeros((size, size))
k[size//2, size//2] = 2
k = k - np.ones((size, size)) / (size * size)
return k
elif kernel_type == “Laplacian”:
if size == 3:
return np.array([[0, 1, 0], [1, -4, 1], [0, 1, 0]], dtype=float)
else:
return np.array([[0, 0, 1, 0, 0], [0, 1, 2, 1, 0], [1, 2, -16, 2, 1],
[0, 1, 2, 1, 0], [0, 0, 1, 0, 0]], dtype=float)
elif kernel_type == “Gaussian Blur”:
if size == 3:
return np.array([[1, 2, 1], [2, 4, 2], [1, 2, 1]], dtype=float) / 16
elif size == 5:
return np.array([[1, 4, 6, 4, 1], [4, 16, 24, 16, 4], [6, 24, 36, 24, 6],
[4, 16, 24, 16, 4], [1, 4, 6, 4, 1]], dtype=float) / 256
else:  # Custom
return np.random.randn(size, size)

# Convolution function

def convolve2d(image, kernel, stride=1, padding=0):
“”“Convolution 2D from scratch avec tracking des positions”””
if len(image.shape) == 3:  # RGB to grayscale
image = np.mean(image, axis=2)

```
# Add padding
if padding > 0:
    image = np.pad(image, padding, mode='constant', constant_values=0)

img_h, img_w = image.shape
k_h, k_w = kernel.shape

# Output dimensions
out_h = (img_h - k_h) // stride + 1
out_w = (img_w - k_w) // stride + 1

output = np.zeros((out_h, out_w))
positions = []  # Store positions for visualization

for i in range(out_h):
    for j in range(out_w):
        y_start = i * stride
        x_start = j * stride
        
        region = image[y_start:y_start+k_h, x_start:x_start+k_w]
        output[i, j] = np.sum(region * kernel)
        
        positions.append({
            'out_pos': (i, j),
            'in_pos': (y_start, x_start),
            'region': region.copy(),
            'result': output[i, j]
        })

return output, positions, image
```

# Generate input based on mode

if mode == “Matrice Simple”:
input_size = st.sidebar.slider(“Taille de l’entrée”, 5, 12, 8)
input_matrix = np.random.randint(0, 10, (input_size, input_size)).astype(float)

elif mode == “Image Upload”:
uploaded_file = st.sidebar.file_uploader(“Choisir une image”, type=[‘png’, ‘jpg’, ‘jpeg’])
if uploaded_file:
img = Image.open(uploaded_file).convert(‘L’)
img = img.resize((128, 128))  # Resize for performance
input_matrix = np.array(img).astype(float) / 255.0
else:
# Default image
input_matrix = np.random.rand(8, 8)
else:  # Image Custom
input_matrix = np.array([
[0, 0, 0, 0, 0, 0, 0, 0],
[0, 1, 1, 1, 1, 1, 1, 0],
[0, 1, 0, 0, 0, 0, 1, 0],
[0, 1, 0, 1, 1, 0, 1, 0],
[0, 1, 0, 1, 1, 0, 1, 0],
[0, 1, 0, 0, 0, 0, 1, 0],
[0, 1, 1, 1, 1, 1, 1, 0],
[0, 0, 0, 0, 0, 0, 0, 0],
], dtype=float)

# Get kernel

kernel = get_kernel(kernel_type, kernel_size)

# Perform convolution

output, positions, padded_input = convolve2d(input_matrix, kernel, stride, padding)

# Display formulas

st.markdown(’<div class="formula-box">’, unsafe_allow_html=True)
st.markdown(”### 📐 Formules”)
col_f1, col_f2 = st.columns(2)
with col_f1:
st.latex(r”Output_{i,j} = \sum_{m=0}^{k_h-1} \sum_{n=0}^{k_w-1} Input_{i \cdot s + m, j \cdot s + n} \times Kernel_{m,n}”)
with col_f2:
out_h = (padded_input.shape[0] - kernel.shape[0]) // stride + 1
out_w = (padded_input.shape[1] - kernel.shape[1]) // stride + 1
st.latex(f”Output_Height = \frac{{{padded_input.shape[0]} - {kernel.shape[0]}}}{{{stride}}} + 1 = {out_h}”)
st.latex(f”Output_Width = \frac{{{padded_input.shape[1]} - {kernel.shape[1]}}}{{{stride}}} + 1 = {out_w}”)
st.markdown(’</div>’, unsafe_allow_html=True)

# Main visualization

col1, col2, col3 = st.columns([2, 1.5, 2])

# Calculate current step

current_step = step if animate else len(positions) - 1
current_step = min(current_step, len(positions) - 1)

with col1:
st.markdown(”### 🖼️ Input (avec padding)”)

```
fig, ax = plt.subplots(figsize=(6, 6))
im = ax.imshow(padded_input, cmap='gray', interpolation='nearest')

# Show grid
for i in range(padded_input.shape[0] + 1):
    ax.axhline(i - 0.5, color='white', linewidth=0.5, alpha=0.3)
for j in range(padded_input.shape[1] + 1):
    ax.axvline(j - 0.5, color='white', linewidth=0.5, alpha=0.3)

# Highlight current region
if animate and current_step < len(positions):
    pos = positions[current_step]
    y, x = pos['in_pos']
    rect = Rectangle((x - 0.5, y - 0.5), kernel.shape[1], kernel.shape[0], 
                     linewidth=3, edgecolor='red', facecolor='none')
    ax.add_patch(rect)

# Add values
for i in range(padded_input.shape[0]):
    for j in range(padded_input.shape[1]):
        ax.text(j, i, f'{padded_input[i, j]:.1f}', 
               ha='center', va='center', color='yellow', fontsize=8, weight='bold')

ax.set_xticks(range(padded_input.shape[1]))
ax.set_yticks(range(padded_input.shape[0]))
ax.set_title(f'Shape: {padded_input.shape}', fontsize=12, weight='bold')
plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
st.pyplot(fig)
plt.close()
```

with col2:
st.markdown(”### ⊗ Kernel”)

```
# Allow kernel editing if custom
if kernel_type == "Custom":
    st.markdown("**Éditer les valeurs:**")
    edited_kernel = kernel.copy()
    for i in range(kernel_size):
        cols = st.columns(kernel_size)
        for j in range(kernel_size):
            with cols[j]:
                edited_kernel[i, j] = st.number_input(
                    f"",
                    value=float(kernel[i, j]),
                    format="%.2f",
                    key=f"k_{i}_{j}",
                    label_visibility="collapsed"
                )
    kernel = edited_kernel

fig, ax = plt.subplots(figsize=(4, 4))
im = ax.imshow(kernel, cmap='RdBu', interpolation='nearest', vmin=-3, vmax=3)

for i in range(kernel.shape[0]):
    for j in range(kernel.shape[1]):
        ax.text(j, i, f'{kernel[i, j]:.2f}', 
               ha='center', va='center', color='black', fontsize=11, weight='bold')

ax.set_xticks(range(kernel.shape[1]))
ax.set_yticks(range(kernel.shape[0]))
ax.set_title(f'Shape: {kernel.shape}', fontsize=12, weight='bold')
plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
st.pyplot(fig)
plt.close()

st.markdown(f"**Stride:** {stride} | **Padding:** {padding}")
```

with col3:
st.markdown(”### 📊 Output”)

```
fig, ax = plt.subplots(figsize=(6, 6))
im = ax.imshow(output, cmap='viridis', interpolation='nearest')

# Show grid
for i in range(output.shape[0] + 1):
    ax.axhline(i - 0.5, color='white', linewidth=0.5, alpha=0.3)
for j in range(output.shape[1] + 1):
    ax.axvline(j - 0.5, color='white', linewidth=0.5, alpha=0.3)

# Highlight current position
if animate and current_step < len(positions):
    pos = positions[current_step]
    i, j = pos['out_pos']
    rect = Rectangle((j - 0.5, i - 0.5), 1, 1, 
                     linewidth=3, edgecolor='red', facecolor='none')
    ax.add_patch(rect)

# Add values
for i in range(output.shape[0]):
    for j in range(output.shape[1]):
        ax.text(j, i, f'{output[i, j]:.1f}', 
               ha='center', va='center', color='white', fontsize=8, weight='bold')

ax.set_xticks(range(output.shape[1]))
ax.set_yticks(range(output.shape[0]))
ax.set_title(f'Shape: {output.shape}', fontsize=12, weight='bold')
plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
st.pyplot(fig)
plt.close()
```

# Calculation details

if animate:
st.markdown(”—”)
st.markdown(”### 🔢 Calcul détaillé (étape courante)”)

```
if current_step < len(positions):
    pos = positions[current_step]
    
    col_calc1, col_calc2, col_calc3 = st.columns(3)
    
    with col_calc1:
        st.markdown("**Région extraite:**")
        st.code(str(pos['region']))
    
    with col_calc2:
        st.markdown("**Kernel:**")
        st.code(str(kernel))
    
    with col_calc3:
        st.markdown("**Calcul:**")
        calculation = ""
        for i in range(kernel.shape[0]):
            for j in range(kernel.shape[1]):
                calculation += f"({pos['region'][i, j]:.2f} × {kernel[i, j]:.2f}) + "
        calculation = calculation[:-3]  # Remove last " + "
        st.code(calculation + f"\n= {pos['result']:.2f}")
    
    st.info(f"📍 Position: Input[{pos['in_pos'][0]}:{pos['in_pos'][0]+kernel.shape[0]}, {pos['in_pos'][1]}:{pos['in_pos'][1]+kernel.shape[1]}] → Output[{pos['out_pos'][0]}, {pos['out_pos'][1]}]")
```

# Statistics

st.markdown(”—”)
st.markdown(”### 📈 Statistiques”)
col_stats1, col_stats2, col_stats3, col_stats4 = st.columns(4)

with col_stats1:
st.metric(“Input Size”, f”{input_matrix.shape[0]}×{input_matrix.shape[1]}”)
with col_stats2:
st.metric(“Output Size”, f”{output.shape[0]}×{output.shape[1]}”)
with col_stats3:
st.metric(“Réduction”, f”{100 * (1 - output.size/input_matrix.size):.1f}%”)
with col_stats4:
st.metric(“Opérations”, f”{len(positions) * kernel.size}”)

# Footer

st.markdown(”—”)
st.markdown( ”””

<div class="footer">
    <strong>🧠 ToulouseML Toolkit</strong> - Créé par <a href="https://votre-portfolio.com" target="_blank">Votre Nom</a><br>
    Master Signal, Image & Apprentissage Automatique - Université Toulouse III Paul Sabatier<br>
    📧 Contact | 💻 <a href="https://github.com/votre-github" target="_blank">GitHub</a> | 📚 <a href="https://votre-portfolio.com" target="_blank">Portfolio Complet</a>
</div>
""", unsafe_allow_html=True)