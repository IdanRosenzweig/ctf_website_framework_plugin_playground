# CTFd Playground Plugin

Introduces the attack playground inside CTFd: one page that says what the
playground is, what a session gets you, and the ssh command to connect with.

The page is rendered from configuration alone. CTFd never talks to the
playground, so the page is there whether the playground is up or down, and
nothing has to be reachable between the two hosts for this plugin to work.

The playground itself is a separate project:
<https://github.com/jonathanlotan/attack_playground>.

## What it adds

- `/playground`, listed in the user menu as "Playground": what the playground
  is, the `ssh` command to connect with (and a button to copy it), what a
  session gets, and the house rules.

That is the whole of it. No endpoints, no admin page, no database tables, no
background requests.

## Setup

Install like any plugin and restart CTFd. Then point the page at your
playground, which means telling it the address players should ssh to.

The defaults describe a playground on a host called `researchlabs` with the
ports it ships with. If yours is elsewhere, set `PLAYGROUND_SSH_HOST` (and
`PLAYGROUND_SSH_PORT`, if you changed `SSH_PORT` in the playground's `.env`).

Note that this is the address as **players** reach it, not as CTFd reaches it:
CTFd does not connect to the playground at all, so a name that only resolves
inside CTFd's docker sandbox would put an address on the page that nobody can
use.

## Options

All options can be set as environment variables or in the `[extra]` section of
`CTFd/config.ini`. Environment variables take precedence.

- `PLAYGROUND_SSH_HOST` (default: `researchlabs`): the host players ssh to.
- `PLAYGROUND_SSH_PORT` (default: `2222`): the port they ssh to, which is
  `SSH_PORT` in the playground's `.env`.
- `PLAYGROUND_SSH_USER` (default: `guestuser`): the username the example
  command uses. The playground accepts every username and every password, so
  this is only what the page suggests.
- `PLAYGROUND_GATEWAY_HOST` (default: `researchlabs.tech`): the name that, from
  inside a session, resolves to the exercise endpoints. The playground defines
  it in `config.yaml` under `docker.execution.host.extrahosts`; read the current
  one with `python3 scripts/render_config.py hostname` there.
- `PLAYGROUND_DOCS_URL` (default: the repository above): where the page's
  "written up at" link points.

## Keeping the page true

The page describes the playground as it ships: a throwaway Ubuntu container per
ssh session, a filesystem in memory that dies with the session, no internet, and
the exercise endpoints reachable by name. The things most likely to drift are
configurable above; the rest is deliberately described in words rather than
numbers, so that retuning the playground's limits does not silently make this
page wrong.

If you change what a session *is* over there - the tooling in
`guest_docker.dockerfile`, or the network policy in
`attack_network_endpoints.conf` - reread `templates/playground.html` and see
whether it still tells the truth.

## Removing

Delete this directory, as with any plugin. The page returns 404 and the menu
entry goes with it. The plugin keeps no tables and stores nothing.
