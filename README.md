# 🎬 YouTube Downloader Web

Una aplicación web moderna para descargar videos y audio de YouTube de forma rápida y sencilla.

## ✨ Características

- 🎯 **Interfaz intuitiva** - Diseño moderno y fácil de usar
- 🚀 **Descarga rápida** - Powered by yt-dlp
- 📊 **Progreso en tiempo real** - Monitoreo de descarga con barra de progreso
- 🎵 **Múltiples formatos** - Video completo o solo audio
- 📱 **Responsive** - Funciona en desktop y móvil
- ⚡ **Múltiples calidades** - 1080p, 720p, 480p o mejor disponible

## 🚀 Instalación Local

### Prerrequisitos
- Python 3.11+
- pip

### Pasos

1. **Clonar el repositorio**
   ```bash
   git clone <tu-repo>
   cd youtube-web-app
   ```

2. **Crear entorno virtual**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   ```

3. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   ```

4. **Ejecutar la aplicación**
   ```bash
   python app.py
   ```

5. **Abrir en navegador**
   ```
   http://localhost:5000
   ```

## 🌐 Despliegue en la Web

### Opción 1: Render (Recomendado - Gratis)

1. **Crear cuenta** en [render.com](https://render.com)
2. **Conectar repositorio** GitHub
3. **Configurar servicio:**
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `./start.sh`
   - Environment: Python 3

### Opción 2: Railway

1. **Crear cuenta** en [railway.app](https://railway.app)
2. **Conectar GitHub** y desplegar automáticamente
3. **Configuración automática**

### Opción 3: Docker

```bash
# Construir imagen
docker build -t youtube-downloader .

# Ejecutar contenedor
docker run -p 5000:5000 youtube-downloader
```

## 🔧 Configuración

### Variables de Entorno

- `PORT` - Puerto de la aplicación (default: 5000)
- `FLASK_ENV` - Entorno de Flask (development/production)

### Personalización

- **Estilos:** Edita `static/css/style.css`
- **Lógica:** Modifica `static/js/app.js`
- **Backend:** Actualiza `app.py`

## 📁 Estructura del Proyecto

```
youtube-web-app/
├── app.py                 # Aplicación Flask principal
├── requirements.txt       # Dependencias Python
├── Dockerfile            # Configuración Docker
├── gunicorn.conf.py      # Configuración Gunicorn
├── start.sh              # Script de inicio
├── templates/
│   └── index.html        # Plantilla HTML
├── static/
│   ├── css/
│   │   └── style.css     # Estilos CSS
│   └── js/
│       └── app.js        # JavaScript frontend
└── downloads/            # Directorio de descargas temporales
```

## 🛡️ Consideraciones Legales

⚠️ **Importante:** Esta aplicación debe usarse responsablemente:

- Respeta los términos de servicio de YouTube
- No descargues contenido con derechos de autor sin permiso
- Usa solo para contenido propio o con licencia apropiada
- Considera las leyes locales sobre descarga de contenido

## 🤝 Contribuir

1. Fork el proyecto
2. Crea una branch (`git checkout -b feature/nueva-caracteristica`)
3. Commit los cambios (`git commit -am 'Agregar nueva característica'`)
4. Push a la branch (`git push origin feature/nueva-caracteristica`)
5. Crear Pull Request

## 📝 Licencia

Este proyecto es de código abierto. Ver `LICENSE` para más detalles.

## 🐛 Reportar Bugs

Si encuentras algún problema, por favor abre un issue en GitHub con:

- Descripción del problema
- Pasos para reproducir
- Información del sistema
- Screenshots si es posible

---

**Creado con ❤️ por Hugo Torres**