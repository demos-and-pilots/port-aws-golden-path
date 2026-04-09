# Port Artifacts — CI/CD Self-Service para Lambda

Artefactos completos para implementar un portal de self-service de desarrollo en [Port](https://getport.io), integrando GitHub, GitHub Actions y AWS Lambda.

---

## Estructura de archivos

```
port-artifacts/
├── blueprints/
│   ├── squad.json                   # Entidad: equipo de desarrollo
│   ├── github-repository.json       # Entidad: repositorio GitHub
│   ├── ci-pipeline.json             # Entidad: pipeline de CI
│   ├── cd-pipeline.json             # Entidad: pipeline de CD
│   └── lambda-function.json         # Entidad: función Lambda
│
├── actions/
│   ├── create-github-repository.json     # Acción: crear repositorio
│   ├── provision-lambda-service.json     # Acción: provisionar servicio completo (Day 0)
│   ├── deploy-lambda.json                # Acción: desplegar Lambda (Day 2)
│   └── rollback-lambda.json              # Acción: rollback de Lambda (Day 2)
│
├── scorecards/
│   └── cicd-readiness.json          # Scorecard: madurez CI/CD (4 niveles)
│
└── workflows/                       # GitHub Actions (repo: port-actions)
    ├── create-github-repository.yml      # Ejecutor de la acción crear repositorio
    ├── provision-lambda-service.yml      # Orquestador de aprovisionamiento completo
    ├── rollback-lambda.yml               # Ejecutor de rollback
    └── port-sync-lambda-entities.yml     # Sync periódico (cada 15 min)
```

---

## Orden de instalación en Port

### 1. Blueprints (en este orden por dependencias)

Ir a **Builder → Blueprints → Add blueprint → Paste JSON**:

1. `blueprints/squad.json`
2. `blueprints/github-repository.json`
3. `blueprints/ci-pipeline.json`
4. `blueprints/cd-pipeline.json`
5. `blueprints/lambda-function.json`

### 2. Scorecard

Ir al blueprint `lambdaFunction → Scorecards → Add scorecard → Paste JSON`:

- `scorecards/cicd-readiness.json`

### 3. Self-Service Actions

Ir a **Self-Service → Add action → Paste JSON**:

1. `actions/provision-lambda-service.json` *(acción principal Day 0)*
2. `actions/create-github-repository.json` *(solo repositorio)*
3. `actions/deploy-lambda.json` *(Day 2 — despliegue manual)*
4. `actions/rollback-lambda.json` *(Day 2 — rollback de emergencia)*

### 4. Workflows en GitHub

Crear un repositorio `port-actions` en tu organización y agregar los workflows:

```
port-actions/
└── .github/
    └── workflows/
        ├── create-github-repository.yml
        ├── provision-lambda-service.yml
        ├── rollback-lambda.yml
        └── port-sync-lambda-entities.yml
```

---

## Secrets y variables requeridas

### En GitHub (repo `port-actions`)

| Secret / Variable | Descripción |
|---|---|
| `PORT_CLIENT_ID` | Client ID de Port (Settings → Credentials) |
| `PORT_CLIENT_SECRET` | Client Secret de Port |
| `GH_ORG_TOKEN` | PAT con permisos `repo`, `admin:org` |
| `GITHUB_ORG` | Nombre de la organización en GitHub |
| `SLACK_WEBHOOK_URL` | Webhook de Slack para notificaciones |
| `AWS_ROLE_PLATFORM` | ARN del role IAM de platform engineering |
| `AWS_ACCOUNT_ID_DEV` | Account ID de la cuenta dev |
| `LAMBDA_EXECUTION_ROLE_ARN` | ARN del role de ejecución base de Lambda |

### Variables por ambiente (GitHub Environments)

Configurar en cada ambiente (`dev`, `staging`, `production`):

| Variable | Ejemplo |
|---|---|
| `AWS_ROLE_DEV` | `arn:aws:iam::123456789:role/github-actions-...` |
| `AWS_ROLE_STAGING` | `arn:aws:iam::987654321:role/github-actions-...` |
| `AWS_ROLE_PRODUCTION` | `arn:aws:iam::111222333:role/github-actions-...` |
| `AWS_REGION` | `us-east-1` |

---

## Modelo de entidades y relaciones

```
squad
  └── githubRepository (many)
        ├── ciPipeline (1:1)
        ├── cdPipeline (1:1)
        └── lambdaFunction (many)
```

---

## Scorecard CI/CD Readiness — niveles

| Nivel | Color | Criterios |
|---|---|---|
| Básico | Rojo | Tiene repo, CI pipeline, CD pipeline |
| Estándar | Amarillo | Deploy exitoso, OIDC activo, Secrets configurados, datos clasificados |
| Avanzado | Azul | CI >90% success, cobertura >=80%, SAST activo, error rate <1% |
| Excelente | Verde | Canary deploy, rollback automático, MTTD <15min, MTTR <30min |

---

## Flujo de aprovisionamiento (acción principal)

La acción `provision-lambda-service` ejecuta 4 pasos en secuencia:

```
[1/4] Crear repo GitHub (template + branch protection + CODEOWNERS)
      ↓
[2/4] Crear IAM Role con OIDC (trust policy por repo específico)
      ↓
[3/4] Crear Lambda stub en dev (con alias 'live' y CloudWatch Logs)
      ↓
[4/4] Registrar entidades en Port (repo + lambda con todas sus relaciones)
```

Tiempo estimado: **5–8 minutos** por servicio.

---

## Acción de rollback — cómo funciona

1. Obtiene la versión actual del alias `live`
2. Lista todas las versiones publicadas y encuentra la inmediata anterior
3. Apunta el alias `live` a la versión anterior
4. Verifica que el alias apunta correctamente
5. Notifica en Slack y actualiza Port
6. Si falla: actualiza Port con estado `FAILURE` para visibilidad inmediata

---

## Sync periódico de entidades

El workflow `port-sync-lambda-entities.yml` se ejecuta cada 15 minutos y sincroniza:

- Métricas de CloudWatch (invocaciones, error rate, duración promedio)
- Metadata de repos GitHub (último push)

Para sincronizar también staging y prod, duplicar el job `sync-dev` cambiando el environment y el AWS role.
