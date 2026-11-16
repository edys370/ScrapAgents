# Obscura TLS Trust Extras / Certificados Extra para Obscura

[![Language: ES](https://img.shields.io/badge/Language-Espa%C3%B1ol-yellow.svg)](#español)
[![Language: EN](https://img.shields.io/badge/Language-English-blue.svg)](#english)

---

## Español

Obscura `0.2.6` **no cuenta con un flag** para ignorar errores de certificados HTTPS: su cliente HTTP interno está compilado con `danger_accept_invalid_certs(false)`. La opción `ignore_https_errors=True` de Playwright solo afecta a contextos locales de Chromium; sobre CDP el handshake TLS lo realiza Obscura.

### Solución Oficial Soportada
Agregar las CAs faltantes mediante `SSL_CERT_FILE` / `SSL_CERT_DIR`.

La carpeta `certs/extra/` contiene los certificados intermedios y raíces de Sectigo que `www.caf.com` no envía en su cadena (ver `ingestions/caf/discovery.md`). El archivo `docker-compose.yml` monta dicho directorio como `SSL_CERT_DIR=/etc/obscura/extra-cas` y conserva el `SSL_CERT_FILE` predeterminado de la imagen.

---

## English

Obscura `0.2.6` has **no flag** to ignore HTTPS certificate errors: its HTTP client is built with `danger_accept_invalid_certs(false)`. Playwright's `ignore_https_errors=True` only affects a local Chromium context; over CDP the TLS handshake is performed by Obscura.

### Official Supported Solution
Add missing intermediate CA(s) via `SSL_CERT_FILE` / `SSL_CERT_DIR`.

`certs/extra/` holds the Sectigo intermediates/roots that `www.caf.com` does not send in its chain (see `ingestions/caf/discovery.md`). `docker-compose.yml` mounts that directory as `SSL_CERT_DIR=/etc/obscura/extra-cas` and preserves the image's default `SSL_CERT_FILE`.
