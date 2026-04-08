## Comando para ver errores en consola

    aws cloudformation describe-stack-events \
    --stack-name cuenta-palabras-dev-lambda \
    --query 'StackEvents[?ResourceStatus==`UPDATE_FAILED` || ResourceStatus==`CREATE_FAILED`].[LogicalResourceId,ResourceStatusReason]' \
    --output table