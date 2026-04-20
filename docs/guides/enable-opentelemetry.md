## Contexte
Le boilerplate est “OTel-ready” : `request_id` + parsing `traceparent` existent déjà.

## Étapes (V2)
1. Ajouter `opentelemetry-sdk` + exporters
2. Remplacer/étendre `app/core/middleware/logging.py` pour créer spans
3. Conserver les champs de logs `trace_id` / `span_id` pour compat dashboards

