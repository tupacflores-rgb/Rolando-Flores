# Etapa 2 — Voz, fotos y tablet

**Herramientas:** adaptador HTTP/local de simulador, transcriptor local,
Pydantic y FastAPI.

**Conceptos:** structured output, timestamp de observación, resolución de
alias, normalización de unidades, ambigüedad, confirmación humana y
idempotencia.

`app/integrations.py` separa la descarga y transcripción de la lógica del
dominio. `VoicePartExtractor` convierte una nota en `FilaParte`; conserva la
hora de la nota, vincula fotos, resuelve los aliases de `datos/planta.yaml`,
normaliza kg/cm², psi y bar, y rechaza nombres ambiguos. Los fixtures locales
permiten probar sin inventar un modelo cerrado. Las notas y audios del
simulador oficial llegan por `planta/recorridas`; el sistema debe descargar
`audio_url` y las fotos antes de transcribir.

**Verificación:** construir un `VoiceNote`, pasar texto al extractor y validar
que cada fila use `observed_at` de la nota; una corrección de tablet no confirma
silenciosamente el parte.
