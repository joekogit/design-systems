# Deploying

Live at **https://systems.joeko.net** (also https://joekonet-systems.netlify.app).

- **Repo:** `github.com/joekogit/design-systems` (private)
- **Netlify site:** `joekonet-systems` — site id `9a161ed6-7881-4b6c-8ee7-864d7fccd50d`
- **Team:** `joe-kocovsky`
- Static: no build step, no dependencies, relative links only. `netlify.toml` sets
  `publish = "."` with an empty build command plus a few security headers.

## Domain — done

`systems.joeko.net` is the primary URL. `joeko.net` is on Netlify DNS (nameservers
`dns*.p02.nsone.net`), so the A records and the wildcard `*.joeko.net` Let's Encrypt certificate
were issued automatically. Verified: HTTP/2, HSTS, security headers, and a working 404.

```bash
dig +short A systems.joeko.net    # 98.84.224.111  18.208.88.157
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
