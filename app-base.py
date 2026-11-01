import streamlit as st
import pandas as pd
import numpy as np
import base64
from pathlib import Path
import streamlit.components.v1 as components
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from statsmodels.tsa.holtwinters import ExponentialSmoothing

import warnings
warnings.filterwarnings("ignore")

# --- CONFIGURACIÓN DE PÁGINA (ÚNICA) ---
st.set_page_config(page_title="Terminal Residual Analysis", layout="wide", page_icon=":material/analytics:")

# --- CABECERA Y ANIMACIONES DE APP.PY ---
col_izq, col_central, col_der = st.columns([1, 10, 1])

with col_central:    
    st.subheader(":material/terminal: Terminal Residual Analysis", anchor=False, text_alignment="center")
    st.markdown(r"""
        <style>
        .stAlert > div {
            text-align: center;
            display: flex;
            justify-content: center;
        }
        </style>
    """, unsafe_allow_html=True)

# Carga de HTMLs / Animaciones
def get_html_data_url(file_path):
    try:
        content = Path(file_path).read_text(encoding="utf-8")
        b64 = base64.b64encode(content.encode()).decode()
        return f"data:text/html;base64,{b64}"
    except:
        return ""

opcion1_html = get_html_data_url("static/index2.html")
opcion2_html = get_html_data_url("static/texto-2.html")

col_izq, col_central, col_der = st.columns([1, 10, 1])
with col_central:
    v1, v2 = st.columns(2)
    with v1:        
        if opcion1_html:
            st.iframe(opcion1_html, height=320)
    with v2:
        if opcion2_html:
            st.iframe(opcion2_html, height=320)
    st.write("") 

st.markdown("---")

# ==============================================================================
# --- BARRA LATERAL (SIDEBAR): CARGA DE DATOS Y CONFIGURACIÓN ÚNICA ---
# ==============================================================================
st.sidebar.title(":material/dashboard: Panel de Control Global")

# ------------------------------------------------------------------------------
# SECCIÓN 1: DÓLAR / IPC (DATOS Y CONFIGURACIÓN UNIFICADA)
# ------------------------------------------------------------------------------
st.sidebar.markdown(r"### :material/finance_mode: Módulo Dólar / IPC")
uploaded_dolar = st.sidebar.file_uploader("Subir 'dolar-ipc.xlsx'", type=["xlsx"], key="up_dolar")

if uploaded_dolar is not None:
    df_dolar_base = pd.read_excel(uploaded_dolar, sheet_name="data")
else:
    try:
        df_dolar_base = pd.read_excel("data/dolar-ipc.xlsx", sheet_name="data")
    except:
        df_dolar_base = None

if df_dolar_base is not None:
    df_dolar = df_dolar_base.copy()
    df_dolar['fecha'] = pd.to_datetime(df_dolar['fecha'])
    df_dolar = df_dolar.sort_values('fecha').set_index('fecha')

    var_dolar = st.sidebar.selectbox(
        "Variable Macroeconómica", 
        [col for col in df_dolar.columns if col != 'fecha'],
        key="var_dolar"
    )
    seas_dolar = st.sidebar.slider("Periodos Estacionalidad (Dólar/IPC)", min_value=2, max_value=24, value=12, key="seas_dolar")
    trend_dolar = st.sidebar.selectbox("Tendencia (Dólar/IPC)", ["add", "mul", None], index=0, key="trend_dolar")
    stype_dolar = st.sidebar.selectbox("Estacionalidad (Dólar/IPC)", ["add", "mul", None], index=0, key="stype_dolar")

st.sidebar.markdown("---")

# ------------------------------------------------------------------------------
# SECCIÓN 2: VENTAS TECH (DATOS Y CONFIGURACIÓN UNIFICADA)
# ------------------------------------------------------------------------------
st.sidebar.markdown(r"### :material/finance_mode: Módulo Ventas Tech")
uploaded_tech = st.sidebar.file_uploader("Subir 'db-datos.xlsx'", type=["xlsx"], key="up_tech")

if uploaded_tech is not None:
    df_tech_base = pd.read_excel(uploaded_tech, sheet_name="Hoja1")
else:
    try:
        df_tech_base = pd.read_excel("data/db-datos-2.xlsx", sheet_name="Hoja1")
    except:
        try:
            df_tech_base = pd.read_excel("db-datos.xlsx", sheet_name="Hoja1")
        except:
            df_tech_base = None

if df_tech_base is not None:
    df_tech = df_tech_base.copy()
    df_tech['fecha'] = pd.to_datetime(df_tech['fecha'])

    paises_tech = sorted(df_tech['pais'].unique().tolist())
    pais_tech = st.sidebar.selectbox("Selecciona el País", paises_tech, key="pais_tech")

    categorias_tech = sorted(df_tech['categoria'].unique().tolist())
    cat_tech = st.sidebar.selectbox("Selecciona la Categoría", categorias_tech, key="cat_tech")

    metrica_tech = st.sidebar.selectbox(
        "Métrica Financiera", 
        ["total", "cantidad", "utilidad"], 
        format_func=lambda x: {"total": "Ventas Totales ($)", "cantidad": "Cantidad Vendida", "utilidad": "Utilidad / Beneficio ($)"}[x],
        key="metrica_tech"
    )

    df_filtered_tech = df_tech[(df_tech['pais'] == pais_tech) & (df_tech['categoria'] == cat_tech)].copy()
    if not df_filtered_tech.empty:
        df_filtered_tech['periodo'] = df_filtered_tech['fecha'].dt.to_period('M').dt.to_timestamp()
        ts_df_tech = df_filtered_tech.groupby('periodo')[metrica_tech].sum().sort_index()
    else:
        ts_df_tech = None

    seas_tech = st.sidebar.slider(
        "Periodos Estacionalidad (Ventas Tech)", 
        min_value=2, max_value=12, 
        value=min(6, len(ts_df_tech)//2 if (ts_df_tech is not None and len(ts_df_tech)>=4) else 2),
        key="seas_tech"
    )
    trend_tech = st.sidebar.selectbox("Tendencia (Ventas Tech)", ["add", "mul", None], index=0, key="trend_tech")
    stype_tech = st.sidebar.selectbox("Estacionalidad (Ventas Tech)", ["add", "mul", None], index=2, key="stype_tech")

# ==============================================================================
# --- RENDERING DE CONTENIDOS EN PESTAÑAS (st.tabs) ---
# ==============================================================================
tab1, tab2, tab3, tab4 = st.tabs([
    ":material/browse_activity: Dólar e IPC (Avanzado)", 
    ":material/browse_activity: Dólar e IPC (Estándar)", 
    ":material/browse_activity: Ventas Tech (Avanzado)", 
    ":material/browse_activity: Ventas Tech (Estándar)"
])

# ------------------------------------------------------------------------------
# TAB 1: DÓLAR E IPC - AVANZADO (PLOTLY + ANOMALÍAS)
# ------------------------------------------------------------------------------
with tab1:
    st.subheader(":material/monitoring: Análisis de Residuales: Tipo de Cambio e Inflación Regional (IPC)")
    st.markdown(r"""
    Herramienta financiera avanzada para evaluar si las variables macroeconómicas presentan patrones predecibles 
    o si sus fluctuaciones responden a componentes aleatorios, con detección de anomalías y métricas de precisión.
    """)
    
    if df_dolar_base is None:
        st.warning(":material/warning: Por favor sube el archivo 'dolar-ipc.xlsx' en la barra lateral o colócalo en el directorio de trabajo.")
    else:
        ts_data1 = df_dolar[var_dolar].dropna()

        try:
            model1 = ExponentialSmoothing(
                ts_data1, 
                trend=trend_dolar, 
                seasonal=stype_dolar, 
                seasonal_periods=seas_dolar
            ).fit()
            
            fitted_values1 = model1.fittedvalues
            residuals1 = ts_data1 - fitted_values1
            
            rmse1 = np.sqrt(np.mean(residuals1**2))
            mae1 = np.mean(np.abs(residuals1))
            with np.errstate(divide='ignore', invalid='ignore'):
                mape1 = np.mean(np.abs(residuals1 / ts_data1)) * 100

            mean_res1 = residuals1.mean()
            std_res1 = residuals1.std()
            upper_band1 = mean_res1 + (2 * std_res1)
            lower_band1 = mean_res1 - (2 * std_res1)
            outliers1 = residuals1[(residuals1 > upper_band1) | (residuals1 < lower_band1)]

            st.markdown("---")
            st.subheader(":material/insert_chart: Métricas de Desempeño y Error del Modelo")
            col1, col2, col3, col4, col5 = st.columns(5)
            col1.metric("Media Residuales", f"{mean_res1:.4f}", help="Idealmente cercano a 0")
            col2.metric(r"Desv. Estándar ($\sigma$)", f"{std_res1:.4f}")
            col3.metric("RMSE", f"{rmse1:.4f}", help="Raíz del Error Cuadrático Medio")
            col4.metric("MAE", f"{mae1:.4f}", help="Error Absoluto Medio")
            col5.metric(r"Anomalías Detectadas", f"{len(outliers1)} periodos", help=r"Fuera de $\pm 2\sigma$")
            
            st.markdown("---")
            st.subheader(f":material/insert_chart: Evolución y Residuales con Bandas de Control para: {var_dolar}")
            
            fig1 = make_subplots(
                rows=2, cols=1, 
                shared_xaxes=True, 
                vertical_spacing=0.12,
                subplot_titles=(
                    f"Serie Histórica vs. Predicción del Modelo ({var_dolar})", 
                    r"Serie de Residuales con Bandas de Control ($\pm 2\sigma$)"
                )
            )
            
            fig1.add_trace(go.Scatter(x=ts_data1.index, y=ts_data1, mode='lines+markers', name="Valor Real (Yt)", line=dict(color="#1f77b4", width=2)), row=1, col=1)
            fig1.add_trace(go.Scatter(x=fitted_values1.index, y=fitted_values1, mode='lines', name="Modelo Ajustado (Ŷt)", line=dict(color="#ff7f0e", width=2, dash="dash")), row=1, col=1)
            fig1.add_trace(go.Scatter(x=residuals1.index, y=residuals1, mode='lines+markers', name="Residuales (Rt)", line=dict(color="#9467bd", width=1.5)), row=2, col=1)
            fig1.add_hline(y=upper_band1, line_dash="dash", line_color="orange", annotation_text="+2σ (Límite Superior)", row=2, col=1)
            fig1.add_hline(y=lower_band1, line_dash="dash", line_color="orange", annotation_text="-2σ (Límite Inferior)", row=2, col=1)
            fig1.add_hline(y=0, line_dash="dot", line_color="red", annotation_text="Cero (Ideal)", row=2, col=1)
            
            if not outliers1.empty:
                fig1.add_trace(go.Scatter(x=outliers1.index, y=outliers1, mode='markers', name="Anomalías / Outliers", marker=dict(color="red", size=10, symbol="x")), row=2, col=1)

            fig1.update_layout(height=700, template="plotly_white", hovermode="x unified", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
            fig1.update_xaxes(title_text="Fecha", row=2, col=1)
            fig1.update_yaxes(title_text="Variación (%)", row=1, col=1)
            fig1.update_yaxes(title_text="Residual", row=2, col=1)
            
            st.plotly_chart(fig1, width='stretch')
            
            df_export1 = pd.DataFrame({
                'Fecha': ts_data1.index,
                'Valor_Real': ts_data1,
                'Prediccion_Modelo': fitted_values1,
                'Residual': residuals1,
                'Es_Anomalia': (residuals1 > upper_band1) | (residuals1 < lower_band1)
            })
            st.download_button(
                label=":material/download: Descargar Reporte CSV (Dólar/IPC)",
                data=df_export1.to_csv(index=False).encode('utf-8'),
                file_name=f"residuales_{var_dolar.replace(' ', '_')}.csv",
                mime="text/csv",
                key="dl_tab1"
            )

            st.markdown(r"""
            ###  Guía Gerencial de Anomalías y Proyecciones
            * **Anomalías fuera de $\pm 2\sigma$:** Puntos marcados con 'X' roja indican shocks extraordinarios que escapan a la inercia normal del modelo.
            * **Proyección Futura:** Métricas de error como RMSE/MAE bajas otorgan validez estadística para proyectar la tendencia con confianza.
            """)
        except Exception as e:
            st.error(f"Error al ajustar el modelo: {e}")

# ------------------------------------------------------------------------------
# TAB 2: DÓLAR E IPC - ESTÁNDAR (PLOTLY INTERACTIVO)
# ------------------------------------------------------------------------------
with tab2:
    st.subheader("Análisis de Residuales: Tipo de Cambio e Inflación Regional (IPC)")
    st.markdown(r"""
    Herramienta financiera para evaluar si las variables macroeconómicas (**Dólar** y **Variaciones de Precios por Regiones**) 
    presentan patrones predecibles o si sus fluctuaciones responden a un componente puramente aleatorio.
    """)
    
    if df_dolar_base is None:
        st.warning("Por favor sube el archivo 'dolar-ipc.xlsx' en la barra lateral o colócalo en el directorio de trabajo.")
    else:
        ts_data2 = df_dolar[var_dolar].dropna()

        try:
            model2 = ExponentialSmoothing(
                ts_data2, 
                trend=trend_dolar, 
                seasonal=stype_dolar, 
                seasonal_periods=seas_dolar
            ).fit()
            
            fitted_values2 = model2.fittedvalues
            residuals2 = ts_data2 - fitted_values2
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Media de Residuales", f"{residuals2.mean():.4f}", help="Idealmente cercano a 0 (sin sesgo)")
            col2.metric("Desviación Estándar", f"{residuals2.std():.4f}")
            col3.metric("Último Registro", f"{ts_data2.iloc[-1]:.2f}%")
            
            st.markdown("---")
            st.subheader(f"Evolución y Residuales para: {var_dolar}")
            
            fig2 = make_subplots(
                rows=2, cols=1, 
                shared_xaxes=True, 
                vertical_spacing=0.12,
                subplot_titles=(
                    r"Serie Histórica vs. Predicción del Modelo ($\hat{Y}_t$)", 
                    r"Serie de Residuales ($R_t = Y_t - \hat{Y}_t$)"
                )
            )
            
            fig2.add_trace(go.Scatter(x=ts_data2.index, y=ts_data2, mode='lines+markers', name=r"Valor Real ($Y_t$)", line=dict(color="#1f77b4", width=2)), row=1, col=1)
            fig2.add_trace(go.Scatter(x=fitted_values2.index, y=fitted_values2, mode='lines', name=r"Modelo Ajustado ($\hat{Y}_t$)", line=dict(color="#ff7f0e", width=2, dash="dash")), row=1, col=1)
            fig2.add_trace(go.Scatter(x=residuals2.index, y=residuals2, mode='lines+markers', name=r"Residuales ($R_t$)", line=dict(color="#9467bd", width=1.5)), row=2, col=1)
            fig2.add_hline(y=0, line_dash="dot", line_color="red", annotation_text="Línea Cero (Ideal)", row=2, col=1)

            fig2.update_layout(height=700, template="plotly_white", hovermode="x unified", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
            fig2.update_xaxes(title_text="Fecha", row=2, col=1)
            fig2.update_yaxes(title_text="Variación (%)", row=1, col=1)
            fig2.update_yaxes(title_text="Residual", row=2, col=1)
            
            st.plotly_chart(fig2, width='stretch')
            
            st.markdown(r"""
            ### Guía de Interpretación para Análisis Macroeconómico
            * **Media cercana a cero:** Confirma que el modelo no sobreestima ni subestima sistemáticamente la variable.
            * **Ruido Blanco:** Si los residuales no muestran patrones cíclicos evidentes, el modelo ha capturado correctamente la dinámica estacional.
            """)
        except Exception as e:
            st.error(f"Error al ajustar el modelo: {e}")

# ------------------------------------------------------------------------------
# TAB 3: VENTAS TECH - AVANZADO (PLOTLY + ANOMALÍAS)
# ------------------------------------------------------------------------------
with tab3:
    st.subheader(":material/monitoring: Análisis de Residuales en Ventas de Tecnología por País y Categoría")
    st.markdown(r"""
    Herramienta comercial avanzada para evaluar rendimiento histórico, detectar quiebres o campañas atípicas mediante **bandas de control**, 
    calcular **métricas de error (RMSE, MAPE)** y exportar reportes ejecutivos.
    """)
    
    if df_tech_base is None:
        st.warning(":material/warning: Por favor sube el archivo 'db-datos.xlsx' en la barra lateral.")
    elif ts_df_tech is None:
        st.warning("No se encontraron registros para la combinación seleccionada de País y Categoría.")
    else:
        col_k1, col_k2, col_k3 = st.columns(3)
        col_k1.metric("Ventas Totales (Filtro)", f"${df_filtered_tech['total'].sum():,.2f}")
        col_k2.metric("Utilidad Acumulada", f"${df_filtered_tech['utilidad'].sum():,.2f}")
        col_k3.metric("Unidades Vendidas", f"{df_filtered_tech['cantidad'].sum():,}")

        st.markdown("---")

        if len(ts_df_tech) < 4:
            st.warning("La serie temporal agregada tiene pocos puntos de datos para generar modelos estacionales.")
        else:
            try:
                model3 = ExponentialSmoothing(
                    ts_df_tech, 
                    trend=trend_tech, 
                    seasonal=stype_tech, 
                    seasonal_periods=seas_tech if seas_tech < len(ts_df_tech) else None
                ).fit()
                
                fitted_values3 = model3.fittedvalues
                residuals3 = ts_df_tech - fitted_values3
                
                rmse3 = np.sqrt(np.mean(residuals3**2))
                mae3 = np.mean(np.abs(residuals3))
                with np.errstate(divide='ignore', invalid='ignore'):
                    mape3 = np.mean(np.abs(residuals3 / ts_df_tech)) * 100
                mape_str3 = f"{mape3:.2f}%" if not np.isnan(mape3) and np.isfinite(mape3) else "N/A"

                mean_res3 = residuals3.mean()
                std_res3 = residuals3.std()
                upper_band3 = mean_res3 + (2 * std_res3)
                lower_band3 = mean_res3 - (2 * std_res3)
                outliers3 = residuals3[(residuals3 > upper_band3) | (residuals3 < lower_band3)]

                st.subheader(f":material/insert_chart: Desempeño del Modelo para {cat_tech} en {pais_tech} ({metrica_tech.upper()})")
                col_m1, col_m2, col_m3, col_m4, col_m5 = st.columns(5)
                col_m1.metric("Media Residuales", f"{mean_res3:,.2f}")
                col_m2.metric(r"Desv. Estándar ($\sigma$)", f"{std_res3:,.2f}")
                col_m3.metric("RMSE", f"{rmse3:,.2f}")
                col_m4.metric("MAPE", mape_str3, help="Error Porcentual Absoluto Medio")
                col_m5.metric("Meses Atípicos", f"{len(outliers3)} detectados")
                
                fig3 = make_subplots(
                    rows=2, cols=1, 
                    shared_xaxes=True, 
                    vertical_spacing=0.12,
                    subplot_titles=(
                        f"Rendimiento Comercial vs. Pronóstico ({metrica_tech.capitalize()})", 
                        r"Serie de Residuales con Bandas de Control de Outliers ($\pm 2\sigma$)"
                    )
                )
                
                fig3.add_trace(go.Scatter(x=ts_df_tech.index, y=ts_df_tech, mode='lines+markers', name=f"Real ({metrica_tech})", line=dict(color="#2ca02c", width=2)), row=1, col=1)
                fig3.add_trace(go.Scatter(x=fitted_values3.index, y=fitted_values3, mode='lines+markers', name="Predicción (Ŷt)", line=dict(color="#ff7f0e", width=2, dash="dash"), marker=dict(symbol="x")), row=1, col=1)
                fig3.add_trace(go.Scatter(x=residuals3.index, y=residuals3, mode='lines+markers', name="Residuales (Rt)", line=dict(color="#d62728", width=1.5), marker=dict(symbol="square")), row=2, col=1)
                fig3.add_hline(y=upper_band3, line_dash="dash", line_color="orange", annotation_text="+2σ (Éxito Atípico)", row=2, col=1)
                fig3.add_hline(y=lower_band3, line_dash="dash", line_color="orange", annotation_text="-2σ (Alerta Quiebre)", row=2, col=1)
                fig3.add_hline(y=0, line_dash="dot", line_color="black", annotation_text="Cero (Ideal)", row=2, col=1)
                
                if not outliers3.empty:
                    fig3.add_trace(go.Scatter(x=outliers3.index, y=outliers3, mode='markers', name="Meses Atípicos", marker=dict(color="purple", size=12, symbol="star")), row=2, col=1)

                fig3.update_layout(height=700, template="plotly_white", hovermode="x unified", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
                fig3.update_xaxes(title_text="Periodo Mensual", row=2, col=1)
                fig3.update_yaxes(title_text=metrica_tech.capitalize(), row=1, col=1)
                fig3.update_yaxes(title_text="Residual", row=2, col=1)
                
                st.plotly_chart(fig3, width='stretch')
                
                df_export3 = pd.DataFrame({
                    'Periodo': ts_df_tech.index,
                    'Valor_Real': ts_df_tech,
                    'Prediccion_Modelo': fitted_values3,
                    'Residual': residuals3,
                    'Es_Anomalia_Comercial': (residuals3 > upper_band3) | (residuals3 < lower_band3)
                })
                st.download_button(
                    label=":material/download: Descargar Reporte CSV (Ventas Tech)",
                    data=df_export3.to_csv(index=False).encode('utf-8'),
                    file_name=f"ventas_residuales_{pais_tech}_{cat_tech}_{metrica_tech}.csv",
                    mime="text/csv",
                    key="dl_tab3"
                )
                
                st.markdown(r"""
                ### Conclusiones Gerenciales:
                * **Identificación de Éxitos o Crisis:** Los meses fuera de las bandas $\pm 2\sigma$ señalan eventos comerciales inusuales.
                * **Confiabilidad del Pronóstico:** El análisis de errores permite presupuestar compras con certidumbre cuantificable.
                """)
            except Exception as e:
                st.error(f"Error al ajustar el modelo: {e}")

# ------------------------------------------------------------------------------
# TAB 4: VENTAS TECH - ESTÁNDAR
# ------------------------------------------------------------------------------
with tab4:
    st.subheader(":material/monitoring: Análisis de Residuales en Ventas de Tecnología por País y Categoría")
    st.markdown(r"""
    Herramienta de inteligencia comercial para analizar el rendimiento histórico de ventas de tecnología segmentado por **País** y **Categoría**, 
    evaluando la **Cantidad de productos vendidos**, las **Ventas Totales ($)** y la **Utilidad ($)** mediante modelos de pronóstico y análisis de residuales.
    """)
    
    if df_tech_base is None:
        st.warning(":material/warning: Por favor sube el archivo 'db-datos.xlsx' en la barra lateral.")
    elif ts_df_tech is None:
        st.warning("No se encontraron registros para la combinación seleccionada de País y Categoría.")
    else:
        col_k1, col_k2, col_k3 = st.columns(3)
        col_k1.metric("Ventas Totales (País/Cat)", f"${df_filtered_tech['total'].sum():,.2f}")
        col_k2.metric("Utilidad Acumulada", f"${df_filtered_tech['utilidad'].sum():,.2f}")
        col_k3.metric("Unidades Vendidas", f"{df_filtered_tech['cantidad'].sum():,}")

        st.markdown("---")

        if len(ts_df_tech) < 4:
            st.warning("La serie temporal agregada tiene pocos puntos de datos.")
        else:
            try:
                model4 = ExponentialSmoothing(
                    ts_df_tech, 
                    trend=trend_tech, 
                    seasonal=stype_tech, 
                    seasonal_periods=seas_tech if seas_tech < len(ts_df_tech) else None
                ).fit()
                
                fitted_values4 = model4.fittedvalues
                residuals4 = ts_df_tech - fitted_values4
                
                st.subheader(f"Análisis para {cat_tech} en {pais_tech} — Métrica: {metrica_tech.upper()}")
                
                col_m1, col_m2 = st.columns(2)
                col_m1.metric("Media de Residuales ($R_t$)", f"{residuals4.mean():.2f}")
                col_m2.metric("Desviación Estándar de Residuales", f"{residuals4.std():.2f}")
                
                fig4 = make_subplots(
                    rows=2, cols=1, 
                    shared_xaxes=True, 
                    vertical_spacing=0.12,
                    subplot_titles=(
                        f"Rendimiento Comercial vs. Modelo de Pronóstico ({metrica_tech.capitalize()})", 
                        "Serie de Residuales (Variaciones no explicadas)"
                    )
                )
                
                fig4.add_trace(go.Scatter(x=ts_df_tech.index, y=ts_df_tech, mode='lines+markers', name=f"Real ({metrica_tech})", line=dict(color="#2ca02c", width=2)), row=1, col=1)
                fig4.add_trace(go.Scatter(x=fitted_values4.index, y=fitted_values4, mode='lines+markers', name="Predicción (Ŷt)", line=dict(color="#ff7f0e", width=2, dash="dash"), marker=dict(symbol="x")), row=1, col=1)
                fig4.add_trace(go.Scatter(x=residuals4.index, y=residuals4, mode='lines+markers', name="Residuales (Rt)", line=dict(color="#d62728", width=1.5), marker=dict(symbol="square")), row=2, col=1)
                fig4.add_hline(y=0, line_dash="dot", line_color="black", annotation_text="Cero (Ideal)", row=2, col=1)
                
                fig4.update_layout(height=700, template="plotly_white", hovermode="x unified", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
                fig4.update_xaxes(title_text="Periodo", row=2, col=1)
                fig4.update_yaxes(title_text=metrica_tech.capitalize(), row=1, col=1)
                fig4.update_yaxes(title_text="Residual", row=2, col=1)
                
                st.plotly_chart(fig4, width='stretch')
                
                st.markdown(r"""
                ### Conclusiones Gerenciales:
                * **Evaluación de Desviaciones:** Los picos en la gráfica de residuales permiten identificar meses con anomalías comerciales.
                * **Robustez del Modelo:** Una media de residuales cercana a cero valida que el modelo de ventas es insesgado.
                """)
            except Exception as e:
                st.error(f"Error al ajustar el modelo: {e}")