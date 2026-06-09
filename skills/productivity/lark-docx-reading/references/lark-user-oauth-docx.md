# Lark User-Identity OAuth Docx Reading — U-VISA continuation (2026-05-09)

## Security decision

When the human user can open/read a Lark Docx but `tenant_access_token` / bot identity returns `403` or OAuth returns scope errors, prefer **user identity OAuth** instead of broadening tenant/app document access.

Rationale:

- User identity (`user_access_token`) aligns with the user's existing document ACL.
- It avoids granting a bot/app broad tenant-level document access when the task only needs to read documents the user can already access.
- It makes the trust boundary explicit: app declares scopes; the user authorizes; calls use `Authorization: Bearer <user_access_token>`.

## Route verified from Lark docs

Docx block API accepts either `tenant_access_token` or `user_access_token`:

- `GET https://open.larksuite.com/open-apis/docx/v1/documents/:document_id/blocks`
- Header: `Authorization: Bearer <access_token>`

For this U-VISA PRD case, the target route is:

1. Register OAuth redirect URL exactly: `http://localhost:8765/callback`.
2. Add **user** scopes, not tenant scopes:
   - `docx:document`
   - `offline_access` only if refresh tokens are needed.
3. Build authorize URL with `scope=docx:document offline_access`.
4. User authorizes; callback receives one-time code.
5. Exchange code through `POST /open-apis/authen/v2/oauth/token`.
6. Read Docx with `--auth user`.

## Errors observed and meaning

- `20029`: redirect URL invalid. Fix Security Settings → Redirect URL. Exact URL was added successfully: `http://localhost:8765/callback`.
- `20027`: app permissions insufficient. This occurred before permission import and still occurred after adding scopes while they remained `待发布`.
- `403` / `1770032`: tenant/app token lacks document permission or needed scope; if the user can read the doc, switch to user OAuth.

## Current U-VISA state

Evidence state:

- `/tmp/uvisa-lark-user-oauth-permission-state.json`
- `/tmp/lark-batch-permissions-pasted.png`
- `/tmp/lark-batch-permissions-review.png`
- `/tmp/lark-permission-after-apply.png`
- `/tmp/lark-oauth-after-permission.png`

Completed:

- `~/.hermes/scripts/lark_docx_reader.py` supports:
  - `--auth user`
  - `LARK_USER_ACCESS_TOKEN`
  - `--oauth-code`
  - `--make-auth-url`
- Redirect URL added.
- User scopes imported and applied:
  - `offline_access`
  - `docx:document`
- Permission table shows `docx:document` as `待发布｜可调试`.

Blocked by safety boundary:

- OAuth still returns `20027` because permission changes require version creation/release.
- Do not click version publish / approval / tenant install without explicit user confirmation.

## Safe next steps

After user authorizes version publication:

1. In Lark Developer Console, create/publish version containing the new user scopes.
2. If admin approval appears, stop and ask unless already explicitly authorized.
3. Retry OAuth authorize URL.
4. When callback writes `/tmp/lark-oauth-callback.json`, use its `code` without printing it.
5. Run:

```bash
LARK_APP_ID='[REDACTED]' LARK_APP_SECRET='[REDACTED]' \
python3 ~/.hermes/scripts/lark_docx_reader.py \
  'https://uaecprod.sg.larksuite.com/docx/GaGLdayTSosobYx6kWylgS7PgMg' \
  --auth user \
  --oauth-code '<callback-code>' \
  --redirect-uri http://localhost:8765/callback \
  --scope 'docx:document offline_access' \
  --out /tmp/uvisa-lark-product-doc-user-openapi.json
```

Never print the code, access token, refresh token, app secret, or cookies.
