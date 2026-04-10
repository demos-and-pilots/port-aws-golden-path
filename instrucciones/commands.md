## Comando para ver errores en consola

    aws cloudformation describe-stack-events \
    --stack-name consultar-saldos-dev-lambda \
    --query 'StackEvents[?ResourceStatus==`UPDATE_FAILED` || ResourceStatus==`CREATE_FAILED`].[LogicalResourceId,ResourceStatusReason]' \
    --output table

**1. Eliminar el stack manualmente**
    aws cloudformation delete-stack \
    --stack-name consultar-saldos-dev-lambda \
    --region us-east-1

**2. Esperar que termine**
    aws cloudformation wait stack-delete-complete \
    --stack-name consultar-saldos-dev-lambda \
    --region us-east-1

**3. Consultar Stack**
    aws cloudformation describe-stack-events --stack-name consultar-saldos-dev-lambda