# Multi-identity dotfiles

[Español](README.es.md)

**One computer, several GitHub accounts, zero mix-ups, no passwords in plain text.**

If you have a personal GitHub account and also work for one or more companies, you've probably
committed with the wrong email, pushed with the wrong SSH key, or left an API key sitting in a `.env` file.
This repo sets up your computer so that **the right identity switches on by itself when you enter a folder**:

```
~/code/personal/my-blog     →  you@personal.example, your personal SSH key and GitHub login
~/code/acme/backend         →  you@acme.com, Acme's SSH key and GitHub login, Acme's API keys
anywhere else               →  git refuses to commit until you're in the right place
```

Your passwords, tokens and private SSH keys **stay in your password manager** (1Password or Bitwarden).
Only *references* to them are written to disk, so nothing secret ends up in this repo or in your home folder in plain text.

## What you get

- **The right git name, email and commit signature** in every folder, plus in clones and worktrees
  outside those folders, matched by the remote's URL.
- **The right SSH key** for each GitHub (or Bitbucket, or GitLab) account, even with several accounts on the same site.
- **The right `gh` login** per account.
- **API keys that load when you enter a folder and unload when you leave it** (Linear, Jira, Sentry, Stripe,
  Datadog, Expo, Claude Code… or your own). They're never saved in plain text.
- **Signed commits** ("Verified" on GitHub) with keys that never leave your password manager.
- A **setup wizard** that asks a few questions and does the rest, on macOS, Linux, WSL and Windows (PowerShell).

## Quick start

About 10 minutes. It changes `~/.gitconfig`, `~/.ssh/config` and your shell profile (`~/.zshrc`, or your
PowerShell profile on Windows). If you already have those files, the wizard saves a backup copy before replacing them.

You need:
- a password manager: **1Password** or **Bitwarden**, with its desktop app and its **SSH agent** turned on. That's a
  built-in helper that lets other programs use your SSH keys without ever seeing them; see the [Glossary](#glossary).
  How to turn it on: [1Password](https://developer.1password.com/docs/ssh/get-started/#step-3-turn-on-the-1password-ssh-agent),
  [Bitwarden](https://bitwarden.com/help/ssh-agent/).
- **git**
- on Windows: **PowerShell 7** (`winget install Microsoft.PowerShell`)

Then:

1. **Make your own copy** of this repo on GitHub (Fork, or "Use this template"). A **private** copy is a good idea:
   it will contain your emails and *public* keys. Those aren't secret, but they are personal.
2. **Install [mise](https://mise.jdx.dev)**, which installs every other tool for you:
   - macOS / Linux / WSL: `curl https://mise.run | sh`
   - Windows: `winget install jdx.mise`
3. **Download your copy** (this doesn't change anything yet):
   ```sh
   mise use -g chezmoi
   chezmoi init https://github.com/<you>/<your-copy>.git
   ```
4. **Run the wizard:**
   ```sh
   cd "$(chezmoi source-path)"
   mise trust
   mise run setup
   ```
5. **Follow the "Next steps"** it prints at the end: add your keys to GitHub, log in to `gh`, and put your API keys in your password manager.

Nothing in your home folder changes until you confirm: the wizard shows a summary and the list of files first, and
you can stop at any point with Ctrl-C. (SSH keys it creates in 1Password stay there; if you run it again, it reuses them.)

Using a screen reader, or prefer plain questions over menus? Run `mise run setup -- --plain`.

**Already have your own aliases or settings?** Put them in `~/.zshrc.local`, `~/.gitconfig.local` or `~/.ssh/config.local`
(Windows: `~/profile.local.ps1`). They're loaded automatically and the setup never touches them.

### Beginner or advanced?

The wizard asks first.

- **Beginner** covers the essentials:
  - your name
  - your personal GitHub account and email (it can use GitHub's private no-reply address)
  - your work accounts
  - which API keys each account needs
  - an SSH key per account, which it can create for you in 1Password
- **Advanced** adds:
  - a different projects folder (instead of `~/code`)
  - extra git hosts per account (Bitbucket, GitLab, self-hosted), each with its own key
  - your own secrets beyond the built-in list
  - environment variables (like `AWS_PROFILE`)
  - tool versions per account (like `node` or `ruby`)

## How it works, in one minute

When you `cd ~/code/acme/backend`:

1. **git** sees the folder (or the repo's remote URL) and loads Acme's settings: your Acme email, which SSH key to use,
   and the key that signs your commits. The key itself lives in your password manager's SSH agent, which signs
   when git asks it to.
2. **mise** sets Acme's non-secret settings, like which `gh` login to use, plus any tool versions Acme needs.
3. **fnox** loads Acme's API keys into your shell. It reads them from a small **encrypted** cache on your machine,
   so this is instant and never pops up a password prompt. Leave the folder and they're gone.

When you rotate a token in your password manager, run `secrets-sync` (or `secrets-sync acme`) to refresh that cache.

## Day to day

| I want to… | Run |
|---|---|
| refresh API keys after changing them in the password manager | `secrets-sync` |
| add, edit or remove an account, or redo SSH keys | `cd "$(chezmoi source-path)" && mise run setup` (it asks what you want to do) |
| see the after-setup checklist again | `mise run setup -- --next-steps` |
| see what would change before applying | `chezmoi diff` |
| set up a new computer | steps 2–4 of the quick start (your answers are already in your copy) |
| check which identity a repo uses | `git config user.email` |

## Under the hood

Built on three small tools, all installed by mise:
- [chezmoi](https://www.chezmoi.io) writes the config files.
- [mise](https://mise.jdx.dev) sets per-folder tool versions and settings.
- [fnox](https://fnox.jdx.dev) handles per-folder secrets, read from your password manager.

<details>
<summary><b>What changes where</b></summary>

With the example data in this repo:

| Folder | Git email + signing key | SSH key for git | `gh` account | Secrets in env |
|---|---|---|---|---|
| `~/code/personal/` | personal | `id_personal` | personal | personal |
| `~/code/org1/` | org1 | `id_org1` (GitHub) / `id_org1_bitbucket` (Bitbucket) | org1 | org1 |
| `~/code/org2/` | org2 | `id_org2` | personal (shared) | org2 |
| anywhere else | **none: git refuses to commit** | agent default | default | none |

- **Git identity:** `~/.gitconfig` uses `includeIf` by **folder**, and by **remote URL** too
  (`hasconfig:remote.*.url`, git ≥ 2.36), so it also works in worktrees and clones under `/tmp`.
  `user.useConfigOnly` makes git fail instead of guessing.
- **SSH key:** every identity's `core.sshCommand` passes `-i ~/.ssh/id_<id>.pub -o IdentitiesOnly=yes`. The `.pub`
  only tells the agent *which* private key to offer, so two accounts on the same host don't collide.
- **Signing:** SSH signatures through the password manager's agent (`op-ssh-sign` for 1Password, `ssh-keygen` for
  Bitwarden). `~/.ssh/allowed_signers` lists every identity, so `git log --show-signature` verifies them all.
- **Secrets:** each `~/code/<id>/fnox.toml` lists references (`op://Vault/Item/field`, or `Item/field` for Bitwarden).
  `fnox activate` loads them on `cd`. Values come from `fnox.local.toml`, an age-encrypted cache that
  `secrets-sync` fills, and secrets marked `env = false` are only available through `fnox get`.
- **Non-secrets:** each `~/code/<id>/mise.toml` holds `GH_CONFIG_DIR`, extra env vars and tool versions.
  For your own additions use `mise.local.toml`, which the setup never touches.
</details>

<details>
<summary><b>Repo layout</b></summary>

```
.chezmoidata/user.toml         your answers: name, emails, accounts, PUBLIC keys (the wizard writes it; hand edits are fine)
.chezmoidata/services.toml     the built-in list of services and the secrets each one needs
.chezmoitemplates/             the shared templates every identity is rendered from
dot_gitconfig.tmpl             includeIf rules, generated for every identity and host
dot_gitconfig.os.tmpl          the only file with OS-specific paths (signing program, ssh/ssh.exe, gh helper)
dot_gitconfig-<id>*.tmpl       one-line stubs per identity (the wizard creates/removes them)
private_dot_ssh/               agent config, id_<id>.pub, allowed_signers
code/<id>/                     per-identity mise.toml + fnox.toml stubs
dot_zshrc.tmpl                 zsh: mise + fnox activation, secrets-sync
Documents/PowerShell/          the same for PowerShell 7 on Windows
setup/wizard.ts                the wizard (Bun + gum, run with `mise run setup`)
tests/identities.sh            renders the example data and checks identity resolution (CI runs it on all 3 OSes)
examples/                      extras you can copy, like a short-lived OAuth token refresher
```

Hand-edited `user.toml`? Run `mise run setup -- --sync` to regenerate the stubs, then `chezmoi apply`.
Setting up many machines? `mise run setup -- --answers my-answers.toml --yes` runs without questions.
</details>

<details>
<summary><b>Password managers</b></summary>

| | 1Password | Bitwarden |
|---|---|---|
| Secrets (fnox) | `op` provider | `bitwarden` provider (needs `BW_SESSION`; `secrets-sync` unlocks for you) |
| SSH agent | 1Password agent | Bitwarden agent (on Windows, disable the "OpenSSH Authentication Agent" service) |
| Commit signing | `op-ssh-sign` | `ssh-keygen` through the agent |
| Wizard can create SSH keys | yes | no: create the key in the desktop app and paste its public key |
| Item naming | vault → item → field | `"<prefix> <item>"` with a custom field |

To switch later, change `password_manager` in `.chezmoidata/user.toml` (or re-run the wizard) and apply.
fnox supports [many other backends](https://fnox.jdx.dev). Adding one means touching `.chezmoitemplates/secret-ref`,
the fnox config template and `secrets_unlock`.
</details>

<details>
<summary><b>Platforms and project status</b></summary>

- **macOS, Linux, WSL:** zsh, with `~/.ssh/config` pointing at the agent's socket. On WSL the Windows agent is reached through `ssh.exe`.
- **Windows:** PowerShell 7 profile, `ssh.exe` and named pipes, `gitdir/i` for case-insensitive paths.

Status: CI renders the configuration and checks identity resolution on macOS, Linux and Windows. End-to-end use
(real keys, real pushes) has been exercised the least on Bitwarden, WSL and native Windows. Issues and fixes are welcome.
</details>

## What is and isn't in this repo

**In it (public, not secret):** names, emails, account/org names, *public* SSH keys, and *references* like `op://Acme/Linear/api-key`.

**Never in it:** private keys, tokens, passwords, `fnox.local.toml` (the encrypted cache), `~/.config/fnox/age.txt`
(this machine's key for that cache), `gh` login state. `.gitignore` blocks the usual suspects as a safety net.

## Glossary

- **SSH key:** a key pair that proves who you are to GitHub. The private half stays in your password manager; the public half is shared.
- **SSH agent:** a program, here part of your password manager, that uses your private keys on request without exposing them.
- **Commit signing:** a signature on each commit proving you made it. GitHub shows it as "Verified".
- **chezmoi / mise / fnox:** see [Under the hood](#under-the-hood).

## Support

This is an example to copy and adapt, provided as-is. Issues and pull requests are welcome but may not get a response.

## License

[MIT](LICENSE)
