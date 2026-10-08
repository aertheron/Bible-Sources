# Free Cloudflare hosting

Canonical Scripture Study can start on **Cloudflare Workers Free**, using **Workers Static Assets** for the verified source packets. ChatGPT remains the study interface and performs translation, exegesis and theology. This server makes no model API calls and needs no OpenAI API key. Your ChatGPT plan and workspace permissions still govern access to ChatGPT Work and custom MCP plugins.

The deployment package is ready; no live endpoint or ChatGPT installation is claimed. Cloudflare account login and deployment are the remaining account-side steps.

## Deploy from your computer

Install Node.js 22 or later and Git, then run:

```bash
git clone https://github.com/aertheron/Bible-Sources.git
cd Bible-Sources/plugins/canonical-scripture-study/cloudflare
npm ci
npx wrangler login
npm run deploy
```

Wrangler opens Cloudflare login in your browser. Use a **Workers Free** account. The project uses Workers and Static Assets; it has no Containers, R2, paid database or paid model binding. A paid plan is not required by the configuration. The first deploy uploads approximately 518 MiB of prepared evidence files and can take several minutes; later deploys reuse unchanged assets.

Copy the actual `workers.dev` URL printed after a successful deployment. Add `/mcp`, for example:

```text
https://canonical-scripture-study.YOUR-SUBDOMAIN.workers.dev/mcp
```

This is a pattern, not an already deployed URL. Check your actual endpoint:

```bash
npm run smoke -- https://canonical-scripture-study.YOUR-SUBDOMAIN.workers.dev/mcp
```

The check covers MCP initialization, eleven read-only tools, source retrieval, Next, word studies, DSS reconstruction and linguistic columns, methodology instructions and domain errors.

## Deploy through Cloudflare's GitHub integration

In Cloudflare's **Workers & Pages** area, create a **Worker** and connect `aertheron/Bible-Sources`. Choose branch `main` and use:

| Setting | Value |
| --- | --- |
| Root directory | `plugins/canonical-scripture-study/cloudflare` |
| Dependency installation | `npm ci` (or the detected npm lockfile installation) |
| Build command | `npm run prepare:data` |
| Deploy command | `npx wrangler deploy` |
| Node version | 22 or later |

Use the Workers path in the dashboard. A static Pages site by itself does not expose this MCP server. The build needs the full repository checkout because the deterministic data preparation reads the source files above the application directory. Retain the default `ASSETS` binding from `wrangler.jsonc`.

## Connect it in ChatGPT

On ChatGPT web, open **Plugins → + → Add custom MCP server**. Name it **Canonical Scripture Study**, enter the deployed HTTPS `/mcp` URL, and select **OAuth** after configuring Cloudflare Access as described below. Review ChatGPT's connection prompt, create the personal plugin, then install it. In a new Work conversation select **@Canonical Scripture Study** and try:

- `Full study Romans 12:1-2`
- `Word study testing. Compare Matthew 6:13 and James 1:13.`
- `Translate Genesis 1-2, in Dutch, with original language interlinear`
- `Next`

The initial connection supplies the tools, server-wide method and translation key, and `get_study_instructions`, which retrieves the exact eight published skill instructions on demand. It also exposes twelve methodology resources. This allows an initial study trial through the MCP connection. Registering an MCP server does not itself install the repository's skill folders as native ChatGPT skills. To install the complete bundled plugin afterward, copy the registered connection ID beginning `plugin_asdk_app...` and wire that existing connection to this plugin's eight skills using the supported plugin packaging flow. There is no need to build a separate study website.


## Secure a private deployment with Cloudflare Access

The Worker **requires valid Cloudflare Access JWT assertions for every `/mcp` request**, including requests through a `workers.dev` hostname. Without environment configuration it fails closed with HTTP 503; requests lacking assertions are refused with HTTP 403. The existing `/health` endpoint remains an intentionally public, non-sensitive status response.

**Before deploying the protection:**

1. Configure a Cloudflare Access **self-hosted application** for the Worker custom domain (for example, `study.canonical-theology.com`), with an Allow policy for your exact email. Do not use an Everyone policy for a personal deployment.
2. In Zero Trust, copy the application's **Application Audience (AUD) Tag** from Additional settings, and your **Team domain** (for example, `https://example.cloudflareaccess.com`).
3. Under **Workers & Pages → canonical-scripture-study → Settings → Variables and Secrets**, add two text variables named `TEAM_DOMAIN` and `POLICY_AUD`. The configured `keep_vars` setting preserves dashboard variables across Wrangler deployments. Neither value is a client secret.
4. Deploy and test that unauthenticated `/mcp` requests are rejected. In Access application settings, under **Advanced settings**, enable **Managed OAuth**. Configure the Access token lifetime to approximately 15 minutes and the grant session to up to 14 days. Only allow redirect URIs actually needed by trusted OAuth clients.
5. In ChatGPT, reconnect the personal MCP plugin to the custom domain using **OAuth**. Complete the Cloudflare login through your permitted account and smoke-test actual tool calls.
6. After OAuth works, disable the unneeded `workers.dev` route. JWT checks remain enabled as defense in depth.

**Do not merge or deploy this change until `TEAM_DOMAIN` and `POLICY_AUD` are configured.** Otherwise the MCP endpoint intentionally stops responding to valid tool calls. Cloudflare Access handles the OAuth browser flow and forwards a signed JWT in `Cf-Access-Jwt-Assertion`; the Worker validates the JWT signature, issuer, audience and expiry before it runs tools. ChatGPT's OAuth access token is not itself a JWT for this Worker to verify.

For future public release, keep JWT validation but replace the single-email Access policy with a suitable public-user authentication policy and identity provider. Do not provide Cloudflare-account access to end users.

## Free limits and verification

Workers Free currently allows **100,000 requests/day and 10 ms CPU per invocation**. Static asset storage and serving have no additional charge; the free file allowance is **20,000 files**, each at most **25 MiB**. This build uses **13,365 files** and its largest is **782,080 bytes**. `prepare:data` checks both file limits and aborts if they are exceeded. The compressed Worker bundle is approximately 1.16 MiB.

The ten Python runtime operations have a native JavaScript counterpart. There are **1,921 matching Python/Worker comparisons**, including all 1,189 chapter boundaries, all 50 word studies and all selected lexical lookup IDs. Five Worker test groups check parity, source tampering, Unicode offsets, asset limits and the actual Streamable HTTP handler. The same protocol smoke check also passed against local Wrangler/workerd over HTTP. The existing 32 Python checks also pass. These establish local behavior and a successful Wrangler deployment dry run; they do not establish live CPU usage or completed ChatGPT installation. Check the actual deployed endpoint and Cloudflare CPU metrics during a trial. Use smaller verse windows and paged DSS retrieval for dense packets. Free-plan quota exhaustion or CPU failures require smaller requests or a later hosting decision; this project does not upgrade your account automatically.

Run `npm test` for behavior and protocol checks, `npm run build` for a deployment dry run, and `npm run dev` for the normal local Wrangler server. A restricted development environment may need explicit local ports: `npx wrangler dev --local --ip 127.0.0.1 --port 8787 --inspector-port 9229`.

## Data and state

`prepare:data` verifies 103 required metadata files and 64,104 unique source spans against the pinned profile before producing assets. Native chapter spans remain byte-for-byte intact. DSS is packaged by native verse while preserving physical-record order, nullable linguistic cells and passage reconstruction statuses; the prepared subset contains the 23,422 mapped physical records available through the current base-book router. Unmapped/nonbiblical DSS material remains in the source repository and is outside the current tool routes. The generated files are ignored by Git and are reproducible from the existing source snapshot.

Every retrieved asset is SHA-256 checked against the build manifest before parsing. Original edition paths, byte offsets, lengths, source hashes and commit remain in evidence packets. Runtime caches contain only verified public source bytes. No conversation state is saved on the server: ChatGPT passes back the returned `continuation_state`. Raw static asset paths are not public application routes; access is through bounded read-only tools. Rahlfs is excluded. Source-specific terms and attribution remain in force, including **CC BY-NC 4.0 for DSS**. Code is covered by the parent plugin's MIT licence.

Official setup references, checked 6 October 2026:

- [Cloudflare Workers pricing](https://developers.cloudflare.com/workers/platform/pricing/)
- [Static asset billing and limits](https://developers.cloudflare.com/workers/static-assets/billing-and-limitations/)
- [Workers platform limits](https://developers.cloudflare.com/workers/platform/limits/)
- [Workers Git build configuration](https://developers.cloudflare.com/workers/ci-cd/builds/configuration/)
- [Add a custom MCP server in ChatGPT](https://developers.openai.com/api/docs/guides/custom-mcp-server)
- [Package the complete plugin](https://developers.openai.com/plugins/build/plugins)
