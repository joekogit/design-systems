# Deploying

Live at **https://joekonet-systems.netlify.app** — pending the `systems.joeko.net` alias below.

- **Repo:** `github.com/joekogit/design-systems` (private)
- **Netlify site:** `joekonet-systems` — site id `9a161ed6-7881-4b6c-8ee7-864d7fccd50d`
- **Team:** `joe-kocovsky`
- Static: no build step, no dependencies, relative links only. `netlify.toml` sets
  `publish = "."` with an empty build command plus a few security headers.

## Remaining: point systems.joeko.net at it

`joeko.net` is on Netlify DNS (nameservers `dns*.p02.nsone.net`), the same as `move`, `shot`,
`play`, `arcade` and `rave`. So the DNS record and the TLS certificate are both created for you —
there is nothing to add at a registrar.

1. https://app.netlify.com/projects/joekonet-systems/domain-management
2. **Add a domain** → `systems.joeko.net` → confirm.
3. Netlify writes the record in its own zone and provisions the certificate. Usually under a
   minute; occasionally a few minutes for the certificate.

Verify:

```bash
dig +short A systems.joeko.net          # expect the Netlify load-balancer IPs
curl -sI https://systems.joeko.net | head -1
```

## Continuous deploys are NOT set up yet

The first deploy was a direct upload, not a Git-linked build, so **pushing to GitHub will not
redeploy the site**. Two ways to fix that:

**Link the repo (recommended).** Site configuration → Build & deploy → Continuous deployment →
link `joekogit/design-systems`. Build command empty, publish directory `.`. This needs the
Netlify GitHub app authorisation, which is a browser flow. After that, `git push` deploys.

**Or deploy manually** with the Netlify CLI:

```bash
npm i -g netlify-cli
netlify login
netlify link --id 9a161ed6-7881-4b6c-8ee7-864d7fccd50d
netlify deploy --prod --dir .
```

## Before any deploy

```bash
python3 build.py all     # regenerate all pages + index
```

Then check `tools/audit.html` over a local server (`python3 -m http.server 8899`) — it needs
HTTP, not `file://`.
