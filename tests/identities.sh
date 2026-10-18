#!/usr/bin/env bash
# Renders the repo with its example data into a throwaway HOME and checks that git picks the
# right identity per folder and per remote. Used by CI; safe to run locally (touches nothing in ~).
set -euo pipefail
repo=$(cd "$(dirname "$0")/.." && pwd)
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT

chezmoi archive --source "$repo" --format tar --output "$work/out.tar"
mkdir -p "$work/home" && tar -xf "$work/out.tar" -C "$work/home"
export HOME="$work/home" GIT_CONFIG_NOSYSTEM=1
git config --global --get user.name >/dev/null   # rendered .gitconfig parses

fail=0
check() { # where expected-email expected-key-suffix
  local got key
  got=$(git -C "$1" config user.email || echo NONE)
  key=$(git -C "$1" config user.signingkey | sed 's/.*REPLACE_WITH_YOUR_//' || true)
  if [[ $got == "$2" && $key == "$3" ]]; then echo "ok   $1"; else echo "FAIL $1: email=$got key=$key (want $2 / $3)"; fail=1; fi
}
repo_at() { mkdir -p "$1" && git -C "$1" init -q && { [[ -z ${2:-} ]] || git -C "$1" remote add origin "$2"; }; echo "$1"; }

check "$(repo_at "$HOME/code/personal/a")"            you@personal.example PERSONAL_PUBLIC_KEY
check "$(repo_at "$HOME/code/org1/a")"                you@org1.example     ORG1_GITHUB_PUBLIC_KEY
check "$(repo_at "$HOME/code/org1/bitbucket/a")"      you@org1.example     ORG1_BITBUCKET_PUBLIC_KEY
check "$(repo_at "$HOME/code/org2/a")"                you@org2.example     ORG2_PUBLIC_KEY
check "$(repo_at "$work/elsewhere")"                  NONE                 ""
check "$(repo_at "$work/r1" git@github.com:org1/x.git)"          you@org1.example     ORG1_GITHUB_PUBLIC_KEY
check "$(repo_at "$work/r2" git@bitbucket.org:org1/x.git)"       you@org1.example     ORG1_BITBUCKET_PUBLIC_KEY
check "$(repo_at "$work/r3" https://bitbucket.org/org1/x.git)"   you@org1.example     ORG1_BITBUCKET_PUBLIC_KEY
check "$(repo_at "$work/r4" https://github.com/org2/x.git)"      you@org2.example     ORG2_PUBLIC_KEY
check "$(repo_at "$work/r5" git@github.com:your-user/x.git)"     you@personal.example PERSONAL_PUBLIC_KEY
exit $fail
