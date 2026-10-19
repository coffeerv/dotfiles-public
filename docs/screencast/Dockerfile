FROM debian:12
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates curl git zsh unzip xz-utils openssh-client age python3 && rm -rf /var/lib/apt/lists/*
RUN useradd -m -s /bin/zsh demo
USER demo
WORKDIR /home/demo
ENV PATH="/home/demo/.local/bin:/home/demo/.local/share/mise/shims:$PATH" TERM=xterm-256color
RUN curl -fsSL https://mise.run | sh
RUN mise use -g bun gum chezmoi age fnox github-cli
RUN mkdir -p /home/demo/dotfiles
ADD --chown=demo:demo repo.tar /home/demo/dotfiles/
WORKDIR /home/demo/dotfiles
RUN mise trust && mise install
CMD ["zsh", "-f"]
