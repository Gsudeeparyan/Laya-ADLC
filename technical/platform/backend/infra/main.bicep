// Azure resources for the Laya Excel Expert (SharePoint) backend.
//   az deployment group create -g <rg> -f backend/infra/main.bicep -p namePrefix=layaadlc backendClientId=<app id> tenantId=<tenant>
// The Entra app registration is created separately (see non-technical/admin/deploy-sharepoint-backend.md).

@description('Short prefix for resource names (lowercase letters and digits).')
param namePrefix string = 'layaadlc'
param location string = resourceGroup().location
@description('Client ID of the backend Entra app registration (the API the Copilot plugin signs in to).')
param backendClientId string
param tenantId string = subscription().tenantId

var storageName = take('${namePrefix}st${uniqueString(resourceGroup().id)}', 24)

resource storage 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: storageName
  location: location
  sku: { name: 'Standard_LRS' }
  kind: 'StorageV2'
  properties: {
    minimumTlsVersion: 'TLS1_2'
    allowBlobPublicAccess: false
    supportsHttpsTrafficOnly: true
  }
}

resource tableService 'Microsoft.Storage/storageAccounts/tableServices@2023-05-01' = {
  parent: storage
  name: 'default'
}

resource vaultTable 'Microsoft.Storage/storageAccounts/tableServices/tables@2023-05-01' = {
  parent: tableService
  name: 'piivault'
}

resource insights 'Microsoft.Insights/components@2020-02-02' = {
  name: '${namePrefix}-ai'
  location: location
  kind: 'web'
  properties: { Application_Type: 'web' }
}

resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: take('${namePrefix}-kv-${uniqueString(resourceGroup().id)}', 24)
  location: location
  properties: {
    tenantId: tenantId
    sku: { family: 'A', name: 'standard' }
    enableRbacAuthorization: true
    enableSoftDelete: true
  }
}

resource plan 'Microsoft.Web/serverfarms@2023-12-01' = {
  name: '${namePrefix}-plan'
  location: location
  sku: { name: 'Y1', tier: 'Dynamic' }
  kind: 'functionapp'
  properties: { reserved: true }
}

resource func 'Microsoft.Web/sites@2023-12-01' = {
  name: '${namePrefix}-func'
  location: location
  kind: 'functionapp,linux'
  identity: { type: 'SystemAssigned' }
  properties: {
    serverFarmId: plan.id
    httpsOnly: true
    siteConfig: {
      linuxFxVersion: 'Python|3.11'
      ftpsState: 'Disabled'
      minTlsVersion: '1.2'
      appSettings: [
        { name: 'FUNCTIONS_EXTENSION_VERSION', value: '~4' }
        { name: 'FUNCTIONS_WORKER_RUNTIME', value: 'python' }
        { name: 'AzureWebJobsStorage', value: 'DefaultEndpointsProtocol=https;AccountName=${storage.name};AccountKey=${storage.listKeys().keys[0].value};EndpointSuffix=${environment().suffixes.storage}' }
        { name: 'APPLICATIONINSIGHTS_CONNECTION_STRING', value: insights.properties.ConnectionString }
        { name: 'AAD_TENANT_ID', value: tenantId }
        { name: 'AAD_CLIENT_ID', value: backendClientId }
        { name: 'AAD_CLIENT_SECRET', value: '@Microsoft.KeyVault(VaultName=${keyVault.name};SecretName=backend-client-secret)' }
        { name: 'VAULT_TABLE_URL', value: '${storage.properties.primaryEndpoints.table}piivault' }
        { name: 'VAULT_TTL_SECONDS', value: '1209600' }
      ]
    }
  }
}

// Easy Auth: only callers with a valid Entra token for the backend API get through.
resource auth 'Microsoft.Web/sites/config@2023-12-01' = {
  parent: func
  name: 'authsettingsV2'
  properties: {
    globalValidation: {
      requireAuthentication: true
      unauthenticatedClientAction: 'Return401'
    }
    identityProviders: {
      azureActiveDirectory: {
        enabled: true
        registration: {
          openIdIssuer: '${environment().authentication.loginEndpoint}${tenantId}/v2.0'
          clientId: backendClientId
        }
        validation: {
          allowedAudiences: [ 'api://${backendClientId}', backendClientId ]
        }
      }
    }
  }
}

// The Function's identity may read/write the vault table and read the client secret - nothing else.
var tableContributor = '0a9a7e1f-b9d0-4cc4-a60d-0319b160aaa3'
var kvSecretsUser = '4633458b-17de-408a-b874-0445c86b69e6'

resource tableRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: storage
  name: guid(storage.id, func.id, tableContributor)
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', tableContributor)
    principalId: func.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

resource kvRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: keyVault
  name: guid(keyVault.id, func.id, kvSecretsUser)
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', kvSecretsUser)
    principalId: func.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

output functionHost string = func.properties.defaultHostName
output keyVaultName string = keyVault.name
