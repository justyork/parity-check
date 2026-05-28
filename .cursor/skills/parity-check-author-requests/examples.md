# parity-check: additional request examples

## PUT with path vars and minimal body (negative case)

```yaml
# file: projects/tcf/requests/put-session-invalid-body-400.yaml
id: put-session-invalid-body-400
method: PUT
path: /api/v1/users/${USER_ID}/platforms/${PLATFORM_IOS}/stores/${STORE_APP_STORE}/bundles/${BUNDLE_ID_IOS}/session
headers:
  X-Request-ID: parity-b004-invalid-body
body:
  language: en
ignore_paths:
  - $.instance
  - $.detail
  - $.traceId
```

## Different headers on right only

```yaml
# file: projects/consent-metrics/requests/post-session-android-form.yaml
id: post-session-android-form
method: POST
path: /session
headers:
  Content-Type: application/x-www-form-urlencoded
body: >-
  os_name=android&user_id=${random.uuid.1}&advertising_id=${random.uuid.2}
right:
  headers:
    X-Tenant-ID: ${TENANT_ID}
ignore_paths:
  - $.install_date
  - $.rt
```

## Full URL for one side

```yaml
# file: projects/example/requests/proxy-left-only.yaml
id: proxy-left-only
method: GET
path: /health
left:
  url: https://special-proxy.internal/health
```

## Explicit skip with reason

```yaml
# file: projects/my-api/requests/legacy-only-endpoint.yaml
id: legacy-only-endpoint
method: GET
path: /internal/deprecated
skip: true
skip_reason: endpoint removed on right; parity N/A until migration done
```

## env with base override

```yaml
# file: projects/consent-metrics/env/local.yaml
base:
  left: http://localhost:8080
  right: http://localhost:8100
vars:
  TENANT_ID: test-tenant
  ANDROID_PACKAGE_NAME: com.example.android
```
