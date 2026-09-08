# Deploying

Live at **https://systems.joeko.net** (also https://joekonet-systems.netlify.app).

- **Repo:** `github.com/joekogit/design-systems` (public, since 2026-09-08)
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

## Troubleshooting: "can't resolve systems.joeko.net"

If you looked the domain up **before** the alias existed, your machine cached the failure.
`joeko.net`'s SOA negative TTL is 3600s, so a failed lookup sticks for an hour. The giveaway is
`dig` succeeding while `curl` and the browser fail — `dig` queries the DNS server directly, but
everything else goes through the OS resolver, which holds the stale negative entry.

```bash
sudo dscacheutil -flushcache && sudo killall -HUP mDNSResponder   # macOS resolver
```

Then in Chrome: `chrome://net-internals/#dns` -> **Clear host cache**. On Tailscale, MagicDNS
(`100.100.100.100`) caches separately — toggling the connection clears it.

Confirm the server side is healthy regardless of local DNS:

```bash
curl -sI --resolve "systems.joeko.net:443:98.84.224.111" https://systems.joeko.net/ | head -1
```

## Netlify rewrites the HTML on deploy

Post-processing minifies markup and turns on **pretty URLs**, so `href="designs/x.html"` in the
built file is served as `href='/designs/x'`. Both forms resolve; don't be alarmed when the live
HTML doesn't match the local build byte for byte.

## Continuous deploys

While the repo was **private**, every webhook build was refused:

> Build blocked: Unrecognized Git contributor. This plan allows only verified account members
> to push to private repos.

Three things were tried and none of them lifted it, so don't repeat them:

- **`netlify init`** — its own output says what it does: *"Adding deploy key to repository...
  Creating Netlify GitHub Notification Hooks"*. That is the deploy-key path, which grants read
  access but no GitHub **identity** mapping, so Netlify still cannot verify who pushed.
- **The Netlify GitHub App** (installation `111393814`) — this *does* create the identity
  mapping, and after installing it with access to all repositories a push does reach Netlify and
  create a production deploy. It still failed with the identical message.
- **Commit authorship** — failing identically whether authored as `joe.kocovsky@gmail.com` or
  `13067392+joekogit@users.noreply.github.com`, and with or without a `Co-Authored-By` trailer.

The message means exactly what it says: it is a **plan restriction on private repos**, not a
wiring problem. The repo is now public, which removes the restriction.

Netlify caches the repo's visibility on the site record as `build_settings.public_repo`. It is
derived from GitHub rather than settable over the API, and refreshed on the next push after the
repo went public.

### The second blocker: a publish directory with a leading space

With the contributor block gone, builds ran but failed in the **Deploying** stage (the API reports
this misleadingly as *"Failed during stage 'building site': exit code 2"*; the stage breakdown in
the UI shows Building complete, Deploying failed). `netlify init` had left two bad values in the
site's stored build settings:

```
build_settings.dir = " ."               # leading space - that directory does not exist
build_settings.cmd = "# no build command"   # the literal string, i.e. a shell comment
```

Editing `netlify.toml` did **not** override them — three pushes proved it. The stored settings had
to be corrected directly:

```bash
netlify api updateSite --data '{"site_id":"9a161ed6-7881-4b6c-8ee7-864d7fccd50d",
  "body":{"build_settings":{"dir":".","cmd":""}}}'
```

Same thing in the UI: Site configuration -> Build & deploy -> Build settings.

**Continuous deploys work as of 2026-09-08**: a push to `main` builds and publishes on its own.

Build logs are not reachable from the CLI — the API 404s on `/deploys/{id}/log` and
`log_access_attributes` is null — so read them in the web UI. The per-stage breakdown there is
usually enough to place a failure, and it is what separated "building" from "deploying" here.

**Manual deploy always works** and takes a few seconds:

```bash
netlify deploy --prod --dir .
```

## Before any deploy

```bash
python3 build.py all     # regenerate all pages + index
```

Then check `tools/audit.html` over a local server (`python3 -m http.server 8899`) — it needs
HTTP, not `file://`.
