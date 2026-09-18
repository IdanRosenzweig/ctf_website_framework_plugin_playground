# CTFd Playground Stats Plugin

Shows the attack playground's live connection statistics inside CTFd: how many
guests are on it right now, how many were on it during the last hour (or
another window), and how many ever were. The numbers come from the playground's
own stats server (`stats_server.py` next to its `docker-compose.yaml`), which
counts ssh sessions off docker's event stream.

## What it adds

- `/playground`, a page with the three numbers, listed in the user menu as
  "Playground". It refreshes itself every few seconds while it is open, pauses
  when the tab is hidden, and lets the viewer switch the window. A status pill
  says whether the numbers are **live** (the stats server is following docker),
  **stale** (the server is up but its collector is not, so the numbers may be
  out of date) or **unavailable** (CTFd could not reach the server).
- `/api/v1/playground/stats?window=1h`, the json the page polls. It answers
  with the stats server's response under `data`, or with 503 and an `errors`
  object when the server cannot be reached. `window` has to be one of the
  configured windows; anything else is a 400.
- `/admin/playground_stats`, in the admin menu as "playground stats": the
  settings in effect and a fresh, uncached answer from the stats server, for
  finding out why the page says "unavailable".

## Setup

CTFd reads the numbers from `http://researchlabs:2224/stats` and hands them to
the page itself, so visitors never talk to the playground host. The playground
publishes its stats server on every address of its host on `STATS_PORT` from
its `.env` (2224 as shipped), so CTFd reaches it over the network like anyone
else would.

CTFd runs in its own docker sandbox, where `127.0.0.1` is the CTFd container
rather than the machine, which is why the plugin addresses the playground by
name. When the playground runs on the same machine as CTFd, the `ctfd` service
in `docker-compose.yml` maps `researchlabs` to the docker host with
`extra_hosts`, and nothing else is needed. If the name already resolves (dns or
`/etc/hosts`) that mapping can go, and if the playground runs on another host,
set `PLAYGROUND_STATS_URL` instead.

Restart CTFd after installing, like any plugin.

## Options

All options can be set as environment variables or in the `[extra]` section of
`CTFd/config.ini`. Environment variables take precedence.

- `PLAYGROUND_STATS_URL` (default: `http://127.0.0.1:2224`): where the stats
  server answers. Change it when the playground runs elsewhere or on another
  port. A trailing `/stats` is optional.
- `PLAYGROUND_STATS_WINDOWS` (default: `15m,1h,24h,7d`): the "connected in the
  last ..." windows the page offers, comma separated, in the stats server's
  notation (seconds, or a count with `s`, `m`, `h` or `d`). Only these are ever
  requested upstream.
- `PLAYGROUND_STATS_WINDOW` (default: `1h`): the window the page opens with.
  Has to be one of the windows above.
- `PLAYGROUND_STATS_REFRESH` (default: `5`): seconds between refreshes of an
  open page. `0` turns polling off.
- `PLAYGROUND_STATS_TIMEOUT` (default: `2`): seconds a request to the stats
  server may take before it is given up on, so an unresponsive server cannot
  hang a CTFd worker.
- `PLAYGROUND_STATS_CACHE` (default: `2`): seconds an answer from the stats
  server is reused before it is fetched again. Many open pages therefore add up
  to one request per window every couple of seconds. A failure to reach the
  server is remembered for the same time.

## When the page says "unavailable"

CTFd could not get an answer from the stats server. From the CTFd host:

```sh
curl http://127.0.0.1:2224/stats
```

should print json. If it does not, the playground is down (`./start.sh` in
its directory brings it up, stats server included) or it publishes the stats
on a different port than `PLAYGROUND_STATS_URL` says. The admin page shows the
exact error CTFd got.

"Stale" is different: the stats server answered, but it is not following
docker's event stream at the moment, usually because docker went away and the
server is waiting to reconnect. The numbers are the last ones it knew. The
`playground-stats` container's log says why.

## Removing

Delete this directory, as with any plugin. The page and the endpoints return
404, the menu entries disappear with them, and `tests/test_playground_stats_plugin.py`
skips itself. The plugin keeps no tables.
