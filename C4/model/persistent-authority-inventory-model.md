# E5 Persistent Authority Inventory Model

This model compares persistent secret-key objects retained by authority holders
as the number of protected functions grows. It does not count active worker
copies, warm caches, session state, key/FID bindings, policy metadata, or general
trusted memory.

The protected-function grid is `F={1,10,100,1000,10000}`.

| Series | Persistent objects | Evidence boundary |
|---|---:|---|
| AsynCS | `1` | One master-secret object per authority domain. Function-scoped invocation and function-code capabilities are derived on demand rather than retained at the TEE-KMS. |
| Per-function stored capabilities | `2F` | Controlled model that persistently stores the two function-scoped decryption capabilities which AsynCS derives on demand. It is not a measured prior system. |
| Wallet | `F` | One function-provider private-key object per protected function. Copies provisioned to active monitors are outside this persistent-authority metric. |
| CoFunc | `ceil(F/K)` | One tenant-key object retained by the CoFunc KMS per modeled tenant. `K=4.928751447449084` is the 14-day mean observed functions per Azure `HashOwner`; `HashOwner` is a tenant proxy, not an observed CoFunc tenant. |

Reusable Enclaves is not plotted because its public artifact closes active
Gateway/worker session state but not complete persistent authority inventory.
S-FaaS is not plotted because its default authority unit is a KDE domain rather
than a function; assigning one three-key KDE domain per function would be an
explicit counterfactual model.

Object count is not a comparison of serialized bytes, compromise probability,
security strength, or performance. The curves compare inventory organization
under their stated authority granularities.
