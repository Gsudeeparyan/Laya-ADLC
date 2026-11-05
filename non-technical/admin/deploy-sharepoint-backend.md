# Deploy the backend for Laya Excel Expert for SharePoint

**For:** IT and platform engineers. This is the one agent that changes workbooks in place in SharePoint, so it needs a small Azure backend. Deploy the rest of the agents first: this one is optional.

**This hasn't been deployed to a real tenant yet.** The backend's tests use a fake Microsoft Graph. Treat the first deployment as a pilot, and have Security and the DPO review it, because it handles personal data.

## What you're deploying

| Part | What it does |
|---|---|
| Azure Function App (`technical/platform/backend/`) | Opens, changes and saves workbooks through Microsoft Graph |
| App Service Authentication | Checks the caller's Entra ID token before any code runs |
| Storage table `piivault` | Holds the real values behind privacy tokens, for 14 days by default |
| Key Vault | Holds the app's client secret |
| Application Insights | Diagnostics |

**How access works:** each call exchanges the signed-in person's token for a Microsoft Graph token (on-behalf-of), so the service can only open files that person can open. Values such as `PERSON_001` are what the model sees.

## 1. Register the app in Entra ID

1. Create an app registration for the backend. Note the **client ID** and **tenant ID**.
2. Expose an API scope for the Copilot plugin to sign in to.
3. Grant delegated Microsoft Graph permissions for the files people work on. Use the narrowest that work, and get admin consent **[Security to confirm the exact permissions]**.
4. Create a client secret, for putting into Key Vault in step 3.

## 2. Deploy the Azure resources

From `technical/platform`:

```text
az deployment group create -g <resource group> -f backend/infra/main.bicep -p namePrefix=<prefix> backendClientId=<client id> tenantId=<tenant id>
```

Note the `functionHost` and `keyVaultName` outputs. Choose an EU region, and record the service in the ICT third-party register if Compliance needs it.

## 3. Add the secret

Put the client secret into the Key Vault from step 2, named `backend-client-secret`: the Function App reads it from there. Never put it in a settings file, a pipeline or the repo. `backend/local.settings.sample.json` shows the settings, for local testing only.

## 4. Publish the code

```text
python tools/package_backend.py
cd backend
func azure functionapp publish <prefix>-func --python
```

`package_backend.py` copies the engines into `backend/packages`, so the Function App can run on its own.

## 5. Build the agent package

From `technical/platform`:

```text
python tools/build_agents.py --function-host <functionHost> --oauth-reference-id <OAuth registration id>
```

The OAuth registration comes from the Teams Developer Portal, pointing at the backend's API scope. Without these two values the package still holds placeholders and **won't work**: `ready-to-use/agents/README.md` flags that.

## 6. Upload and test

1. Upload `ready-to-use/agents/everyone/laya-excel-expert-sharepoint/laya-excel-expert-sharepoint.zip`, as in [Deploy the agents](deploy-agents.md). Start with a pilot group.
2. With a made-up workbook in a test SharePoint folder, check that:
   - it reads the workbook and lists its sheets;
   - personal data comes back as tokens;
   - it asks for confirmation before saving;
   - SharePoint version history shows the previous copy;
   - a person with no access to the file can't open it through the agent;
   - two people editing at once gets a conflict message, not a silent overwrite.

## Before going wider

- [ ] Security has reviewed the permissions, network access and logs.
- [ ] The DPO has reviewed the vault, its retention period, and whether a DPIA is needed.
- [ ] Logs hold no personal data.
- [ ] There's a named service owner, an alert on failures, and a rollback plan.

Use the `production-ready` and `member-data-safety` skills for the review. The backend's API is described in `backend/openapi.yaml`.
