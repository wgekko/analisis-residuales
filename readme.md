#  Terminal Avanzada de Análisis Econométrico y Residuales

Una aplicación web interactiva desarrollada en **Python** y **Streamlit** orientada al análisis financiero, modelado de series temporales y auditoría de residuales (ruido blanco). Diseñada bajo buenas prácticas de ingeniería de software para científicos de datos y analistas financieros.

---

##  Características Principales

* **Módulos Especializados:** 
  * **Análisis Macroeconómico:** Evaluación de tipos de cambio e inflación regional (IPC).
  * **Inteligencia Comercial (Ventas Tech):** Segmentación por país, categoría y métricas financieras (ventas totales, unidades y utilidad).
* **Modelos Estadísticos Predictivos:** Ajuste mediante **Suavizamiento Exponencial de Holt-Winters** con selectores avanzados de tendencia y estacionalidad.
* **Pronóstico Out-of-Sample & Cono de Confianza:** Proyecciones a futuro (hasta 24 meses) acompañadas de intervalos de confianza probabilísticos al 95% ($\pm 1.96\sigma$).
* **Control de Anomalías y Outliers:** Bandas dinámicas de control ($\pm 2\sigma$) para la detección visual de shocks o eventos atípicos.
* **Pruebas de Diagnóstico Formales:** 
  * *Prueba de Ljung-Box* para la verificación de autocorrelación serial (Ruido Blanco).
  * *Prueba de Jarque-Bera* para auditar la normalidad de los errores estadísticos.
* **Descomposición Estructural (STL):** Aislamiento matemático de la Tendencia, la Estacionalidad y el Ruido puro mediante *Seasonal and Trend decomposition using Loess*.
* **Benchmarking Multi-Modelo:** Comparativa de desempeño y criterios de información (**AIC / BIC**) entre *Holt-Winters* y *SARIMAX Automático*.
* **Optimización de Rendimiento:** Ingesta de datos y modelos acelerados mediante caché nativo (`st.cache_data`) y visualizaciones interactivas de alto rendimiento con **Plotly**.

---

##  Tecnologías y Librerías Utilizadas

* **Python 3.x**
* **Streamlit** (Interfaz de usuario interactiva y multipestaña)
* **Statsmodels** (Modelos de series temporales, STL y pruebas de diagnóstico econométrico)
* **Pandas & NumPy** (Procesamiento y manipulación numérica de datos)
* **Plotly** (Gráficos dinámicos y responsivos)

---
## Configuración de las fuentes y background de la actual app

- Crear una carpeta llamada .streamlit y dentro generar un archivo llamado config.toml

[server]
enableStaticServing = false

[[theme.fontFaces]]
family = "Inter"
url = "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap"

[theme]
primaryColor = "#FF8C00"
backgroundColor = "#0D1B2A"
secondaryBackgroundColor = "#1B263B"
textColor = "#FFA500"
linkColor = "#FFA500"
borderColor = "#CCCCCC"
showWidgetBorder = true
baseRadius = "0.5rem"
buttonRadius = "0.5rem"
font = "Inter"
headingFontWeights = [600, 500]
headingFontSizes = ["2.5rem", "1.8rem"]
codeFont = "Courier New"
codeFontSize = "0.75rem"
codeBackgroundColor = "#112B3C"
showSidebarBorder = false
chartCategoricalColors = [
  "#FF8C00",  # Orange oscuro
  "#FFA500",  # Naranja clásico
  "#FFD700",  # Mostaza / dorado
  "#E1C16E",  # Mostaza claro
  "#C8E25D",  # Lima suave
  "#A8D08D",  # Verde pastel
  "#7AC36A",  # Verde hoja
  "#4CAF50",  # Verde medio
  "#40C4FF",  # Celeste vibrante
  "#00B0F0",  # Celeste profesional
  "#3399FF",  # Celeste más oscuro
  "#1E88E5",  # Azul Francia
  "#1976D2",  # Azul fuerte
  "#1565C0",  # Azul oscuro
  "#0D47A1",   # Azul muy profundo
  "#FF8C00",
  "#FFA500",
  "#FFB347",
  "#FFD580",
  "#FFA07A",
  "#FF7F50",
  "#FF6F00",
  "#CC7000",
  "#FFC107",
  "#FFDD57",
  "#E67E22",
  "#D35400",
  "#F39C12",
  "#E67E22",
  "#F4A261"
]

[theme.sidebar]
backgroundColor = "#1E3A5F"
secondaryBackgroundColor = "#1B263B"
headingFontSizes = ["1.6rem", "1.4rem", "1.2rem"]
dataframeHeaderBackgroundColor = "#1A2A40"

---

## Instalación y Ejecución Local

1. Clona este repositorio:
   ```bash
   git clone [https://github.com/tu-usuario/tu-repositorio.git](https://github.com/tu-usuario/tu-repositorio.git)
   cd tu-repositorio