# 👗 Fashion Wardrobe Manager - Frontend App

Una aplicación moderna de gestión de guardarropa con arquitectura local-first y sincronización automática con backend.

## 🎯 Características Principales

### 🏠 Arquitectura Local-First
- **Imágenes almacenadas localmente** en `~/.fashion_wardrobe_app/images/`
- **Modelos IA almacenados localmente** en `~/.fashion_wardrobe_app/models/`
- **Soporte offline** - funciona sin conexión backend
- **Sincronización automática** cuando el backend está disponible
- **Acceso rápido** a todos los datos sin depender de internet

### 👔 Gestión de Guardarropa
- 📸 **Subir prendas**: Carga imágenes de ropa con metadatos automáticos
- 🏷️ **Auto-etiquetado**: Categorización automática usando IA (main category, subcategoría, atributos)
- 🎨 **Organización**: Filtra por categoría, color, marca, estación
- 💾 **Almacenamiento local**: Todas las imágenes guardadas localmente para acceso rápido
- ✏️ **Edición**: Modifica detalles, colores, categorías de prendas existentes
- 🗑️ **Gestión**: Elimina prendas no deseadas
- 🔍 **Búsqueda avanzada**: Filtra por múltiples criterios

### 👗 Combinador de Outfits
- 🎯 **Generador automático**: Crea combinaciones compatibles usando IA
- ⭐ **Puntuación de compatibilidad**: Muestra qué tan bien combinan las prendas (0-1)
- 💾 **Guardar favoritos**: Almacena outfits que te gustan
- 📊 **Estadísticas**: Analiza tendencias en tus combinaciones
- 🎨 **Visualización**: Ve cómo se ven juntas las prendas
- 🔄 **Sugerencias personalizadas**: Genera recomendaciones basadas en tus preferencias

### 🤖 Gestión de Modelos de IA
- 📥 **Descargar modelos persona**: Obtén modelos personalizados según tus preferencias
- ✓ **Verificación automática**: Valida integridad con checksums SHA-256
- 💾 **Almacenamiento local**: Guarda los modelos en tu máquina
- 🔄 **Backup automático**: Realiza copias de seguridad de tus modelos
- 📋 **Manifest tracking**: Control de versiones de modelos
- ⚡ **Carga rápida**: Acceso instantáneo a modelos sin descargas repetidas
- 🔐 **Encriptación**: Modelos protegidos localmente

### 🔐 Autenticación y Seguridad
- 📝 **Registro**: Crea nuevas cuentas de usuario
- 🔑 **Login seguro**: Autenticación con backend segura
- 👤 **Sesiones persistentes**: Mantiene tu sesión activa
- 🔒 **Cifrado**: Datos sensibles protegidos
- 📊 **Control de acceso**: Solo tus datos privados son visibles

### 📊 Dashboard Inteligente
- 📈 **Estadísticas almacenamiento**: Ve cuánto espacio usas
- 📦 **Información de modelos**: Detalles de modelos descargados
- 🔌 **Estado conexión**: Verifica si backend está disponible
- ⚡ **Actividad reciente**: Historial de cambios
- 💻 **Información del dispositivo**: Datos del almacenamiento local
- 🎨 **Contador de prendas**: Total de items en tu guardarropa
- 👕 **Desglose por categoría**: Ve distribución de prendas

### ⚙️ Configuración Avanzada
- 🔗 **Configurar backend**: Cambia URL del servidor
- 💾 **Gestionar almacenamiento**: Limpia cache, libera espacio
- 🗑️ **Limpiar caché**: Elimina datos temporales
- 🔄 **Sincronización manual**: Fuerza sincronización con backend
- ℹ️ **Información de la app**: Versión, licencia
- 🌙 **Tema**: Cambia entre tema claro/oscuro (Streamlit nativo)

## 📋 Guía Detallada de Funcionalidades

### 1️⃣ Pantalla de Autenticación
**Archivo:** `app_pages/auth.py`

**Funcionalidades:**
- 📝 **Registro de usuario** - Crea nueva cuenta
- 🔑 **Login** - Accede con credenciales
- 👤 **Gestión de sesión** - Mantiene estado autenticado
- 🔄 **Recuperación de sesión** - Carga sesión guardada

**Flujo:**
```
1. Usuario abre la app
2. Si no está autenticado → Muestra formulario login/registro
3. Si está autenticado → Carga dashboard
4. Sesión se guarda en Streamlit session_state
```

### 2️⃣ Dashboard
**Archivo:** `app_pages/dashboard.py`

**Componentes:**
- 📊 **Tarjetas de estadísticas**
  - Total de prendas en guardarropa
  - Espacio usado por imágenes
  - Espacio usado por modelos
  - Modelos descargados
  
- 📈 **Gráficos visuales**
  - Distribución de prendas por categoría
  - Desglose por colores más comunes
  - Historial de actividad reciente
  
- 🔌 **Estado del sistema**
  - Conectividad con backend
  - Disponibilidad de sincronización
  - Última sincronización realizada

- ⚡ **Acciones rápidas**
  - Sincronizar ahora
  - Ir a guardarropa
  - Crear outfit
  - Descargar modelo

### 3️⃣ Gestión de Guardarropa
**Archivo:** `app_pages/wardrobe.py`

**Características principales:**

**Subir nuevas prendas:**
- 📷 Carga múltiples imágenes
- 📝 Ingresa metadatos manuales
- 🤖 Auto-categorización con IA
- 💾 Guarda en almacenamiento local
- 🔄 Sincroniza con backend

**Visualizar prendas:**
- 🎨 Galería con miniaturas
- 📋 Vista de lista detallada
- 🔍 Búsqueda en tiempo real
- 🏷️ Filtros por:
  - Categoría principal (Tops, Bottoms, Shoes, etc.)
  - Color
  - Marca
  - Estación (Verano, Invierno, etc.)
  - Fecha de agregación

**Acciones por prenda:**
- ✏️ **Editar**: Modifica categoría, color, detalles
- 👁️ **Ver detalles**: Información completa
- ❤️ **Marcar favorito**: Para acceso rápido
- 🗑️ **Eliminar**: Quita del guardarropa
- 📤 **Compartir**: Envía a otros usuarios (futuro)

**Vista de tabla:**
- Nombre de la prenda
- Categoría (con emojis indicadores)
- Color principal
- Marca
- Fecha de agregación
- Acciones rápidas

### 4️⃣ Combinador de Outfits
**Archivo:** `app_pages/outfits.py`

**Modo generador automático:**
- 🎯 **Generar outfit**: Selecciona número de prendas
- 🤖 **Recomendaciones IA**: Basadas en compatibilidad
- ⭐ **Puntuación**: Muestra compatibilidad (0.0-1.0)
- 👁️ **Visualización**: Ve cómo se ven juntas

**Funcionalidades:**
- 🔄 **Regenerar**: Obtén diferentes combinaciones
- 💾 **Guardar outfit**: Almacena como favorito
- 📊 **Historial**: Ve outfits guardados anteriormente
- 🎨 **Análisis estilístico**:
  - Combinaciones por categoría
  - Tendencias de color
  - Compatibilidad promedio

**Tipos de generación:**
- 🌞 **Por ocasión**: Casual, Trabajo, Noche, Deportiva
- 🎨 **Por paleta de colores**: Monocromático, Complementario, Análogo
- 📍 **Por estación**: Apta para clima actual
- ❤️ **Personalizado**: Basado en tus preferencias

### 5️⃣ Edición de Prendas
**Archivo:** `app_pages/edit_item.py`

**Campos editables:**
- 🏷️ **Nombre**: Descripción de la prenda
- 🎨 **Color**: Principal y secundarios
- 📂 **Categoría**: Main, Sub, Tipo específico
- 🏢 **Marca**: Fabricante/Diseñador
- 📏 **Talla**: XS, S, M, L, XL, XXL
- 🧵 **Material**: Algodón, Poliéster, etc.
- 📝 **Notas**: Observaciones personales
- 🏷️ **Etiquetas**: Tags personalizadas

**Validaciones:**
- ✓ Campos requeridos
- ✓ Formatos válidos
- ✓ Sin caracteres especiales
- ✓ Longitud máxima/mínima

**Guardar cambios:**
- 💾 Localización inmediata
- 🔄 Sincronización con backend
- ↩️ Opción de deshacer

### 6️⃣ Configuración
**Archivo:** `app_pages/settings.py`

**Opciones de backend:**
- 🔗 **URL del servidor**: Cambia endpoint backend
- ⏱️ **Timeout**: Segundos para esperar respuesta
- ✓ **Prueba de conexión**: Verifica disponibilidad

**Gestión de almacenamiento:**
- 📊 **Estadísticas de uso**: Desglose de espacio
- 🗑️ **Limpiar caché**: Elimina datos temporales
- 📥 **Exportar datos**: Backup de guardarropa
- 📤 **Importar datos**: Restaura desde backup

**Sincronización:**
- 🔄 **Sincronizar ahora**: Fuerza sincronización manual
- 📅 **Último sync**: Cuándo se sincronizó por última vez
- ⚙️ **Auto-sync**: Habilitado por defecto
- 📋 **Log de sincronización**: Historial de cambios

**Información y ayuda:**
- ℹ️ **Versión de la app**
- 📄 **Licencia**
- 🔗 **Enlaces útiles**
- 💬 **Contacto/Soporte**

## 🏗️ Estructura del Proyecto

```
frontend/
├── app.py                      # Punto de entrada Streamlit
├── config.py                   # Configuración y LocalStorage
├── api_client.py              # Cliente HTTP backend
├── model_manager.py           # Gestión de modelos IA
├── preference_client.py       # Cliente de preferencias usuario
├── requirements.txt           # Dependencias Python
├── run.py                     # Script de inicio
├── README.md                  # Este archivo
├── .streamlit/                # Config Streamlit
│   └── config.toml           # Configuración de tema
└── app_pages/                 # Páginas modularizadas
    ├── __init__.py
    ├── auth.py               # Autenticación
    ├── dashboard.py          # Dashboard principal
    ├── wardrobe.py           # Gestión de guardarropa
    ├── outfits.py            # Combinador de outfits
    ├── edit_item.py          # Edición de prendas
    └── settings.py           # Configuración
```

## 💾 Estructura de Almacenamiento Local

```
~/.fashion_wardrobe_app/
├── images/                    # Imágenes de prendas
│   ├── thumbs/               # Miniaturas (generadas automáticamente)
│   └── original/             # Imágenes originales
│
├── models/                    # Modelos IA descargados
│   ├── persona_model.pt      # Modelo personalizado
│   ├── base_model.pt         # Modelo base
│   ├── manifest.json         # Índice de modelos
│   └── backups/              # Copias de seguridad
│       └── persona_model_backup_2024-12-15.pt
│
├── cache/                     # Datos cacheados
│   ├── embeddings/           # Embeddings de imágenes
│   ├── predictions/          # Predicciones IA
│   └── ui_cache/             # Cache de Streamlit
│
├── data/                      # Base de datos local
│   ├── wardrobe.json         # Índice de prendas
│   ├── outfits.json          # Outfits guardados
│   └── preferences.json      # Preferencias usuario
│
├── config/                    # Configuración
│   └── app_config.json      # Ajustes de la app
│
└── logs/                      # Logs de operaciones
    └── app.log               # Historial de actividades
```

## 🚀 Instalación y Uso

### Requisitos
- Python 3.8+
- pip o conda
- 2GB de espacio libre en disco (recomendado)
- Conexión a internet (para sincronización inicial)

### Instalación

```bash
# 1. Clonar y acceder al directorio
cd frontend

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Ejecutar la aplicación
streamlit run app.py
```

### Configurar Backend Remoto (Opcional)

```bash
# Por defecto usa localhost:8000
# Para cambiar a servidor remoto:

export BACKEND_URL="http://tu-servidor.com:8000"
streamlit run app.py

# O usa la sección de Configuración dentro de la app
```

### Ejecución con Script de Inicio

```bash
# Usa el script incluido
python run.py

# Esto automáticamente:
# - Detecta ambiente Python
# - Instala dependencias si falta
# - Inicia Streamlit
```

## 📡 API Client - Uso Programático

### Autenticación

```python
from api_client import BackendAPIClient

# Inicializar cliente
client = BackendAPIClient()

# Login
success, data = client.login("usuario", "contraseña")
if success:
    print(f"Autenticado como: {data['username']}")
    
# Obtener token
token = client.get_token()

# Logout
success, message = client.logout()
```

### Gestión de Prendas

```python
from pathlib import Path

# Subir prenda con metadatos
image_path = Path("mi_prenda.jpg")
metadata = {
    'name': 'Camisa Azul',
    'main_category': 'Tops',
    'color': 'Blue',
    'brand': 'Nike',
    'size': 'M'
}
success, data = client.add_wardrobe_item(image_path, metadata)

# Obtener todas las prendas
success, items = client.get_wardrobe_items()
for item in items:
    print(f"{item['name']} - {item['main_category']}")

# Obtener prenda específica
success, item = client.get_item(item_id=123)

# Actualizar prenda
success, data = client.update_item(item_id=123, {
    'color': 'Red',
    'notes': 'Favorita'
})

# Eliminar prenda
success, message = client.delete_item(item_id=123)
```

### Generación de Outfits

```python
# Generar outfit automático
success, outfit = client.generate_outfit(
    num_items=3,
    occasion="casual",
    preferences={"preferred_colors": ["blue", "black"]}
)
print(f"Compatibilidad: {outfit['compatibility_score']:.2f}")
print(f"Prendas: {outfit['item_ids']}")

# Guardar outfit favorito
success, data = client.save_outfit(
    item_ids=[1, 5, 10],
    name="Mi outfit favorito",
    occasion="casual"
)

# Obtener outfits guardados
success, outfits = client.get_saved_outfits()
```

### Gestión de Modelos

```python
from model_manager import PersonaModelManager

# Guardar modelo
model_bytes = b'...'  # Bytes del modelo
PersonaModelManager.save_model(model_bytes, "persona_model.pt")

# Cargar modelo
model = PersonaModelManager.load_model("persona_model.pt")

# Verificar integridad
is_valid = PersonaModelManager.verify_model("persona_model.pt")
if not is_valid:
    print("Modelo corrupto, restaurando backup...")
    PersonaModelManager.restore_backup("persona_model.pt")

# Obtener información del modelo
info = PersonaModelManager.get_model_info("persona_model.pt")
print(f"Tamaño: {info['size']} bytes")
print(f"Fecha: {info['timestamp']}")
print(f"SHA-256: {info['checksum']}")

# Hacer backup
backup_path = PersonaModelManager.backup_model("persona_model.pt")
print(f"Backup en: {backup_path}")
```

### Sincronización

```python
from api_client import SyncManager

# Inicializar gestor de sincronización
sync_manager = SyncManager(client)

# Sincronización completa (full sync)
success, message = sync_manager.full_sync()
print(message)  # "Sincronización completada: 10 cambios"

# Sincronización parcial (solo cambios)
success, changes = sync_manager.sync_changes()
print(f"Cambios sincronizados: {len(changes)}")

# Ver estado de sincronización
status = sync_manager.get_sync_status()
print(f"Última sincronización: {status['last_sync']}")
print(f"Cambios pendientes: {status['pending_changes']}")

# Configurar sincronización automática
sync_manager.enable_auto_sync(interval_minutes=5)
```

### Almacenamiento Local

```python
from config import LocalStorage

# Guardar imagen
image_bytes = open("foto.jpg", "rb").read()
success, filename = LocalStorage.save_image(image_bytes, "mi_foto.jpg")

# Cargar imagen
image_data = LocalStorage.load_image("mi_foto.jpg")

# Listar todas las imágenes
images = LocalStorage.list_images()
for img in images:
    print(f"- {img['name']} ({img['size']} bytes)")

# Eliminar imagen
LocalStorage.delete_image("mi_foto.jpg")

# Estadísticas de almacenamiento
stats = LocalStorage.get_storage_stats()
print(f"Total prendas: {stats['images_count']}")
print(f"Espacio usado: {stats['images_size'] / 1024 / 1024:.2f} MB")
print(f"Modelos: {stats['models_count']}")
print(f"Espacio modelos: {stats['models_size'] / 1024 / 1024:.2f} MB")

# Limpiar caché
freed_space = LocalStorage.clear_cache()
print(f"Espacio liberado: {freed_space / 1024 / 1024:.2f} MB")

# Exportar datos (backup)
backup_path = LocalStorage.export_data()
print(f"Datos exportados a: {backup_path}")

# Importar datos (restore)
success = LocalStorage.import_data(backup_path)
```

## ⚙️ Variables de Entorno

```bash
# URL del backend (por defecto: http://localhost:8000)
export BACKEND_URL="http://your-backend:8000"

# Timeout para requests HTTP (por defecto: 30)
export BACKEND_TIMEOUT="30"

# Nivel de logging (por defecto: INFO)
export LOG_LEVEL="DEBUG"

# Directorio de datos locales (por defecto: ~/.fashion_wardrobe_app)
export FASHION_APP_DATA_DIR="/ruta/custom"

# Modo debug (por defecto: False)
export DEBUG_MODE="True"
```

## 🔄 Flujo de Datos

```
┌─────────────────────────────────────┐
│  Usuario interactúa con UI (Streamlit)
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│  Validación en Frontend             │
│  - Formatos corrects                │
│  - Campos requeridos                │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│  Almacenamiento Local               │
│  - Guardar imágenes                 │
│  - Cachear predicciones             │
│  - Sincronizar índices              │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│  API Client (HTTP)                  │
│  - Serializar datos                 │
│  - Enviar al backend                │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│  Backend (FastAPI)                  │
│  - Procesar requests                │
│  - Ejecutar IA si es necesario      │
│  - Guardar en BD                    │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│  Respuesta al Frontend              │
│  - Resultados de IA                 │
│  - Confirmación guardado            │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│  Actualizar UI                      │
│  - Mostrar nuevo contenido          │
│  - Refrescar componentes            │
└─────────────────────────────────────┘
```

## 🔐 Seguridad

- ✅ **Contraseñas**: Encriptadas por el backend
- ✅ **Datos locales**: Almacenados de forma segura
- ✅ **Comunicación**: Soporte HTTPS con backend
- ✅ **Tokens**: JWT para autenticación
- ✅ **Verificación**: Checksums SHA-256 para modelos
- ✅ **Privacidad**: Sin datos enviados sin permiso

## 📊 Rendimiento

| Métrica | Valor |
|---------|-------|
| **Almacenamiento de imágenes** | Ilimitado (depende disco) |
| **Almacenamiento de modelos** | 1-2 GB por modelo |
| **Velocidad de sincronización** | Depende red y tamaño |
| **Tiempo carga UI** | < 2 segundos |
| **Caché automático** | Optimizado automáticamente |
| **Generación de outfits** | < 1 segundo (local) |

## 🐛 Solución de Problemas

### Backend no es alcanzable
```
❌ Error: "No se puede conectar al backend"

Solución:
1. Verifica BACKEND_URL: echo $BACKEND_URL
2. Confirma backend está corriendo: http://localhost:8000/docs
3. Revisa conectividad red: ping tu-servidor.com
4. Comprueba firewall/proxy
```

### Error al descargar modelos
```
❌ Error: "Descarga de modelo fallida"

Solución:
1. Verifica conexión a internet
2. Revisa espacio en disco: df -h
3. Comprueba permisos carpeta: ~/.fashion_wardrobe_app
4. Intenta descarga manual desde Settings
```

### Las imágenes no se sincronizan
```
❌ Error: "Imágenes no sincronizadas"

Solución:
1. Verifica autenticación: ¿sesión activa?
2. Revisa permisos locales de archivos
3. Intenta sincronización manual desde Settings
4. Revisa logs: ~/.fashion_wardrobe_app/logs/app.log
```

### La app se carga lentamente
```
❌ Problema: "Streamlit carga muy lentamente"

Soluciones:
1. Limpia caché: Settings → Limpiar caché
2. Reinicia app: Ctrl+C y streamlit run app.py
3. Reduce imágenes en galería
4. Desactiva auto-sync si la red es lenta
5. Revisa recursos del sistema: top/Task Manager
```

### Modelos no se cargan
```
❌ Error: "No se puede cargar modelo"

Solución:
1. Verifica integridad: Settings → Verificar modelos
2. Restaura backup: Settings → Restaurar backup
3. Reintenta descarga desde Settings
4. Limpia directorio models: rm -rf ~/.fashion_wardrobe_app/models
```

## 🚀 Modo Desarrollo

### Ejecutar con logging debug
```bash
streamlit run app.py --logger.level=debug
```

### Ejecutar con recarga automática
```bash
streamlit run app.py --client.showErrorDetails=true
```

### Conectar a backend desarrollo
```bash
export BACKEND_URL="http://localhost:8000"
export DEBUG_MODE="True"
streamlit run app.py
```

### Limpiar todo y reiniciar
```bash
rm -rf ~/.fashion_wardrobe_app
streamlit run app.py
```

## 📦 Dependencias Principales

```
streamlit>=1.28.0              # Framework UI
streamlit-option-menu>=0.3.2  # Menú navegación
requests>=2.31.0              # Cliente HTTP
Pillow>=10.0.0                # Procesamiento imágenes
numpy>=1.24.0                 # Computación numérica
torch>=2.0.0                  # Deep Learning
```

Ver `requirements.txt` para lista completa.

## 📱 Interfaz de Usuario

### Tema y Estilos
- 🎨 **Tema Streamlit**: Configurable (claro/oscuro)
- 📐 **Layout**: Wide (óptimo para pantallas grandes)
- ⚡ **Responsive**: Funciona en desktop y tablet
- 🎯 **Navegación**: Menú lateral con opción_menu
- 📊 **Componentes**: Tarjetas, gráficos, tablas

### Elementos Visuales
- 🏷️ **Badges**: Para categorías y etiquetas
- 📈 **Gráficos**: Matplotlib y Plotly
- 🖼️ **Galerías**: Con miniaturas optimizadas
- 🎯 **Métricos**: Estadísticas en tarjetas
- ⚠️ **Mensajes**: Success, error, info

## 🔗 Integración con Backend

### Endpoints Usados

```
POST   /auth/login              # Autenticación
POST   /auth/register           # Registro
GET    /wardrobe/items          # Obtener prendas
POST   /wardrobe/items          # Crear prenda
PUT    /wardrobe/items/{id}     # Actualizar prenda
DELETE /wardrobe/items/{id}     # Eliminar prenda
POST   /outfits/generate        # Generar outfit
GET    /outfits/saved           # Obtener guardados
POST   /models/download         # Descargar modelo
GET    /sync/status             # Estado sincronización
```

Ver `app/DOCS/API_Routes.md` para documentación completa.

## 💡 Tips y Trucos

### Para usuarios
- 💾 **Haz backup regularmente**: Settings → Exportar datos
- 🔍 **Usa búsqueda avanzada**: Filtra por múltiples criterios
- ❤️ **Marca favoritos**: Acceso rápido a prendas especiales
- 🔄 **Sincroniza frecuentemente**: Mantén datos actualizados
- 📊 **Revisa estadísticas**: Dashboard te muestra tendencias

### Para desarrolladores
- 🐍 **Modularización**: Las páginas son componentes independientes
- 🔌 **Extensible**: Fácil agregar nuevas páginas
- 📝 **Type hints**: Código bien tipado
- 🧪 **Testeable**: Funciones sin side-effects
- 🔄 **State management**: Streamlit session_state

## 📄 Licencia

Este proyecto es parte del Fashion Wardrobe Management System.

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor:
1. Fork el repositorio
2. Crea una rama para tu feature
3. Commit con mensajes descriptivos
4. Push a la rama
5. Abre un Pull Request

## 💬 Soporte

Para problemas, sugerencias o contacto:
- 📧 Email: support@fashionwardrobe.com
- 🐛 Issues: Abre un issue en GitHub
- 💬 Discussions: Participa en discusiones
- 📞 Contacto: [Formulario de contacto]

---

**Versión:** 1.0.0  
**Última actualización:** Diciembre 2024  
**Mantenedor:** Fashion Tech Team
