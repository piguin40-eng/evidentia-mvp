# Evidentia en movil

## Estado actual

Evidentia funciona como PWA instalable:

- `manifest.webmanifest` con modo `standalone`.
- Service worker para shell basica.
- Iconos PNG 192 y 512 para iOS/Android.
- HTTPS estable por Render para curso y piloto.
- HTTPS temporal por Cloudflare Tunnel solo para emergencia local.
- Login basico opcional para no exponer datos.

## Acceso estable activo

- URL: `https://evidentia-ytra.onrender.com`
- Usuario: no registrar aqui si cambia por piloto.
- Clave: no registrarla en este runbook. Debe vivir solo en entorno local/tunnel activo o gestor seguro.

Nota: las URLs `trycloudflare.com` son temporales y cambian al reiniciar el tunel. No deben mandarse a cursillistas. Para curso, piloto o venta usar Render estable o dominio propio.
No copiar credenciales reales en memoria, guias, capturas, mensajes de estado ni reportes de QA.

## Instalar en iPhone

1. Abrir la URL HTTPS de Evidentia en Safari.
2. Introducir usuario y clave.
3. Pulsar Compartir.
4. Elegir `Añadir a pantalla de inicio`.
5. Abrir Evidentia desde el icono.

## Instalar en Android

1. Abrir la URL HTTPS de Evidentia en Chrome.
2. Introducir usuario y clave.
3. Pulsar menu.
4. Elegir `Instalar app` o `Añadir a pantalla de inicio`.

## Producto comercial

La PWA sirve para piloto y venta inicial si el servidor es estable. Para venderlo como app de mercado con mas confianza:

1. Dominio propio y HTTPS permanente.
2. Cloudflare Access o login propio robusto.
3. Backups automaticos.
4. Monitorizacion uptime.
5. App nativa con Capacitor si se quiere publicar en App Store / Play Store.

No vender ni entregar un tunnel temporal como producto final.

## Puerta de seguridad movil

Antes de entregar una URL movil nueva:

1. Confirmar que la URL entregada no es `trycloudflare.com` salvo emergencia explicita.
2. Probar login correcto e incorrecto sin escribir la clave real en logs/reportes.
3. Verificar que `/api/health` no queda abierto sin sesion.
4. Confirmar manifest, iconos y service worker desde HTTPS.
5. Registrar solo usuario, modo de auth, timestamp y resultado PASS/BLOCKED.
