import streamlit as st
import pandas as pd
import numpy as np
import base64
from pathlib import Path
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from statsmodels.tsa.seasonal import STL
from statsmodels.stats.diagnostic import acorr_ljungbox
from statsmodels.stats.stattools import jarque_bera
from statsmodels.tsa.statespace.sarimax import SARIMAX

import warnings
warnings.filterwarnings("ignore")

# --- CONFIGURACIÓN DE PÁGINA (ÚNICA) ---
st.set_page_config(page_title="Advanced Financial & Residual Terminal", layout="wide", page_icon=":material/analytics:")

# --- CABECERA Y ESTILOS ---
col_izq, col_central, col_der = st.columns([1, 10, 1])

with col_central:    
    st.subheader(":material/terminal: Terminal Avanzada de Análisis Econométrico y Residuales", anchor=False, text_alignment="center")
    st.markdown(r"""
        <style>
        .stAlert > div {
            text-align: center;
            display: flex;
            justify-content: center;
        }
        </style>
    """, unsafe_allow_html=True)

# Carga de HTMLs / Animaciones de apoyo si existen
def get_html_data_url(file_path):
    try:
        content = Path(file_path).read_text(encoding="utf-8")
        b64 = base64.b64encode(content.encode()).decode()
        return f"data:text/html;base64,{b64}"
    except:
        return ""

opcion1_html = get_html_data_url("static/index2.html")
opcion2_html = get_html_data_url("static/texto-2.html")

if opcion1_html or opcion2_html:
    col_izq, col_central, col_der = st.columns([1, 10, 1])
    with col_central:
        v1, v2 = st.columns(2)
        with v1:        
            if opcion1_html:
                st.iframe(opcion1_html, height=280)
        with v2:
            if opcion2_html:
                st.iframe(opcion2_html, height=280)
        st.write("") 

st.markdown("---")

# ==============================================================================
# --- FUNCIONES CACHEADAS PARA OPTIMIZACIÓN DE RENDIMIENTO ---
# ==============================================================================
@st.cache_data
def cargar_excel_dolar(file_or_path):
    if file_or_path is not None:
        df = pd.read_excel(file_or_path, sheet_name="data")
    else:
        df = pd.read_excel("data/dolar-ipc.xlsx", sheet_name="data")
    df['fecha'] = pd.to_datetime(df['fecha'])
    return df.sort_values('fecha').set_index('fecha')

@st.cache_data
def cargar_excel_tech(file_or_path):
    if file_or_path is not None:
        df = pd.read_excel(file_or_path, sheet_name="Hoja1")
    else:
        try:
            df = pd.read_excel("data/db-datos-2.xlsx", sheet_name="Hoja1")
        except:
            df = pd.read_excel("db-datos.xlsx", sheet_name="Hoja1")
    df['fecha'] = pd.to_datetime(df['fecha'])
    return df

# ==============================================================================
# --- BARRA LATERAL (SIDEBAR): PANEL DE CONTROL GLOBAL ---
# ==============================================================================
st.sidebar.title(":material/dashboard: Panel de Control Global")

# ------------------------------------------------------------------------------
# SECCIÓN 1: DÓLAR / IPC
# ------------------------------------------------------------------------------
st.sidebar.markdown(r"### :material/finance_mode: Módulo Dólar / IPC")
uploaded_dolar = st.sidebar.file_uploader("Subir 'dolar-ipc.xlsx'", type=["xlsx"], key="up_dolar")

try:
    df_dolar = cargar_excel_dolar(uploaded_dolar)
    var_dolar = st.sidebar.selectbox(
        "Variable Macroeconómica", 
        [col for col in df_dolar.columns if col != 'fecha'],
        key="var_dolar"
    )
    seas_dolar = st.sidebar.slider("Periodos Estacionalidad (Dólar/IPC)", min_value=2, max_value=24, value=12, key="seas_dolar")
    trend_dolar = st.sidebar.selectbox("Tendencia (Dólar/IPC)", ["add", "mul", None], index=0, key="trend_dolar")
    stype_dolar = st.sidebar.selectbox("Estacionalidad (Dólar/IPC)", ["add", "mul", None], index=0, key="stype_dolar")
except Exception as e:
    df_dolar = None

st.sidebar.markdown("---")

# ------------------------------------------------------------------------------
# SECCIÓN 2: VENTAS TECH
# ------------------------------------------------------------------------------
st.sidebar.markdown(r"### :material/store: Módulo Ventas Tech")
uploaded_tech = st.sidebar.file_uploader("Subir 'db-datos.xlsx'", type=["xlsx"], key="up_tech")

try:
    df_tech = cargar_excel_tech(uploaded_tech)
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
        ts_df_tech = ts_df_tech.resample('MS').sum().fillna(0)
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
except Exception as e:
    df_tech = None
    ts_df_tech = None

st.sidebar.markdown("---")
st.sidebar.markdown(r"### :material/settings: Parámetros de Pronóstico y Diagnóstico")
horizonte_pronostico = st.sidebar.slider("Horizonte Futuro (Meses)", min_value=1, max_value=24, value=6, key="horiz")

# ==============================================================================
# --- RENDERIZADO EN PESTAÑAS (st.tabs) ---
# ==============================================================================
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    ":material/browse_activity: Dólar e IPC (Avanzado)", 
    ":material/fact_check: Dólar e IPC (Diagnósticos)", 
    ":material/browse_activity: Ventas Tech (Avanzado)", 
    ":material/fact_check: Ventas Tech (Diagnósticos)", 
    ":material/analytics: Descomposición STL",
    ":material/compare_arrows: Benchmarking Multi-Modelo"
])

# ------------------------------------------------------------------------------
# TAB 1: DÓLAR E IPC - AVANZADO
# ------------------------------------------------------------------------------
with tab1:
    st.subheader(":material/monitoring: Análisis y Pronóstico Out-of-Sample: Dólar / IPC")
    st.markdown(r"""
    Evaluación econométrica con bandas de control de anomalías ($\pm 2\sigma$) y proyección de incertidumbre futura a N periodos.
    """)
    
    if df_dolar is None:
        st.warning(":material/warning: Por favor sube el archivo 'dolar-ipc.xlsx' en la barra lateral.")
    else:
        ts_data1 = df_dolar[var_dolar].dropna()
        try:
            model1 = ExponentialSmoothing(
                ts_data1, trend=trend_dolar, seasonal=stype_dolar, seasonal_periods=seas_dolar
            ).fit()
            
            fitted_values1 = model1.fittedvalues
            residuals1 = ts_data1 - fitted_values1
            
            forecast_values = model1.forecast(horizonte_pronostico)
            
            if isinstance(ts_data1.index, pd.DatetimeIndex):
                future_dates = pd.date_range(start=ts_data1.index[-1], periods=horizonte_pronostico + 1, freq=ts_data1.index.inferred_freq or 'MS')[1:]
            else:
                future_dates = range(len(ts_data1), len(ts_data1) + horizonte_pronostico)

            std_res1 = residuals1.std()
            upper_cone = forecast_values + (1.96 * std_res1)
            lower_cone = forecast_values - (1.96 * std_res1)

            rmse1 = np.sqrt(np.mean(residuals1**2))
            mae1 = np.mean(np.abs(residuals1))
            mean_res1 = residuals1.mean()
            upper_band1 = mean_res1 + (2 * std_res1)
            lower_band1 = mean_res1 - (2 * std_res1)
            outliers1 = residuals1[(residuals1 > upper_band1) | (residuals1 < lower_band1)]

            col1, col2, col3, col4, col5 = st.columns(5)
            col1.metric("Media Residuales", f"{mean_res1:.4f}")
            col2.metric(r"Desv. Estándar ($\sigma$)", f"{std_res1:.4f}")
            col3.metric("RMSE", f"{rmse1:.4f}")
            col4.metric("MAE", f"{mae1:.4f}")
            col5.metric(r"Anomalías In-Sample", f"{len(outliers1)}")

            st.markdown("---")
            fig1 = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.12,
                                subplot_titles=(f"Histórico, Ajuste y Proyección Futura ({var_dolar})", r"Serie de Residuales con Bandas de Control ($\pm 2\sigma$)"))
            
            fig1.add_trace(go.Scatter(x=ts_data1.index, y=ts_data1, mode='lines+markers', name="Valor Real (Yt)", line=dict(color="#1f77b4", width=2)), row=1, col=1)
            fig1.add_trace(go.Scatter(x=fitted_values1.index, y=fitted_values1, mode='lines', name="Modelo Ajustado (Ŷt)", line=dict(color="#ff7f0e", width=2, dash="dash")), row=1, col=1)
            
            fig1.add_trace(go.Scatter(x=future_dates, y=forecast_values, mode='lines+markers', name="Pronóstico Futuro", line=dict(color="#2ca02c", width=2, dash="dot")), row=1, col=1)
            fig1.add_trace(go.Scatter(x=future_dates, y=upper_cone, mode='lines', name="Límite Superior (95% IC)", line=dict(color="rgba(44,160,44,0.2)", width=1)), row=1, col=1)
            fig1.add_trace(go.Scatter(x=future_dates, y=lower_cone, mode='lines', name="Límite Inferior (95% IC)", line=dict(color="rgba(44,160,44,0.2)", width=1), fill='tonexty', fillcolor='rgba(44,160,44,0.05)'), row=1, col=1)

            fig1.add_trace(go.Scatter(x=residuals1.index, y=residuals1, mode='lines+markers', name="Residuales", line=dict(color="#9467bd", width=1.5)), row=2, col=1)
            fig1.add_hline(y=upper_band1, line_dash="dash", line_color="orange", annotation_text="+2σ (Límite Superior)", row=2, col=1)
            fig1.add_hline(y=lower_band1, line_dash="dash", line_color="orange", annotation_text="-2σ (Límite Inferior)", row=2, col=1)
            fig1.add_hline(y=0, line_dash="dot", line_color="red", row=2, col=1)

            if not outliers1.empty:
                fig1.add_trace(go.Scatter(x=outliers1.index, y=outliers1, mode='markers', name="Anomalías / Outliers", marker=dict(color="red", size=10, symbol="x")), row=2, col=1)

            fig1.update_layout(height=700, template="plotly_white", hovermode="x unified", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
            st.plotly_chart(fig1, width='stretch')

        except Exception as e:
            st.error(f"Error en el modelo: {e}")

# ------------------------------------------------------------------------------
# TAB 2: DÓLAR E IPC - DIAGNÓSTICOS (LJUNG-BOX & JARQUE-BERA)
# ------------------------------------------------------------------------------
with tab2:
    st.subheader(":material/fact_check: Auditoría de Ruido Blanco y Pruebas de Hipótesis: Dólar / IPC")
    st.markdown(r"""
    Validación econométrica formal para certificar la calidad de los residuales del modelo de Dólar / IPC:
    * **Prueba de Ljung-Box:** Evalúa si existe autocorrelación serial (ausencia de patrones ocultos).
    * **Prueba de Jarque-Bera:** Evalúa la normalidad de los errores para legitimar el uso de umbrales probabilísticos.
    """)
    
    if df_dolar is not None:
        try:
            model_diag1 = ExponentialSmoothing(ts_data1, trend=trend_dolar, seasonal=stype_dolar, seasonal_periods=seas_dolar).fit()
            res_diag1 = model_diag1.fittedvalues - ts_data1
            res_clean1 = res_diag1.dropna()

            lb_result1 = acorr_ljungbox(res_clean1, lags=[10], return_df=True)
            lb_stat1 = lb_result1['lb_stat'].values[0]
            lb_pvalue1 = lb_result1['lb_pvalue'].values[0]

            jb_stat1, jb_pvalue1, _, _ = jarque_bera(res_clean1)

            col_d1, col_d2 = st.columns(2)
            
            with col_d1:
                st.markdown(r"#### :material/auto_awesome_motion: Prueba de Autocorrelación (Ljung-Box)")
                st.metric("Estadístico Chi-Cuadrado", f"{lb_stat1:.4f}")
                st.metric("Valor P (p-value)", f"{lb_pvalue1:.4f}")
                if lb_pvalue1 > 0.05:
                    st.success(r" :material/check_box: **Resultado Favorable:** No se rechaza la hipótesis nula. Los residuales **no** presentan autocorrelación serial significativa (Ruido Blanco).")
                else:
                    st.warning(r":material/warning: **Alerta:** Los residuales muestran autocorrelación. El modelo dejó información sin capturar.")

            with col_d2:
                st.markdown(r"#### :material/stacked_line_chart: Prueba de Normalidad (Jarque-Bera)")
                st.metric("Estadístico JB", f"{jb_stat1:.4f}")
                st.metric("Valor P (p-value)", f"{jb_pvalue1:.4f}")
                if jb_pvalue1 > 0.05:
                    st.success(r":material/check_box: **Resultado Favorable:** Los residuales siguen una distribución normal, validando con precisión el uso de bandas basadas en $\sigma$.")
                else:
                    st.info(r":material/chat_info: Los residuales difieren de la normalidad estricta (presencia de colas pesadas o valores atípicos).")

        except Exception as e:
            st.error(f"No se pudieron calcular las pruebas estadísticas: {e}")

# ------------------------------------------------------------------------------
# TAB 3: VENTAS TECH - AVANZADO
# ------------------------------------------------------------------------------
with tab3:
    st.subheader(":material/monitoring: Análisis Comercial y Proyección: Ventas Tech")
    st.markdown(r"""
    Modelo predictivo segmentado por país y categoría con análisis de desviaciones de ventas, bandas de control ($\pm 2\sigma$) y cono de confianza financiero.
    """)
    
    if df_tech is None or ts_df_tech is None:
        st.warning(":material/warning: Por favor sube el archivo de datos comerciales.")
    elif len(ts_df_tech) < 4:
        st.warning("Historial insuficiente para ajustar el modelo estacional.")
    else:
        try:
            model3 = ExponentialSmoothing(
                ts_df_tech, trend=trend_tech, seasonal=stype_tech, seasonal_periods=seas_tech if seas_tech < len(ts_df_tech) else None
            ).fit()
            
            fitted_values3 = model3.fittedvalues
            residuals3 = ts_df_tech - fitted_values3
            forecast_tech = model3.forecast(horizonte_pronostico)
            
            if isinstance(ts_df_tech.index, pd.DatetimeIndex):
                future_dates_tech = pd.date_range(start=ts_df_tech.index[-1], periods=horizonte_pronostico + 1, freq='MS')[1:]
            else:
                future_dates_tech = range(len(ts_df_tech), len(ts_df_tech) + horizonte_pronostico)

            std_res3 = residuals3.std()
            mean_res3 = residuals3.mean()
            upper_band3 = mean_res3 + (2 * std_res3)
            lower_band3 = mean_res3 - (2 * std_res3)
            outliers3 = residuals3[(residuals3 > upper_band3) | (residuals3 < lower_band3)]

            upper_cone_tech = forecast_tech + (1.96 * std_res3)
            lower_cone_tech = forecast_tech - (1.96 * std_res3)

            col_k1, col_k2, col_k3 = st.columns(3)
            col_k1.metric("Ventas Totales Históricas", f"${df_filtered_tech['total'].sum():,.2f}")
            col_k2.metric("Utilidad Acumulada", f"${df_filtered_tech['utilidad'].sum():,.2f}")
            col_k3.metric("Meses Atípicos Detectados", f"{len(outliers3)}")

            st.markdown("---")
            fig3 = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.12,
                                subplot_titles=(f"Rendimiento Comercial y Pronóstico ({metrica_tech.capitalize()})", r"Residuales con Bandas de Control de Outliers ($\pm 2\sigma$)"))
            
            fig3.add_trace(go.Scatter(x=ts_df_tech.index, y=ts_df_tech, mode='lines+markers', name="Real", line=dict(color="#2ca02c", width=2)), row=1, col=1)
            fig3.add_trace(go.Scatter(x=fitted_values3.index, y=fitted_values3, mode='lines', name="Ajuste", line=dict(color="#ff7f0e", width=2, dash="dash")), row=1, col=1)
            fig3.add_trace(go.Scatter(x=future_dates_tech, y=forecast_tech, mode='lines+markers', name="Pronóstico", line=dict(color="#1f77b4", width=2, dash="dot")), row=1, col=1)
            fig3.add_trace(go.Scatter(x=future_dates_tech, y=upper_cone_tech, mode='lines', name="Límite Superior (95%)", line=dict(color="rgba(31,119,180,0.2)", width=1)), row=1, col=1)
            fig3.add_trace(go.Scatter(x=future_dates_tech, y=lower_cone_tech, mode='lines', name="Límite Inferior (95%)", line=dict(color="rgba(31,119,180,0.2)", width=1), fill='tonexty', fillcolor='rgba(31,119,180,0.05)'), row=1, col=1)

            fig3.add_trace(go.Scatter(x=residuals3.index, y=residuals3, mode='lines+markers', name="Residuales", line=dict(color="#d62728", width=1.5)), row=2, col=1)
            fig3.add_hline(y=upper_band3, line_dash="dash", line_color="orange", annotation_text="+2σ (Éxito Comercial Atípico)", row=2, col=1)
            fig3.add_hline(y=lower_band3, line_dash="dash", line_color="orange", annotation_text="-2σ (Alerta Quiebre)", row=2, col=1)
            fig3.add_hline(y=0, line_dash="dot", line_color="black", row=2, col=1)

            if not outliers3.empty:
                fig3.add_trace(go.Scatter(x=outliers3.index, y=outliers3, mode='markers', name="Meses Atípicos", marker=dict(color="purple", size=12, symbol="star")), row=2, col=1)

            fig3.update_layout(height=700, template="plotly_white", hovermode="x unified", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
            st.plotly_chart(fig3, width='stretch')

        except Exception as e:
            st.error(f"Error comercial: {e}")

# ------------------------------------------------------------------------------
# TAB 4: VENTAS TECH - DIAGNÓSTICOS (LJUNG-BOX & JARQUE-BERA)
# ------------------------------------------------------------------------------
with tab4:
    st.subheader(":material/fact_check: Auditoría de Ruido Blanco y Pruebas de Hipótesis: Ventas Tech")
    st.markdown(r"""
    Validación econométrica formal para certificar la calidad de los residuales del modelo comercial de Ventas Tech:
    * **Prueba de Ljung-Box:** Evalúa si existe autocorrelación serial en las ventas.
    * **Prueba de Jarque-Bera:** Evalúa la normalidad de los errores comerciales.
    """)
    
    if df_tech is not None and ts_df_tech is not None and len(ts_df_tech) >= 4:
        try:
            model_diag3 = ExponentialSmoothing(ts_df_tech, trend=trend_tech, seasonal=stype_tech, seasonal_periods=seas_tech if seas_tech < len(ts_df_tech) else None).fit()
            res_diag3 = model_diag3.fittedvalues - ts_df_tech
            res_clean3 = res_diag3.dropna()

            lb_result3 = acorr_ljungbox(res_clean3, lags=[min(10, len(res_clean3)//2)], return_df=True)
            lb_stat3 = lb_result3['lb_stat'].values[0]
            lb_pvalue3 = lb_result3['lb_pvalue'].values[0]

            jb_stat3, jb_pvalue3, _, _ = jarque_bera(res_clean3)

            col_d3, col_d4 = st.columns(2)
            
            with col_d3:
                st.markdown(r"#### :material/auto_awesome_motion: Prueba de Autocorrelación (Ljung-Box)")
                st.metric("Estadístico Chi-Cuadrado", f"{lb_stat3:.4f}")
                st.metric("Valor P (p-value)", f"{lb_pvalue3:.4f}")
                if lb_pvalue3 > 0.05:
                    st.success(r":material/check_box: **Resultado Favorable:** No se rechaza la hipótesis nula. Los residuales de ventas **no** presentan autocorrelación serial significativa (Ruido Blanco).")
                else:
                    st.warning(r":material/warning: **Alerta:** Los residuales de ventas muestran autocorrelación. El modelo comercial dejó estacionalidad sin capturar.")

            with col_d4:
                st.markdown(r"#### :material/stacked_line_chart: Prueba de Normalidad (Jarque-Bera)")
                st.metric("Estadístico JB", f"{jb_stat3:.4f}")
                st.metric("Valor P (p-value)", f"{jb_pvalue3:.4f}")
                if jb_pvalue3 > 0.05:
                    st.success(r":material/check_box: **Resultado Favorable:** Los residuales siguen una distribución normal, validando con precisión el uso de umbrales basados en $\sigma$.")
                else:
                    st.info(r":material/chat_info: Los residuales comerciales difieren de la normalidad estricta (presencia de campañas o shocks atípicos).")

        except Exception as e:
            st.error(f"No se pudieron calcular las pruebas estadísticas de ventas: {e}")
    else:
        st.warning(":material/warning: Selecciona una combinación válida de País y Categoría con suficiente historial para ejecutar los diagnósticos.")

# ------------------------------------------------------------------------------
# TAB 5: DESCOMPOSICIÓN EXPLÍCITA DE LA SERIE (MÉTODO STL MULTI-DATASET)
# ------------------------------------------------------------------------------
with tab5:
    st.subheader(":material/analytics: Descomposición Estructural STL (Tendencia, Estacionalidad y Ruido)")
    st.markdown(r"""
    Aislamiento matemático de los componentes subyacentes de la serie mediante *Seasonal and Trend decomposition using Loess*.
    """)
    
    dataset_stl = st.radio("Selecciona el dataset a descomponer:", ["Dólar / IPC", "Ventas Tech"], horizontal=True, key="ds_stl")
    
    if dataset_stl == "Dólar / IPC":
        if df_dolar is not None:
            serie_stl = ts_data1
            periodo_stl = seas_dolar
            titulo_serie = var_dolar
        else:
            serie_stl = None
    else:
        if ts_df_tech is not None and len(ts_df_tech) >= 4:
            serie_stl = ts_df_tech
            periodo_stl = seas_tech
            titulo_serie = f"Ventas Tech ({pais_tech} - {cat_tech} - {metrica_tech})"
        else:
            serie_stl = None

    if serie_stl is not None:
        try:
            stl = STL(serie_stl, period=periodo_stl)
            res_stl = stl.fit()
            
            trend = res_stl.trend
            seasonal = res_stl.seasonal
            resid = res_stl.resid

            fig_stl = make_subplots(rows=4, cols=1, shared_xaxes=True, vertical_spacing=0.08,
                                    subplot_titles=(f"Serie Original ({titulo_serie})", "Tendencia Estructural", "Componente Estacional", "Residuales Puros (Ruido)"))
            
            fig_stl.add_trace(go.Scatter(x=serie_stl.index, y=serie_stl, mode='lines', name="Original", line=dict(color="#1f77b4")), row=1, col=1)
            fig_stl.add_trace(go.Scatter(x=trend.index, y=trend, mode='lines', name="Tendencia", line=dict(color="#ff7f0e")), row=2, col=1)
            fig_stl.add_trace(go.Scatter(x=seasonal.index, y=seasonal, mode='lines', name="Estacionalidad", line=dict(color="#2ca02c")), row=3, col=1)
            fig_stl.add_trace(go.Scatter(x=resid.index, y=resid, mode='lines+markers', name="Residuales", line=dict(color="#9467bd", width=1)), row=4, col=1)
            
            fig_stl.update_layout(height=800, template="plotly_white", showlegend=False)
            st.plotly_chart(fig_stl, width='stretch')

        except Exception as e:
            st.error(f"Error en descomposición STL (asegúrate de que el periodo de estacionalidad sea compatible con el largo de la serie): {e}")
    else:
        st.warning(":material/warning: Selecciona un dataset y una combinación válida con suficientes datos para realizar la descomposición.")

# ------------------------------------------------------------------------------
# TAB 6: BENCHMARKING MULTI-MODELO (HOLT-WINTERS vs SARIMAX MULTI-DATASET)
# ------------------------------------------------------------------------------
with tab6:
    st.subheader(":material/compare_arrows: Benchmarking y Criterios de Información (AIC / BIC)")
    st.markdown(r"""
    Comparativa algorítmica de ajuste financiero para determinar cuál modelo minimiza el error de estimación y optimiza la parsimonia.
    """)
    
    dataset_bench = st.radio("Selecciona el dataset para el Benchmarking:", ["Dólar / IPC", "Ventas Tech"], horizontal=True, key="ds_bench")
    
    if dataset_bench == "Dólar / IPC":
        if df_dolar is not None:
            serie_bench = ts_data1
            trend_b, stype_b, seas_b = trend_dolar, stype_dolar, seas_dolar
            nombre_b = var_dolar
        else:
            serie_bench = None
    else:
        if ts_df_tech is not None and len(ts_df_tech) >= 4:
            serie_bench = ts_df_tech
            trend_b, stype_b, seas_b = trend_tech, stype_tech, seas_tech
            nombre_b = f"Ventas Tech ({pais_tech} - {cat_tech})"
        else:
            serie_bench = None

    if serie_bench is not None:
        try:
            # Modelo 1: Holt-Winters
            hw_model = ExponentialSmoothing(serie_bench, trend=trend_b, seasonal=stype_b, seasonal_periods=seas_b).fit()
            hw_fit = hw_model.fittedvalues
            hw_res = serie_bench - hw_fit
            hw_rmse = np.sqrt(np.mean(hw_res**2))
            hw_aic = hw_model.aic if hasattr(hw_model, 'aic') else "N/A"

            # Modelo 2: SARIMAX Automático
            sarimax_model = SARIMAX(serie_bench, order=(1,1,1), seasonal_order=(1,1,1,min(12, max(2, seas_b)))).fit(disp=False)
            sar_fit = sarimax_model.fittedvalues
            sar_res = serie_bench - sar_fit
            sar_rmse = np.sqrt(np.mean(sar_res**2))
            sar_aic = sarimax_model.aic

            col_b1, col_b2 = st.columns(2)
            
            with col_b1:
                st.markdown("#### :material/area_chart: Holt-Winters Exponential Smoothing")
                st.metric("RMSE", f"{hw_rmse:,.4f}")
                st.metric("Criterio AIC", f"{hw_aic}" if isinstance(hw_aic, str) else f"{hw_aic:.2f}")

            with col_b2:
                st.markdown("#### :material/line_axis: SARIMAX Automático")
                st.metric("RMSE", f"{sar_rmse:,.4f}")
                st.metric("Criterio AIC", f"{sar_aic:.2f}")

            st.markdown("---")
            fig_bench = go.Figure()
            fig_bench.add_trace(go.Scatter(x=serie_bench.index, y=serie_bench, mode='lines', name="Real", line=dict(color="black", width=2)))
            fig_bench.add_trace(go.Scatter(x=hw_fit.index, y=hw_fit, mode='lines', name="Holt-Winters", line=dict(color="#ff7f0e", width=1.5, dash="dash")))
            fig_bench.add_trace(go.Scatter(x=sar_fit.index, y=sar_fit, mode='lines', name="SARIMAX", line=dict(color="#2ca02c", width=1.5, dash="dot")))
            
            fig_bench.update_layout(height=500, template="plotly_white", title=f"Comparativa de Ajuste de Modelos para: {nombre_b}", hovermode="x unified")
            st.plotly_chart(fig_bench, width='stretch')

        except Exception as e:
            st.info(f"El benchmarking requiere una serie temporal sin valores nulos extremos o con suficiente historial: {e}")
    else:
        st.warning(":material/warning: Selecciona un dataset válido con suficientes registros para ejecutar el benchmarking.")