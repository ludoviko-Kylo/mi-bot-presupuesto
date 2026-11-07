// =============================================================================
// Configuración de Conexión API para Despliegue en la Nube y Multidispositivo
// =============================================================================
//
// Soporta variables de entorno comunes de Vite, Create React App y configuraciones estáticas:
// - VITE_API_URL (Vite / Vercel)
// - REACT_APP_API_URL (Create React App)
// - window.ENV_API_URL (Inyecciones de contenedor o script)
//
// Reglas:
// 1. Si la interfaz web está alojada en el mismo servidor backend (Render/Railway),
//    deja API_URL en "" (cadena vacía) para usar URLs relativas automáticamente.
// 2. Si la interfaz web está en GitHub Pages, Vercel, Netlify o abres index.html en tu móvil,
//    asigna aquí la URL pública de tu backend en Render/Railway:
//    Ejemplo: API_URL: "https://mi-bot-presupuesto.onrender.com"
// 3. También puedes cambiar la URL en cualquier momento desde el botón de la barra superior.

window.APP_CONFIG = {
  API_URL: (
    (typeof window !== "undefined" && window.VITE_API_URL) ||
    (typeof window !== "undefined" && window.REACT_APP_API_URL) ||
    (typeof window !== "undefined" && window.ENV_API_URL) ||
    ""
  )
};

