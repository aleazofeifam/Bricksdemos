---
name: enterprise-branding-assets
description: >
  Gestiona activos de marca corporativa (logos, paleta de colores, CSS, tipografía, templates HTML)
  centralizados en un Volume de Unity Catalog para que Dashboards AI/BI, Databricks Apps, y
  reportes los referencien de forma estandarizada. Úsala cuando el usuario quiera "aplicar
  branding", "usar los colores corporativos", "agregar el logo de la empresa", "crear un
  dashboard con la identidad de marca", "estandarizar el look de la app", o "configurar
  el theme corporativo".
---

# Enterprise Branding Assets

Centraliza los activos visuales de la organización en un UC Volume para garantizar
consistencia en todos los productos de datos (dashboards, apps, reportes).

## Arquitectura de Branding Centralizado

```
/Volumes/{catalog}/{schema}/brand_assets/
├── logos/
│   ├── logo_primary.svg          # Logo principal (preferir SVG)
│   ├── logo_primary.png          # Fallback PNG (300px ancho)
│   ├── logo_white.svg            # Versión blanca para fondos oscuros
│   ├── logo_icon_only.svg        # Isotipo/favicon
│   └── logo_horizontal.svg       # Versión horizontal para headers
├── colors/
│   └── palette.json              # Paleta de colores oficial
├── fonts/
│   ├── primary_font.woff2        # Tipografía principal
│   └── secondary_font.woff2      # Tipografía secundaria
├── templates/
│   ├── app_header.html           # Header reutilizable para Apps
│   ├── app_footer.html           # Footer con disclaimer legal
│   ├── dashboard_theme.json      # Theme para AI/BI dashboards
│   └── email_template.html       # Template para reportes por email
└── css/
    ├── brand.css                 # CSS base con variables
    ├── streamlit_theme.css       # Override para Streamlit apps
    ├── dash_theme.css            # Override para Dash/Plotly apps
    └── gradio_theme.css          # Override para Gradio apps
```

## Paso 1: Crear el Volume de Branding

```sql
-- Crear schema dedicado para assets compartidos
CREATE SCHEMA IF NOT EXISTS {catalog}.shared_assets
  COMMENT 'Assets compartidos de la organización: branding, templates, configs';

-- Crear volume para branding
CREATE VOLUME IF NOT EXISTS {catalog}.shared_assets.brand_assets
  COMMENT 'Activos de marca corporativa: logos, colores, CSS, templates';
```

Permisos recomendados:
```sql
-- Todos pueden LEER, solo admins pueden ESCRIBIR
GRANT READ VOLUME ON VOLUME {catalog}.shared_assets.brand_assets TO `data_consumers`;
GRANT WRITE VOLUME ON VOLUME {catalog}.shared_assets.brand_assets TO `brand_admins`;
```

## Paso 2: Archivo de Paleta de Colores (palette.json)

Estructura estándar del archivo `/Volumes/{catalog}/shared_assets/brand_assets/colors/palette.json`:

```json
{
  "brand_name": "Acme Corp",
  "version": "2.0",
  "updated": "2025-01-15",
  "colors": {
    "primary": "#1B3A5C",
    "secondary": "#FF6B35",
    "accent": "#00B4D8",
    "success": "#2ECC71",
    "warning": "#F39C12",
    "error": "#E74C3C",
    "neutral_dark": "#2C3E50",
    "neutral_light": "#ECF0F1",
    "background": "#FFFFFF",
    "text_primary": "#2C3E50",
    "text_secondary": "#7F8C8D"
  },
  "chart_palette": [
    "#1B3A5C", "#FF6B35", "#00B4D8", "#2ECC71",
    "#9B59B6", "#F39C12", "#E74C3C", "#1ABC9C"
  ],
  "gradients": {
    "primary_to_secondary": ["#1B3A5C", "#FF6B35"],
    "cool": ["#1B3A5C", "#00B4D8"],
    "warm": ["#FF6B35", "#F39C12"]
  }
}
```

## Paso 3: Uso en AI/BI Dashboards

Al crear o editar dashboards, aplica los colores corporativos:

```python
# Leer paleta desde Volume
import json

palette_path = "/Volumes/{catalog}/shared_assets/brand_assets/colors/palette.json"
with open(palette_path) as f:
    brand = json.load(f)

# Usar en chart specifications (renderChartV2)
colors_map = {
    "Category A": brand["colors"]["primary"],
    "Category B": brand["colors"]["secondary"],
    "Category C": brand["colors"]["accent"]
}
```

Para `renderChartV2`, usa el campo `colors` en bar/line/pie charts:
```json
{
  "colors": {
    "Revenue": "#1B3A5C",
    "Costs": "#FF6B35",
    "Profit": "#2ECC71"
  }
}
```

**Regla para dashboards:** Siempre usa `chart_palette` del JSON para asignar colores
a series de datos. Nunca inventes colores ad-hoc.

## Paso 4: Uso en Databricks Apps

### Streamlit App
```python
import streamlit as st
import json

# Leer branding
with open("/Volumes/{catalog}/shared_assets/brand_assets/colors/palette.json") as f:
    brand = json.load(f)

# Configurar theme via .streamlit/config.toml generado dinámicamente
st.set_page_config(
    page_title="Mi App | Acme Corp",
    page_icon="/Volumes/{catalog}/shared_assets/brand_assets/logos/logo_icon_only.svg",
    layout="wide"
)

# Inyectar CSS corporativo
with open("/Volumes/{catalog}/shared_assets/brand_assets/css/streamlit_theme.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Header corporativo
with open("/Volumes/{catalog}/shared_assets/brand_assets/templates/app_header.html") as f:
    st.markdown(f.read(), unsafe_allow_html=True)
```

### Dash/Plotly App
```python
import dash
from dash import html, dcc
import json

with open("/Volumes/{catalog}/shared_assets/brand_assets/colors/palette.json") as f:
    brand = json.load(f)

app = dash.Dash(__name__)

# Plotly template con colores corporativos
import plotly.graph_objects as go
import plotly.io as pio

corporate_template = go.layout.Template(
    layout=go.Layout(
        colorway=brand["chart_palette"],
        font=dict(family="Inter, sans-serif", color=brand["colors"]["text_primary"]),
        paper_bgcolor=brand["colors"]["background"],
        plot_bgcolor=brand["colors"]["background"]
    )
)
pio.templates["corporate"] = corporate_template
pio.templates.default = "corporate"
```

### Gradio App
```python
import gradio as gr
import json

with open("/Volumes/{catalog}/shared_assets/brand_assets/colors/palette.json") as f:
    brand = json.load(f)

# Gradio theme personalizado
theme = gr.themes.Base(
    primary_hue=gr.themes.Color(brand["colors"]["primary"]),
    secondary_hue=gr.themes.Color(brand["colors"]["secondary"]),
    font=["Inter", "sans-serif"]
)

app = gr.Interface(..., theme=theme)
```

## Paso 5: CSS Base Corporativo (brand.css)

Contenido recomendado para `/Volumes/.../css/brand.css`:

```css
:root {
  /* Colores principales */
  --brand-primary: #1B3A5C;
  --brand-secondary: #FF6B35;
  --brand-accent: #00B4D8;
  --brand-success: #2ECC71;
  --brand-warning: #F39C12;
  --brand-error: #E74C3C;
  
  /* Tipografía */
  --font-primary: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  --font-mono: 'JetBrains Mono', 'Fira Code', monospace;
  
  /* Espaciado */
  --spacing-xs: 4px;
  --spacing-sm: 8px;
  --spacing-md: 16px;
  --spacing-lg: 24px;
  --spacing-xl: 32px;
  
  /* Bordes */
  --radius-sm: 4px;
  --radius-md: 8px;
  --radius-lg: 12px;
}

/* Header corporativo */
.brand-header {
  background: var(--brand-primary);
  padding: var(--spacing-md) var(--spacing-lg);
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

.brand-header img {
  height: 40px;
  width: auto;
}

.brand-header h1 {
  color: white;
  font-family: var(--font-primary);
  font-size: 1.25rem;
  font-weight: 600;
  margin: 0;
}

/* KPI Cards */
.brand-kpi-card {
  border: 1px solid #E5E7EB;
  border-radius: var(--radius-md);
  padding: var(--spacing-lg);
  background: white;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.brand-kpi-card .value {
  font-size: 2rem;
  font-weight: 700;
  color: var(--brand-primary);
}

.brand-kpi-card .label {
  font-size: 0.875rem;
  color: var(--brand-neutral-dark);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
```

## Paso 6: Template de Header HTML Reutilizable

`/Volumes/.../templates/app_header.html`:
```html
<div class="brand-header">
  <img src="/Volumes/{catalog}/shared_assets/brand_assets/logos/logo_white.svg" 
       alt="Company Logo" />
  <h1>{app_title}</h1>
  <div style="margin-left: auto; color: white; font-size: 0.8rem;">
    {environment} | {last_updated}
  </div>
</div>
```

## Flujo de Trabajo para el Agente

Cuando el usuario pida aplicar branding:

1. **Verificar existencia del Volume:**
   ```sql
   SHOW VOLUMES IN {catalog}.shared_assets LIKE 'brand_assets';
   ```
   Si no existe, guía la creación (Paso 1).

2. **Verificar palette.json:**
   Intenta leer el archivo. Si no existe, pregunta al usuario los colores
   corporativos y créalo.

3. **Aplicar según contexto:**
   - Si es Dashboard → usa `chart_palette` en `renderChartV2` colors
   - Si es Databricks App → inyecta CSS + header + logo
   - Si es reporte → usa email template

4. **Preguntas si no hay palette.json:**
   ```
   No encontré activos de marca configurados. Necesito:
   1. ¿Color primario de la marca? (hex, ej: #1B3A5C)
   2. ¿Color secundario? (hex)
   3. ¿Tienen logo en SVG o PNG? (¿dónde está?)
   4. ¿Tipografía corporativa? (ej: Inter, Roboto, Arial)
   5. ¿Catálogo/schema donde guardar los assets?
   ```

## Gotchas

* **Volumes en Apps:** Las Apps acceden a Volumes via filesystem (`/Volumes/...`), no URLs
* **SVG vs PNG:** Preferir SVG para logos (escala sin pixelar). PNG solo como fallback
* **Permisos:** El service principal de la App necesita `READ VOLUME` en el brand volume
* **Cache:** Las Apps cachean archivos estáticos. Si actualizas el logo, haz redeploy
* **Dashboards AI/BI:** No soportan CSS custom ni logos incrustados directamente — usa los colores en `colors` map de los charts y counters
* **Consistencia:** NUNCA uses colores hardcoded. Siempre lee de `palette.json`
* **Dark mode:** Si la org tiene dark mode, agrega un campo `colors_dark` en palette.json
* **Versionado:** El campo `version` en palette.json permite tracking de cambios de marca
