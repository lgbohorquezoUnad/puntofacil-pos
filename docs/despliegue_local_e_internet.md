# Despliegue local e internet de PuntoFacil POS

## Estado actual del proyecto

El proyecto ya trae parte de la configuracion para despliegue:

- `backend/app.py` sirve la API y tambien las vistas HTML cuando se trabaja en local.
- `render.yaml` ya deja listo el backend para Render.
- `netlify.toml` fue ajustado para que Netlify abra rutas amigables como `/login`, `/admin`, `/pos`, `/inventory` y `/operativa`.
- `frontend/static/js/config.js` ya detecta si la app corre en local o desde Netlify/Render.
- `backend/config.py` ahora detecta automaticamente el puerto configurado en XAMPP si no defines `MYSQL_PORT` manualmente.

## 1. Despliegue local

### Requisitos

Necesitas tener instalado o disponible:

- Python con el entorno virtual del proyecto.
- MySQL o MariaDB. En este equipo se detecto XAMPP en `C:\xampp`.
- La base de datos `puntofacil_pos`.

### Hallazgo importante en este equipo

Durante la validacion local se detecto que MariaDB normal se cae al iniciar por un problema interno de tablas de permisos. Para no tocar tus datos de la aplicacion, se dejo una ruta segura de prueba local usando un modo temporal de recuperacion.

### Scripts creados para ayudarte

- `start_mysql_recovery.ps1`: inicia MariaDB en modo temporal de recuperacion sobre el puerto `3307`.
- `start_local.ps1`: detecta el puerto de MySQL/XAMPP y arranca el backend Flask.

### Forma recomendada de probar en local

1. Abre PowerShell en la raiz del proyecto.
2. Ejecuta:

```powershell
.\start_mysql_recovery.ps1
```

3. En otra ventana de PowerShell ejecuta:

```powershell
.\start_local.ps1
```

4. Abre en el navegador:

```text
http://127.0.0.1:5000/login
```

### Validacion realizada

Se confirmo localmente que:

- `http://127.0.0.1:5000/login` responde `200`.
- `POST /api/login` funciona con el usuario administrador.
- `GET /api/products` devuelve productos reales desde la base de datos.

### Usuario de prueba sugerido

En `database/migration_users.sql` aparece un usuario inicial:

- correo: `admin@puntofacil.com`
- clave: `admin123`

### Nota sobre la base de datos

En `database/` no aparece el script base de tablas como `productos` o `categorias`, pero en este equipo la base `puntofacil_pos` ya existe y contiene datos. Si en otro equipo esa base no existe, primero deberas restaurarla o crear el esquema base completo antes de probar.

## 2. Despliegue por internet

La separacion recomendada es esta:

- Backend: Render
- Frontend: Netlify
- Base de datos: MySQL accesible desde Render

### Backend en Render

El archivo `render.yaml` ya define:

- runtime Python
- directorio `backend`
- instalacion con `pip install -r requirements.txt`
- arranque con `gunicorn app:app`

### Variables que debes configurar en Render

Agrega estas variables en el panel del servicio:

- `MYSQL_HOST`
- `MYSQL_PORT`
- `MYSQL_USER`
- `MYSQL_PASSWORD`
- `MYSQL_DB`
- `FRONTEND_URL`

Recomendacion:

- En `FRONTEND_URL` coloca exactamente la URL publica de Netlify.
- Ejemplo: `https://tu-proyecto.netlify.app`

### Frontend en Netlify

El archivo `netlify.toml` ya queda listo para publicar la carpeta `frontend` y resolver estas rutas:

- `/`
- `/login`
- `/pos`
- `/admin`
- `/inventory`
- `/operativa`

### Flujo recomendado para publicar

1. Sube el proyecto a GitHub.
2. Conecta el repositorio en Render para el backend.
3. Conecta el mismo repositorio en Netlify para el frontend.
4. En Render configura las variables de entorno del backend.
5. Una vez tengas la URL final del frontend, copiala en `FRONTEND_URL` dentro de Render.
6. Publica Netlify usando como carpeta de salida `frontend`.
7. Prueba el login desde la URL publica de Netlify.

## 3. Pruebas que debes hacer

### Pruebas locales

- Abrir `http://127.0.0.1:5000/login`
- Iniciar sesion con admin
- Consultar productos
- Abrir caja
- Registrar una venta
- Entrar a admin
- Entrar a inventario
- Entrar a operativa

### Pruebas por internet

- Abrir la URL de Netlify
- Confirmar que `/login` cargue correctamente
- Iniciar sesion sin error CORS
- Verificar que las pantallas consuman el backend de Render
- Validar que no haya errores 401, 403 ni 500

## 4. Posibles bloqueos conocidos

### MariaDB local con fallo interno

Si MariaDB normal vuelve a caerse, usa `start_mysql_recovery.ps1` para pruebas locales sin tocar datos de la app.

### Base de datos incompleta en otro equipo

Si faltan tablas como `productos` o `categorias`, necesitaras el esquema base original antes de probar.

### CORS en internet

Si el frontend publica en Netlify pero el backend rechaza peticiones, revisa `FRONTEND_URL` en Render.

### URL del backend incorrecta

`frontend/static/js/config.js` ya intenta detectar la API automaticamente, pero si cambias de servicio puedes ajustar ese archivo o pasar `?api_base_url=...` manualmente.
