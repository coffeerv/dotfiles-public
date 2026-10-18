# Dotfiles multi-identidad (chezmoi + mise + fnox)

[English](README.md)

Un **ejemplo** funcional para tener varias identidades de trabajo (una cuenta personal y las orgs que quieras)
en una misma máquina sin que se mezclen. Haz fork, renombra `org1`/`org2` a las tuyas y reemplaza los
valores de ejemplo.

**Este repo no contiene secretos.** Los secretos se quedan en tu gestor de contraseñas; aquí solo hay *referencias* a ellos.

> Los archivos de configuración y sus comentarios están en inglés; esta traducción cubre la documentación.

## Qué cambia al hacer `cd`

| Directorio | Email + llave de firma de git | Llave SSH para git | Cuenta de `gh` | Secretos en el entorno |
|---|---|---|---|---|
| `~/code/personal/` | personal | `id_personal` | personal | personal |
| `~/code/org1/` | org1 | `id_org1` (GitHub) / `id_org1_bb` (Bitbucket) | org1 | org1 |
| `~/code/org2/` | org2 | `id_org2` | personal (compartida) | org2 |
| cualquier otro lugar | **ninguno: git se niega a commitear** | la del agente | la default | ninguno |

Cómo llega cada pieza:

- **Identidad de git:** `~/.gitconfig` aplica `includeIf` por **directorio** y también por **URL del remote**
  (`hasconfig:remote.*.url`, git ≥ 2.36), así que la identidad correcta aplica también en worktrees y en
  clones dentro de `/tmp`. Con `user.useConfigOnly`, git falla en vez de adivinar.
- **Llave SSH:** el `core.sshCommand` de cada identidad pasa `-i ~/.ssh/id_<id>.pub -o IdentitiesOnly=yes`.
  Ese `.pub` solo le dice al agente SSH *qué* llave privada ofrecer, para que dos cuentas en el mismo host
  (GitHub, Bitbucket) no choquen. Las llaves privadas nunca tocan el disco.
- **Firma de commits:** firmas SSH con `op-ssh-sign`. `~/.ssh/allowed_signers` se genera a partir de todas
  las identidades, así que `git log --show-signature` las verifica todas.
- **Cuenta de `gh`:** mise define `GH_CONFIG_DIR` por directorio. Varios directorios pueden compartir una cuenta (ver org2).
- **Secretos:** el `fnox.toml` de cada identidad lista referencias (`op://Vault/Item/campo`). mise los
  exporta desde la **caché local de fnox cifrada con age**, así que entrar a un directorio no pide nada ni
  usa la red. `secrets-sync` refresca la caché desde el gestor de contraseñas.

Las integraciones de ejemplo están repartidas entre identidades: Jira, Bitbucket, Datadog, Claude Code (org1),
Linear, Sentry, Stripe, Expo, gcloud (org2). Muestran el patrón; ninguna org pretende parecerse a una real.

## Estructura

```
.chezmoidata.toml              tu nombre, emails y llaves PÚBLICAS: el único archivo que casi todos necesitan editar
dot_gitconfig.tmpl             reglas includeIf (directorio + URL del remote)
dot_gitconfig-<id>.tmpl        uno por identidad; org1-bb agrega Bitbucket encima de org1
dot_gitconfig.os.tmpl          el único archivo con rutas propias del sistema (op-ssh-sign, ssh/ssh.exe, helper de gh)
private_dot_ssh/               socket del agente, id_<id>.pub, allowed_signers
dot_config/private_fnox/       providers globales de fnox (gestor de contraseñas + caché age)
dot_zshrc.tmpl                 activación de mise + secrets-sync
code/<id>/{mise,fnox}.toml     entorno y referencias a secretos por identidad
code/org1/bin/                 ejemplo: token OAuth de corta vida refrescado vía fnox
run_once_before_10-*           crea la llave age de esta máquina (nunca se versiona)
```

## Máquina nueva

1. Instala tu gestor de contraseñas (con 1Password: la app, el CLI `op` y su agente SSH activado).
   En WSL, usa el agente de Windows a través de `ssh.exe`.
2. Instala [mise](https://mise.jdx.dev) y luego `mise use -g chezmoi age fnox github-cli`.
3. `chezmoi init --apply https://github.com/<tu-usuario>/<tu-fork>.git` (en WSL pregunta tu usuario de Windows).
4. Inicia sesión en `gh` una vez por cuenta: `GH_CONFIG_DIR=~/.config/gh-personal gh auth login`, y desde
   `~/code/org1`, `gh auth login`.
5. `secrets-sync` llena la caché de fnox de cada identidad.

## Hazlo tuyo

1. Edita `.chezmoidata.toml`: nombre, emails y la llave **pública** de cada identidad (cópiala de tu gestor de contraseñas).
2. Renombra `org1`/`org2` en todos lados (`grep -rn org1 .`): nombres de directorio, dueños en `includeIf`
   (`github.com:org1/**`), nombres de vault, `SECRETS_DIRS` en `dot_zshrc.tmpl`.
3. Reemplaza `your-user` en `dot_gitconfig.tmpl` por tu usuario personal de GitHub.
4. Apunta cada `fnox.toml` a tus items reales. Si un item todavía no existe, fnox avisa (`if_missing = "warn"`) en vez de fallar.

### Agregar una identidad

- Agrega `[identities.<id>]` a `.chezmoidata.toml`.
- Copia `dot_gitconfig-org2.tmpl` a `dot_gitconfig-<id>.tmpl` y cambia el id.
- Agrega `private_dot_ssh/id_<id>.pub.tmpl` con `{{ .identities.<id>.key }}`.
- Agrega su bloque `includeIf` a `dot_gitconfig.tmpl`.
- Crea `code/<id>/{mise,fnox}.toml` y agrega el directorio a `SECRETS_DIRS`.
- Agrega su vault a la config del agente de 1Password (`dot_config/private_1Password/private_ssh/private_agent.toml`).

## Gestor de contraseñas: 1Password, Bitwarden u otro

Los secretos pasan por [fnox](https://fnox.jdx.dev), así que a los archivos de cada identidad no les importa qué gestor hay detrás.
Para cambiar de 1Password a Bitwarden:

- En `dot_config/private_fnox/config.toml.tmpl`, cambia el provider `op` por el de `bitwarden` que está comentado.
- Reescribe cada `value` de `op://Vault/Item/campo` a `Item/Campo`, usando el nombre del provider nuevo.
- En `secrets_unlock` (`dot_zshrc.tmpl`), usa la línea de Bitwarden (`BW_SESSION`).

Dos partes **sí** dependen de 1Password y necesitarían su propio reemplazo: el **agente SSH**
(`private_dot_ssh/config.tmpl`, la config del agente de 1Password) y la **firma de commits** (`op-ssh-sign` en
`dot_gitconfig.os.tmpl`). Sirve cualquier agente SSH que tenga tus llaves; apunta `IdentityAgent` y `gpg.ssh.program` hacia él.

## Por sistema operativo

- `~/.gitconfig.os`: ruta de `op-ssh-sign`, `ssh` vs `ssh.exe`, helper de credenciales de `gh`, CRLF en Windows.
- `~/.ssh/config`: el socket del agente (macOS/Linux). En WSL/Windows, `ssh.exe` habla con el agente de Windows.
- `~/.config/fnox/config.toml`: el destinatario age de esta máquina (un script `run_once` crea la llave).

## Nunca en este repo

`~/.config/fnox/age.txt`, `fnox.local.toml`, llaves SSH privadas, `.gh/`, `*.bak-*`.

## Licencia

[MIT](LICENSE)
