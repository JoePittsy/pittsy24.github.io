---
headline: "User-Assigned Managed Identities for Dynamics 365 Plugins - The Bits the Docs Don't Tell You"
summary: "Wiring a User-Assigned Managed Identity to a Dynamics 365 plugin? The happy path is documented well enough. Here are the two configuration gotchas that'll have you staring at a trace log instead."
date: 02/07/2026
outputPath: ./blog/dynamics365/uami-plugins.html
tags:
    - Dynamics365
    - Azure
---


## What are we doing?

If you need a Dynamics 365 plugin to talk to Azure, publish to Event Grid, call a downstream API, anything that needs a token, you don't want to be hardcoding credentials. The supported way is to associate a Managed Identity with the plugin and let the platform's `IManagedIdentityService` hand you tokens at runtime.

User-Assigned Managed Identities are usually the right choice in enterprise setups. They're portable across environments and they have their own lifecycle, independent of any single resource, which makes them much easier to deal with in an ALM pipeline than a system-assigned one.

The catch is that three things all have to line up:

1. A **UAMI** in Azure with an app registration
2. A **Federated Identity Credential (FIC)** on that app registration, scoped to the specific plugin package
3. The identity **linked to the plugin package** in Dataverse via the `pac` CLI

Get any one of those wrong and it fails before your plugin code even runs.

## The error

Here's what you'll actually see, a trace log entry along these lines:

```
Unhandled Exception: System.Exception: ManagedIdentityServiceProviderAcquireToken...
```

The useful thing to notice is that this is a **platform-level failure**. It happens as Dataverse initialises the execution context, before your `Execute` method runs at all. So it's a configuration problem, not a code one, which narrows things down straight away.

## Gotcha 1: Assembly vs Package

The easiest mistake to make here is linking the managed identity to the plugin **assembly** when you should be linking it to the plugin **package**.

If you deployed with a NuGet package (the modern, recommended approach), the component you link against is `PluginPackage`, not `PluginAssembly`. They're separate component types in Dataverse and the identity link doesn't carry over between them.

You can check what you've got with:

```bash
pac managed-identity get \
  --component-id <your-component-guid> \
  --component-type PluginAssembly
```

If that returns a result and your plugin is deployed as a package, that's your problem. Delete it and recreate it against the package:

```bash
# Remove the incorrect assembly link
pac managed-identity delete \
  --component-id <assembly-guid> \
  --component-type PluginAssembly

# Find your package GUID if you don't have it
pac env fetch --xml "<fetch><entity name='pluginpackage'><attribute name='pluginpackageid'/><attribute name='name'/></entity></fetch>"

# Link to the package instead
pac managed-identity create \
  --component-id <package-guid> \
  --component-type PluginPackage \
  --managed-identity-id <uami-client-id>
```

One tip on that `pac env fetch` output. Don't skip a fixed number of header lines to get at the data, `pac` prefixes its output with a "Connected as..." line that varies. Grep for the lines that look like GUIDs instead:

```bash
pac env fetch --xml "..." | grep -E "^[0-9a-f]{8}-"
```

## Gotcha 2: The missing Federated Identity Credential

Even with the identity correctly linked to the package, token acquisition still fails if the Federated Identity Credential hasn't been added to the app registration in Azure.

The FIC tells Azure AD which issuer and subject are allowed to exchange tokens on behalf of the identity. Dataverse generates a unique subject for each environment/package combination, and there's no way to know that value without asking Dataverse for it:

```bash
pac managed-identity verify-fic \
  --component-id <package-guid> \
  --component-type PluginPackage
```

That returns the exact values you need, something like:

- **Issuer:** `https://login.microsoftonline.com/<tenant-id>/v2.0`
- **Subject:** `/eid1/c/pub/t/<tenant-hash>/e/<env-hash>/h/<component-hash>`
- **Audience:** `api://AzureADTokenExchange`

Take those to the app registration in the Azure portal &rarr; **Certificates & secrets &rarr; Federated credentials &rarr; Add credential**, choose *Other issuer*, and paste them in. The name is arbitrary.

Save it, run `verify-fic` again, and it should confirm the credential is present and valid.

## In your plugin code

Once the configuration is right, acquiring a token is the straightforward part:

```csharp
public void Execute(IServiceProvider serviceProvider)
{
    var context = (IPluginExecutionContext)serviceProvider.GetService(typeof(IPluginExecutionContext));
    var serviceFactory = (IOrganizationServiceFactory)serviceProvider.GetService(typeof(IOrganizationServiceFactory));
    var managedIdentityService = (IManagedIdentityService)serviceProvider.GetService(typeof(IManagedIdentityService));

    var token = managedIdentityService.AcquireToken(new[] { "https://eventgrid.azure.net/.default" });

    // Use token.AccessToken with your HttpClient / Azure SDK client
}
```

`IManagedIdentityService` is the platform's own token vending interface, it handles the federated credential exchange internally. You don't need to implement any of that yourself.

## A note on Azure SDK versions

If you're using the Azure SDK (`Azure.Core`, `Azure.Messaging.EventGrid` and so on) inside your plugin, be aware that the Dataverse sandbox has its own version of `Azure.Core` pre-loaded. At the time of writing that's `1.50.0`.

Bundle a different version without accounting for it and you'll hit a `TypeLoadException` during registration, a completely separate failure from the UAMI config above, but just as opaque.

The fix is to compile against the sandbox version and exclude it from the bundle:

```xml
<PackageReference Include="Azure.Core" Version="1.50.0"
  ExcludeAssets="runtime" PrivateAssets="all" />
```

The Dependent Assemblies packaging approach handles the rest, but that's probably worth its own post.

## Final Thoughts

Once it's set up, UAMIs are the right way to do this, no secrets stored in your plugin and tokens handed to you on demand.

The pain is all in the plumbing. Both gotchas surface as the *same* platform-level trace error, which makes them easy to conflate, so when you hit it, check them in order:

1. **Component type** - is the identity linked to `PluginPackage` and not `PluginAssembly`?
2. **The FIC** - run `pac managed-identity verify-fic` and confirm the credential is on the app registration with the exact issuer/subject Dataverse expects.

Check those two before you touch any code and you'll save yourself a lot of time.

## References and Resources

- [Set up Power Platform managed identity for Dataverse plug-ins](https://learn.microsoft.com/en-us/power-platform/admin/set-up-managed-identity)
- [Power Platform managed identity overview](https://learn.microsoft.com/en-us/power-platform/admin/managed-identity-overview)
- [pac managed-identity command reference](https://learn.microsoft.com/en-us/power-platform/developer/cli/reference/managed-identity)
- [Workload identity federation](https://learn.microsoft.com/en-us/entra/workload-id/workload-identity-federation)
