# Port AWS Golden Path

Golden Path de **Platform Engineering** para desplegar recursos AWS via CloudFormation desde Port IDP.  
El DevOps Engineer llena un formulario en Port → GitHub Actions despliega el template → el recurso queda registrado en el catálogo automáticamente.

---

## Estructura del proyecto

```
port-aws-golden-path/
├── port/
│   ├── blueprints/
│   │   └── aws_resource_blueprint.json      ← Blueprint en Port
│   └── actions/
│       ├── action_vpc.json                  ← Self-service action: VPC
│       ├── action_dynamodb.json             ← Self-service action: DynamoDB
│       ├── action_lambda.json               ← Self-service action: Lambda
│       └── action_complete_stack.json       ← Self-service action: Stack completo
├── github/
│   └── workflows/
│       └── deploy-aws-resource.yml          ← Workflow orquestador
└── cloudformation/
    ├── vpc/
    │   └── vpc.yml                          ← Template VPC
    ├── dynamodb/
    │   └── dynamodb.yml                     ← Template DynamoDB
    ├── lambda/
    │   └── lambda.yml                       ← Template Lambda en VPC
    └── complete/
        └── complete-stack.yml               ← Template Stack completo
```

---

## Setup — 4 pasos

### 1. Crear el repositorio en GitHub

```bash
gh repo create TU_ORG/port-aws-golden-path --public
git clone https://github.com/TU_ORG/port-aws-golden-path
# Copiar todos los archivos y hacer push
```

Mover el workflow a la ruta correcta:
```bash
mkdir -p .github/workflows
cp github/workflows/deploy-aws-resource.yml .github/workflows/
git add . && git commit -m "feat: Port AWS Golden Path" && git push
```

### 2. Configurar secretos en GitHub (nivel organización)

Ir a: `github.com/organizations/TU_ORG/settings/secrets/actions`

| Secreto | Descripción |
|---------|-------------|
| `PORT_CLIENT_ID` | Settings → Credentials en Port |
| `PORT_CLIENT_SECRET` | Settings → Credentials en Port |

Para autenticación AWS, dos opciones:

**Opción A — OIDC (recomendada, sin access keys):**
1. Crear un IAM Role `GitHubActionsDeployRole` en cada cuenta AWS destino
2. El Role debe tener permisos de CloudFormation, VPC, DynamoDB, Lambda, IAM y S3
3. Trust policy debe permitir `token.actions.githubusercontent.com` como OIDC provider

**Opción B — Access Keys (más simple para empezar):**

| Secreto | Descripción |
|---------|-------------|
| `AWS_ACCESS_KEY_ID` | Access key del usuario IAM de despliegue |
| `AWS_SECRET_ACCESS_KEY` | Secret key del usuario IAM |

Si usas la Opción B, descomenta el bloque de credenciales en el workflow y comenta el de OIDC.

### 3. Configurar Port

#### 3a. Crear el Blueprint
1. Port → Builder → Blueprints → + Add Blueprint → Edit as JSON
2. Pegar el contenido de `port/blueprints/aws_resource_blueprint.json`
3. Guardar

#### 3b. Crear las Self-service Actions
Para cada archivo en `port/actions/`:
1. Self-service → + New Action → Edit as JSON
2. Pegar el contenido del archivo
3. Reemplazar `TU_ORG_GITHUB` con el nombre real de tu organización
4. Guardar

### 4. Verificar permisos IAM mínimos

El usuario/rol de AWS usado por GitHub Actions necesita permisos para:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "cloudformation:*",
        "ec2:*",
        "dynamodb:*",
        "lambda:*",
        "iam:CreateRole", "iam:AttachRolePolicy", "iam:PutRolePolicy",
        "iam:GetRole", "iam:PassRole", "iam:CreatePolicy",
        "iam:CreateInstanceProfile", "iam:AddRoleToInstanceProfile",
        "s3:GetObject", "s3:GetObjectVersion",
        "logs:CreateLogGroup", "logs:PutRetentionPolicy",
        "sqs:CreateQueue", "sqs:GetQueueAttributes",
        "xray:PutTraceSegments"
      ],
      "Resource": "*"
    }
  ]
}
```

---

## Uso

### Desde Port

1. Ir a **Self-service** en Port
2. Elegir la acción deseada:
   - **Desplegar VPC en AWS** — solo red
   - **Desplegar DynamoDB en AWS** — solo base de datos
   - **Desplegar Lambda Function en AWS** — solo función (necesita VPC existente)
   - **Desplegar Stack Completo AWS** — VPC + DynamoDB + Lambda integradas
3. Llenar el formulario con Account ID, región, AZ, nombre del proyecto
4. Ejecutar — en ~5 minutos el recurso está creado y registrado en el catálogo

### Desde la CLI de AWS (sin Port)

Si quieres probar los templates directamente:

```bash
# VPC
aws cloudformation deploy \
  --template-file cloudformation/vpc/vpc.yml \
  --stack-name mi-proyecto-dev-vpc \
  --region us-east-1 \
  --capabilities CAPABILITY_IAM \
  --parameter-overrides \
    ProjectName=mi-proyecto \
    Environment=dev \
    VpcCidr=10.0.0.0/16 \
    AvailabilityZone1=us-east-1a \
    AvailabilityZone2=us-east-1b \
    EnableNatGateway=false

# DynamoDB
aws cloudformation deploy \
  --template-file cloudformation/dynamodb/dynamodb.yml \
  --stack-name mi-proyecto-dev-dynamo \
  --region us-east-1 \
  --capabilities CAPABILITY_IAM \
  --parameter-overrides \
    ProjectName=mi-proyecto \
    Environment=dev \
    PartitionKey=id \
    PartitionKeyType=S \
    BillingMode=PAY_PER_REQUEST \
    EnablePitr=true \
    EnableTtl=false

# Stack completo
aws cloudformation deploy \
  --template-file cloudformation/complete/complete-stack.yml \
  --stack-name mi-proyecto-dev-complete \
  --region us-east-1 \
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
  --parameter-overrides \
    ProjectName=mi-proyecto \
    Environment=dev \
    VpcCidr=10.0.0.0/16 \
    AvailabilityZone1=us-east-1a \
    AvailabilityZone2=us-east-1b \
    EnableNatGateway=false \
    DynamoPartitionKey=id \
    EnablePitr=true \
    LambdaRuntime=python3.12 \
    LambdaHandler=lambda_function.lambda_handler \
    LambdaMemorySize=256 \
    LambdaTimeout=30 \
    S3Bucket=mi-bucket-codigo \
    S3Key=releases/function.zip
```

---

## Lo que crea cada template

### VPC (`vpc.yml`)
- VPC con el CIDR configurado
- 2 subnets públicas (una por AZ)
- 2 subnets privadas (una por AZ)
- Internet Gateway + attachment
- NAT Gateway + Elastic IP (opcional)
- Tablas de ruteo públicas y privadas
- Security Group base para la VPC
- Exports con todos los IDs para usar en otros stacks

### DynamoDB (`dynamodb.yml`)
- Tabla DynamoDB con Partition Key (y Sort Key opcional)
- Modo On-Demand o Provisioned según el parámetro
- Point-in-Time Recovery configurable
- TTL configurable
- Encriptación SSE activada
- DynamoDB Streams habilitados (para Lambdas reactivas)
- IAM Managed Policy de acceso CRUD exportada
- `DeletionPolicy: Retain` para proteger datos en producción

### Lambda (`lambda.yml`)
- Lambda Function con el runtime y handler configurados
- IAM Role con permisos mínimos (VPC, S3, X-Ray)
- Security Group propio dentro de la VPC
- Dead-Letter Queue en SQS (opcional)
- Log Group en CloudWatch con retención configurada
- X-Ray Tracing habilitado
- Variables de entorno del sistema (ENVIRONMENT, PROJECT_NAME)

### Stack Completo (`complete-stack.yml`)
Todo lo anterior más:
- **VPC Endpoint para DynamoDB** — el tráfico entre Lambda y DynamoDB nunca sale a internet (más seguro y sin costo de NAT)
- Variable de entorno `DYNAMO_TABLE` inyectada automáticamente en la Lambda
- IAM Role con permisos de DynamoDB ya configurados en la Lambda
- Toda la red, base de datos y función en un único stack coherente
