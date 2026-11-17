# Contexto de Scraping y Negocio / Project Scraping Context (`Contex.md`)

<!--
================================================================================
INSTRUCCIONES PARA EL USUARIO / INSTRUCTIONS FOR USERS:
================================================================================
Este archivo sirve como la FUENTE CANÓNICA de contexto para tu proyecto de scraping.
Cuando una persona clona este repositorio, debe ajustar este archivo definiendo qué 
desea scrapear según sus propias necesidades y objetivos de negocio.

Los agentes de diseño (source-scout, source-assessor, silver-designer) consultarán
este documento para saber qué buscar, qué extraer y qué excluir al procesar cualquier
enlace (URL) que les pases.
================================================================================
-->

## 1. Propósito de Negocio / Business Purpose
<!--
Describe el objetivo general de tu proyecto de scraping.
Ejemplo: "Plataforma analítica para monitorear licitaciones públicas de tecnología en América Latina."
-->


## 2. Criterios de Inclusión (En-Scope: Lo que SÍ se debe buscar)
<!--
Define qué entidades, registros o secciones son de interés.
Ejemplo:
- Convocatorias abiertas y activas de financiamiento.
- Becas de movilidad internacional para posgrado.
- Licitaciones de consultoría técnica especializada.
-->


### Atributos Clave Requeridos en el Esquema / Target Contract Fields
<!--
Define los campos que esperas extraer y normalizar de cada registro.
-->
| Campo Canónico | Tipo | Descripción | Obligatorio |
| :--- | :---: | :--- | :---: |
| `id` | `string` | Identificador único del registro en la fuente | **Sí (PK)** |
| `title` | `string` | Título formal de la oportunidad/registro | **Sí** |
| `publish_date` | `date` | Fecha de publicación (`YYYY-MM-DD`) | **Sí** |
| `source_url` | `string` | Enlace permanente hacia el registro | **Sí** |
| `description` | `string` | Resumen o texto descriptivo principal | Recomendado |


## 3. Criterios de Exclusión (Out-of-Scope: Lo que se DEBE IGNORAR)
<!--
Indica explícitamente qué tipo de contenido o secciones deben descartarse.
Ejemplo:
- Compras rutinarias de suministros de oficina (tóner, papel).
- Comunicados de prensa o noticias informativas sin convocatoria formal.
- Formularios transaccionales protegidos por login.
- Secciones de trámites burocráticos internos.
-->
