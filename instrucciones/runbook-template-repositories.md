# Runbook: Creación de Repositorios Template

## Propósito

Guía para crear los tres repositorios base (template) que usa el workflow automatizado de Port
para bootstrapear nuevos servicios. Cada repo incluye estructura de proyecto, pipeline CI y
pipeline CD listo para AWS Lambda.

## Repositorios a crear

| Nombre | Stack | Variable en workflow |
|---|---|---|
| `lambda-python-template` | Python 3.12 | `python3.12` |
| `lambda-nodejs-template` | Node.js 20.x | `nodejs20.x` |
| `lambda-java-template` | Java 21 | `java21` |

---

## Prerequisitos

- Acceso de Owner/Admin a la organización GitHub
- AWS IAM Role con permisos para `lambda:UpdateFunctionCode` y `lambda:GetFunction`
- OIDC configurado entre GitHub Actions y AWS (ver sección de secrets)

---

## Secrets requeridos en cada template repo

Configurar a nivel de organización (heredados por todos los repos):

| Secret | Descripción |
|---|---|
| `AWS_ROLE_ARN` | ARN del IAM Role con permisos Lambda |

Configurar como variable de repo (o de organización):

| Variable | Descripción |
|---|---|
| `AWS_REGION` | Región AWS (ej. `us-east-1`) |
| `LAMBDA_FUNCTION_NAME` | Nombre de la función Lambda a desplegar |

---

## Pasos comunes para cada template repo

1. Crear el repo en la organización (vacío, sin README)
2. Clonar localmente y crear la estructura de archivos indicada
3. Hacer push a `main`
4. En **Settings → General → Template repository** → activar checkbox
5. Verificar que aparece la etiqueta `Template` en la página del repo

---

## 1. `lambda-python-template`

### Estructura de archivos

```
lambda-python-template/
├── .github/
│   └── workflows/
│       ├── ci.yml
│       └── cd.yml
├── src/
│   └── handler.py
├── tests/
│   └── test_handler.py
├── requirements.txt
├── requirements-dev.txt
├── .gitignore
└── README.md
```

### `.github/workflows/ci.yml`

```yaml
name: ci

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install ruff
      - run: ruff check src/

  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -r requirements.txt -r requirements-dev.txt
      - run: pytest tests/ -v --tb=short

  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install bandit safety
      - run: bandit -r src/ -ll
      - run: safety check -r requirements.txt
```

### `.github/workflows/cd.yml`

```yaml
name: cd

on:
  push:
    branches: [main]

permissions:
  id-token: write
  contents: read

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
          aws-region: ${{ vars.AWS_REGION }}

      - name: Install dependencies
        run: pip install -r requirements.txt -t package/

      - name: Package Lambda
        run: |
          cp -r src/* package/
          cd package && zip -r ../function.zip .

      - name: Deploy to Lambda
        run: |
          aws lambda update-function-code \
            --function-name ${{ vars.LAMBDA_FUNCTION_NAME }} \
            --zip-file fileb://function.zip
```

### `src/handler.py`

```python
import json


def lambda_handler(event, context):
    return {
        "statusCode": 200,
        "body": json.dumps({"message": "Hello from Lambda"}),
    }
```

### `tests/test_handler.py`

```python
from src.handler import lambda_handler


def test_lambda_handler_returns_200():
    result = lambda_handler({}, {})
    assert result["statusCode"] == 200
```

### `requirements.txt`

```
# Agrega aquí las dependencias de producción
```

### `requirements-dev.txt`

```
pytest==8.3.3
bandit==1.8.0
safety==3.2.9
ruff==0.7.0
```

### `.gitignore`

```
__pycache__/
*.pyc
*.pyo
.env
.venv
venv/
dist/
package/
function.zip
.pytest_cache/
```

---

## 2. `lambda-nodejs-template`

### Estructura de archivos

```
lambda-nodejs-template/
├── .github/
│   └── workflows/
│       ├── ci.yml
│       └── cd.yml
├── src/
│   └── handler.js
├── tests/
│   └── handler.test.js
├── package.json
├── .eslintrc.json
├── .gitignore
└── README.md
```

### `.github/workflows/ci.yml`

```yaml
name: ci

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: "npm"
      - run: npm ci
      - run: npm run lint

  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: "npm"
      - run: npm ci
      - run: npm test

  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: "npm"
      - run: npm ci
      - run: npm audit --audit-level=high
```

### `.github/workflows/cd.yml`

```yaml
name: cd

on:
  push:
    branches: [main]

permissions:
  id-token: write
  contents: read

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: "npm"

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
          aws-region: ${{ vars.AWS_REGION }}

      - name: Install production dependencies
        run: npm ci --omit=dev

      - name: Package Lambda
        run: zip -r function.zip src/ node_modules/

      - name: Deploy to Lambda
        run: |
          aws lambda update-function-code \
            --function-name ${{ vars.LAMBDA_FUNCTION_NAME }} \
            --zip-file fileb://function.zip
```

### `src/handler.js`

```javascript
exports.handler = async (event) => {
  return {
    statusCode: 200,
    body: JSON.stringify({ message: "Hello from Lambda" }),
  };
};
```

### `tests/handler.test.js`

```javascript
const { handler } = require("../src/handler");

test("returns 200 status code", async () => {
  const result = await handler({});
  expect(result.statusCode).toBe(200);
});
```

### `package.json`

```json
{
  "name": "lambda-nodejs-template",
  "version": "1.0.0",
  "description": "AWS Lambda Node.js template",
  "main": "src/handler.js",
  "scripts": {
    "test": "jest",
    "lint": "eslint src/"
  },
  "devDependencies": {
    "eslint": "^9.0.0",
    "jest": "^29.0.0"
  }
}
```

### `.eslintrc.json`

```json
{
  "env": { "node": true, "es2022": true },
  "rules": {
    "no-unused-vars": "error",
    "no-console": "warn"
  }
}
```

### `.gitignore`

```
node_modules/
dist/
function.zip
.env
coverage/
```

---

## 3. `lambda-java-template`

### Estructura de archivos

```
lambda-java-template/
├── .github/
│   └── workflows/
│       ├── ci.yml
│       └── cd.yml
├── src/
│   ├── main/java/com/example/
│   │   └── Handler.java
│   └── test/java/com/example/
│       └── HandlerTest.java
├── pom.xml
├── .gitignore
└── README.md
```

### `.github/workflows/ci.yml`

```yaml
name: ci

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-java@v4
        with:
          java-version: "21"
          distribution: "corretto"
          cache: "maven"
      - run: mvn checkstyle:check

  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-java@v4
        with:
          java-version: "21"
          distribution: "corretto"
          cache: "maven"
      - run: mvn test

  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-java@v4
        with:
          java-version: "21"
          distribution: "corretto"
          cache: "maven"
      - run: mvn org.owasp:dependency-check-maven:check -DfailBuildOnCVSS=7
```

### `.github/workflows/cd.yml`

```yaml
name: cd

on:
  push:
    branches: [main]

permissions:
  id-token: write
  contents: read

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-java@v4
        with:
          java-version: "21"
          distribution: "corretto"
          cache: "maven"

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
          aws-region: ${{ vars.AWS_REGION }}

      - name: Build
        run: mvn package -DskipTests

      - name: Deploy to Lambda
        run: |
          aws lambda update-function-code \
            --function-name ${{ vars.LAMBDA_FUNCTION_NAME }} \
            --zip-file fileb://target/function.jar
```

### `src/main/java/com/example/Handler.java`

```java
package com.example;

import com.amazonaws.services.lambda.runtime.Context;
import com.amazonaws.services.lambda.runtime.RequestHandler;
import java.util.Map;

public class Handler implements RequestHandler<Map<String, Object>, Map<String, Object>> {

    @Override
    public Map<String, Object> handleRequest(Map<String, Object> event, Context context) {
        return Map.of(
            "statusCode", 200,
            "body", "{\"message\": \"Hello from Lambda\"}"
        );
    }
}
```

### `pom.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>

    <groupId>com.example</groupId>
    <artifactId>lambda-java-template</artifactId>
    <version>1.0.0</version>
    <packaging>jar</packaging>

    <properties>
        <maven.compiler.source>21</maven.compiler.source>
        <maven.compiler.target>21</maven.compiler.target>
    </properties>

    <dependencies>
        <dependency>
            <groupId>com.amazonaws</groupId>
            <artifactId>aws-lambda-java-core</artifactId>
            <version>1.2.3</version>
        </dependency>
        <dependency>
            <groupId>junit</groupId>
            <artifactId>junit</artifactId>
            <version>4.13.2</version>
            <scope>test</scope>
        </dependency>
    </dependencies>

    <build>
        <plugins>
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-shade-plugin</artifactId>
                <version>3.6.0</version>
                <executions>
                    <execution>
                        <phase>package</phase>
                        <goals><goal>shade</goal></goals>
                        <configuration>
                            <finalName>function</finalName>
                        </configuration>
                    </execution>
                </executions>
            </plugin>
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-checkstyle-plugin</artifactId>
                <version>3.5.0</version>
            </plugin>
        </plugins>
    </build>
</project>
```

### `.gitignore`

```
target/
*.class
.idea/
*.iml
.mvn/
```

---

## Verificación final

Después de crear los tres repos, verificar que el workflow de Port puede usarlos:

```bash
# Verificar que cada repo existe y está marcado como template
gh repo view <ORG>/lambda-python-template --json isTemplate -q '.isTemplate'
gh repo view <ORG>/lambda-nodejs-template --json isTemplate -q '.isTemplate'
gh repo view <ORG>/lambda-java-template  --json isTemplate -q '.isTemplate'
# Los tres deben devolver: true
```

El workflow en Port estará listo para usarlos una vez que los tres retornen `true`.
