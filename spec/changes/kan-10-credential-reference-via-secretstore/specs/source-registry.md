## MODIFIED Requirements

### Requirement: Credentials are references
The system SHALL store only a `credentials_ref`; secret values SHALL NOT be stored, logged or returned. Resolving a `credentials_ref` into an actual secret value SHALL happen only through `SecretStore.get`, via `adapters.secret_store.resolve.resolve_credential`.

#### Scenario: read a source
- **Given** a source with a credentials_ref
- **When** it is fetched through the API
- **Then** no secret value appears in the response or logs

#### Scenario: resolve-credential-success
- **Given** a `credentials_ref` key that resolves to a value in the configured `SecretStore`
- **When** `resolve_credential(credentials_ref, secret_store)` is called
- **Then** it returns that value

#### Scenario: resolve-credential-missing-key
- **Given** a `credentials_ref` key that does not resolve in the configured `SecretStore`
- **When** `resolve_credential(credentials_ref, secret_store)` is called
- **Then** it raises `CredentialNotFoundError` whose message contains only the `credentials_ref` key, never a secret value

#### Scenario: api-never-logs-resolved-secret
- **Given** a `credentials_ref` that matches a real, resolvable secret value
- **When** a source is registered and served through the API
- **Then** the resolved secret value never appears in the HTTP request, the HTTP response, or any captured log line
