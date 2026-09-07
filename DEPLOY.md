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

Configured with `netlify init --force --git-remote-name origin`, which installs a read-only deploy
key and the Netlify notification hooks through the CLI's authenticated GitHub session. `git push`
deploys `main`.

`netlify.toml` is the source of truth for build settings (`publish = "."`, empty build command) and
overrides whatever the site's own settings say.

To deploy without pushing:

```bash
netlify deploy --prod --dir .
```

## Before any deploy

```bash
python3 build.py all     # regenerate all pages + index
```

Then check `tools/audit.html` over a local server (`python3 -m http.server 8899`) — it needs
HTTP, not `file://`.
