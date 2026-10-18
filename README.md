# Multi-identity dotfiles (chezmoi + mise + fnox)

[Español](README.es.md)

A working **example** of keeping several work identities (a personal account and any number of orgs) on one
machine without them bleeding into each other. Fork it, rename `org1`/`org2` to your own, and replace the
placeholders.

**No secrets live in this repo.** Secrets stay in your password manager; this repo only holds *references* to them.

## What changes when you `cd`

| Directory | Git email + signing key | SSH key for git | `gh` account | Secrets in env |
|---|---|---|---|---|
| `~/code/personal/` | personal | `id_personal` | personal | personal |
| `~/code/org1/` | org1 | `id_org1` (GitHub) / `id_org1_bb` (Bitbucket) | org1 | org1 |
| `~/code/org2/` | org2 | `id_org2` | personal (shared) | org2 |
| anywhere else | **none: git refuses to commit** | agent default | default | none |

How each piece gets there:

- **Git identity:** `~/.gitconfig` matches `includeIf` by **directory**, and by **remote URL** too
  (`hasconfig:remote.*.url`, git ≥ 2.36), so the right identity also applies in worktrees and in clones
  under `/tmp`. `user.useConfigOnly` makes git fail instead of guessing.
- **SSH key:** every identity's `core.sshCommand` passes `-i ~/.ssh/id_<id>.pub -o IdentitiesOnly=yes`. That
  `.pub` file only tells the SSH agent *which* private key to offer, so two accounts on the same host
  (GitHub, Bitbucket) don't collide. The private keys never touch disk.
- **Commit signing:** SSH signatures through `op-ssh-sign`. `~/.ssh/allowed_signers` is generated from
  every identity, so `git log --show-signature` verifies all of them.
- **`gh` account:** `GH_CONFIG_DIR` is set per directory by mise. Several directories can share one account (see org2).
- **Secrets:** each identity's `fnox.toml` lists references (`op://Vault/Item/field`). mise exports them
  from fnox's **local age-encrypted cache**, so entering a directory needs no prompt and no network.
  `secrets-sync` refreshes the cache from the password manager.

Example integrations are spread across the identities: Jira, Bitbucket, Datadog, Claude Code (org1),
Linear, Sentry, Stripe, Expo, gcloud (org2). They show the pattern; neither org is meant to look like a real one.

## Layout

```
.chezmoidata.toml              your name, emails and PUBLIC keys: the only file most people need to edit
dot_gitconfig.tmpl             includeIf rules (directory + remote URL)
dot_gitconfig-<id>.tmpl        one per identity; org1-bb layers Bitbucket on top of org1
dot_gitconfig.os.tmpl          the only file with OS-specific paths (op-ssh-sign, ssh/ssh.exe, gh helper)
private_dot_ssh/               agent socket config, id_<id>.pub, allowed_signers
dot_config/private_fnox/       global fnox providers (password manager + age cache)
dot_zshrc.tmpl                 mise activation + secrets-sync
code/<id>/{mise,fnox}.toml     per-identity env and secret references
code/org1/bin/                 example: short-lived OAuth token refreshed via fnox
run_once_before_10-*           creates this machine's age key (never committed)
```

## New machine

1. Install your password manager (for 1Password: the app, the `op` CLI, and its SSH agent turned on).
   On WSL, use the Windows agent through `ssh.exe`.
2. Install [mise](https://mise.jdx.dev), then `mise use -g chezmoi age fnox github-cli`.
3. `chezmoi init --apply https://github.com/<you>/<your-fork>.git` (on WSL it asks for your Windows user).
4. Log `gh` in once per account: `GH_CONFIG_DIR=~/.config/gh-personal gh auth login`, and from inside
   `~/code/org1`, `gh auth login`.
5. `secrets-sync` fills each identity's fnox cache.

## Make it yours

1. Edit `.chezmoidata.toml`: name, emails, and each identity's **public** key (copy it from your password manager).
2. Rename `org1`/`org2` everywhere (`grep -rn org1 .`): directory names, `includeIf` owners
   (`github.com:org1/**`), vault names, `SECRETS_DIRS` in `dot_zshrc.tmpl`.
3. Replace `your-user` in `dot_gitconfig.tmpl` with your personal GitHub username.
4. Point each `fnox.toml` at your real items. If an item doesn't exist yet, fnox warns (`if_missing = "warn"`) instead of failing.

### Adding an identity

- Add `[identities.<id>]` to `.chezmoidata.toml`.
- Copy `dot_gitconfig-org2.tmpl` to `dot_gitconfig-<id>.tmpl` and change the id.
- Add `private_dot_ssh/id_<id>.pub.tmpl` with `{{ .identities.<id>.key }}`.
- Add its `includeIf` block to `dot_gitconfig.tmpl`.
- Create `code/<id>/{mise,fnox}.toml` and add the directory to `SECRETS_DIRS`.
- Add its vault to the 1Password agent config (`dot_config/private_1Password/private_ssh/private_agent.toml`).

## Password manager: 1Password, Bitwarden, or something else

Secrets go through [fnox](https://fnox.jdx.dev), so the per-identity files don't care which manager sits behind them.
To switch from 1Password to Bitwarden:

- In `dot_config/private_fnox/config.toml.tmpl`, swap the `op` provider for the commented `bitwarden` one.
- Rewrite each `value` from `op://Vault/Item/field` to `Item/Field`, using the new provider name.
- In `secrets_unlock` (`dot_zshrc.tmpl`), use the Bitwarden line (`BW_SESSION`).

Two parts **are** tied to 1Password and would need their own replacement: the **SSH agent**
(`private_dot_ssh/config.tmpl`, the 1Password agent config) and **commit signing** (`op-ssh-sign` in
`dot_gitconfig.os.tmpl`). Any SSH agent that holds your keys works; point `IdentityAgent` and `gpg.ssh.program` at it.

## Per OS

- `~/.gitconfig.os`: `op-ssh-sign` path, `ssh` vs `ssh.exe`, `gh` credential helper, CRLF on Windows.
- `~/.ssh/config`: the agent socket (macOS/Linux). On WSL/Windows, `ssh.exe` talks to the Windows agent.
- `~/.config/fnox/config.toml`: this machine's age recipient (a `run_once` script creates the key).

## Never in this repo

`~/.config/fnox/age.txt`, `fnox.local.toml`, private SSH keys, `.gh/`, `*.bak-*`.
