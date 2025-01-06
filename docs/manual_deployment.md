# Manual Deployment of the Services

## Manual Deployment of the Weather and Recommendation Services

Below you will find the detailed instruction on how to deploy services manually for testing purposes without the support 
of the CI/CD pipeline.

## Prerequisites 

1. Switch to the folder called `services/weather_service` *[not mandatory]*:
   ```shell
   $ cd services/weather_service
   ```
2. Install Azure CLI to support communication with Azure Portal/Cloud:
    ```shell
    curl -sL https://aka.ms/InstallAzureCLIWindows.ps1 | pwsh   # Windows
    brew install azure-cli   # macOS
    ```
3. Login inside the shell to the Azure Cloud via:
    ```shell
   $ az login
    # Create Resource Group
   $ az group create --name rg-wearthe-dev --location eastus
    ```
   You can choose any name of the resource group you want to use later. 

## Services setup:

1. The `weather_service` application needs the setup of **Redis Cache**:

    ```bash
   $ az redis create --name redis-wearthe-dev --resource-group rg-wearthe-dev \
   --location westeurope --sku Basic --vm-size c0
    ```
   **FYI**: Please re-check the service requirements and costs as it updates regularly. For easy-to-go setup you can create the Redis Service manually from Azure Cloud UI. Usually the deployment of this service takes a big amount of time (~15-20 minutes in average).

2. Get the Redis Connection string (it will be needed further):

    ```bash
    $ REDIS_CONN=$(az redis list-keys --name redis-wearthe-dev --resource-group rg-wearthe-dev \
      --query primaryConnectionString --output tsv)
    ```

3. Create Azure KeyVault Service to store all the secrets related to this project/service:

    ```bash
   $ az keyvault create --name kv-wearthe-dev --resource-group rg-wearthe-dev --location westeurope
    ```
   And after the keyvault was created you need to assign the additional roles through managed identity to store and manage secrets:
    
    * get your user object ID (you can also find this in Azure Portal under Azure Active Directory → Users): 

    ```bash
   $ az ad signed-in-user show --query id -o tsv
    ```
   
    * assign the "Key Vault Administrator" role to yourself:

    ```bash
    $ az role assignment create \
    --assignee-object-id "your-object-id" \
    --role "Key Vault Administrator" \
    --scope "/subscriptions/[your_subs_id_here]/resourcegroups/rg-wearthe-dev/providers/microsoft.keyvault/vaults/kv-dev-wearthe"
    ```
   
    * set the access policy in Key Vault:
    
    ```bash
    $ az keyvault set-policy --name kv-dev-wearthe --object-id "your-object-id" \
      --secret-permissions get list set delete backup restore recover purge
    ```
   
4. Set the needed secrets via Azure KeyVault store:

    ```bash
   $  az keyvault secret set --vault-name kv-dev-wearthe --name "redis-connection-string" \
   --value "your-redis-connection-string"
   ```
   Create and store other secrets in the similar way as showed above.


5. Create and set-up Azure Container Registry (ACR) Service to store and use Docker images and containers:

    ```bash
     $ az acr create --name acrwearthedev --resource-group rg-wearthe-dev --sku Basic \
        --admin-enabled true
    ```
   * Get the credentials (will be needed below):
   
    ```bash
    $ ACR_USERNAME=$(az acr credential show --name acrwearthedev \
      --query "username" --output tsv) 
   ```
   
    ```bash 
    $ ACR_PASSWORD=$(az acr credential show --name acrwearthedev --query "passwords[0].value" \
      --output tsv)
    ```
6. Build and push the Docker images:

    ```bash
    $ az acr login --name acrwearthedev 
   ```
   
    * Build and push the Weather Service:
   
    ```bash
    $ cd services/weather_service
    $ docker build -t acrwearthedev.azurecr.io/weather-service:latest .
    $ docker push acrwearthedev.azurecr.io/weather-service:latest 
   ```
    
    * Build and push the Recommendation Service:
   
    ```bash
     $ cd ../recommendation_service
     $ docker build -t acrwearthedev.azurecr.io/recommendation-service:latest .
     $ docker push acrwearthedev.azurecr.io/recommendation-service:latest
    ```

7. Set-up and configure WebApp Services:
    
    * Create App Service plan (aka VM for managing the WebApps): 
   
    ```bash
    $ az appservice plan create --name asp-wearthe-dev --resource-group rg-wearthe-dev \
      --sku B1 --is-linux
    ```
   
    * Create Weather Service App:
    
    ```bash
     $ az webapp create --resource-group rg-wearthe-dev --plan asp-wearthe-dev \
       --name weather-service-wearthe-dev --deployment-container-image-name acrwearthedev.azurecr.io/weather-service:latest
    ```
   
    * Create Recommendation Service App:

   ```bash
    $ az webapp create --resource-group rg-wearthe-dev --plan asp-wearthe-dev \
      --name recommendation-service-wearthe-dev --deployment-container-image-name acrwearthedev.azurecr.io/recommendation-service:latest
   ```
   
8. Configure App Settings:

   ```bash
    $ az webapp config appsettings set \
      --resource-group rg-wearthe-dev --name weather-service-wearthe-dev \
      --settings ENVIRONMENT="production" AZURE_KEYVAULT_URL="https://kv-wearthe-dev.vault.azure.net/" \
      WEBSITES_PORT=8000
   ```
   and for the Recommendation Service

   ```bash
    # Recommendation Service Configuration
    $ az webapp config appsettings set --resource-group rg-wearthe-dev --name recommendation-service-wearthe-dev \
      --settings ENVIRONMENT="production" AZURE_KEYVAULT_URL="https://kv-wearthe-dev.vault.azure.net/" \
      WEATHER_SERVICE_URL="https://weather-service-wearthe-dev.azurewebsites.net" \
      WEBSITES_PORT=8000
   ```

9. Enable Managed Identity for Weather Service:

   ```bash
   # Enable managed identity for Weather Service
   az webapp identity assign \
     --resource-group rg-wearthe-dev \
     --name weather-service-wearthe-dev

   # Get Weather Service Managed Identity ID
   WEATHER_ID=$(az webapp identity show --resource-group rg-wearthe-dev \
   --name weather-service-wearthe-dev --query principalId --output tsv)

   # Grant Key Vault access
   az keyvault set-policy --name kv-wearthe-dev --object-id $WEATHER_ID --secret-permissions get list

   # The same steps for Recommendation Service
```
   