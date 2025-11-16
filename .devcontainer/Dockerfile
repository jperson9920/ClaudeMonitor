FROM mcr.microsoft.com/vscode/devcontainers/base:0-debian-12

# noninteractive installs
ENV DEBIAN_FRONTEND=noninteractive
ARG RUST_TOOLCHAIN=1.70.0

RUN apt-get update \
  && apt-get install -y --no-install-recommends \
    ca-certificates curl wget gnupg build-essential git unzip \
    python3.9 python3.9-venv python3-pip \
    libnss3 libxss1 libasound2 fonts-liberation libatk-bridge2.0-0 libgtk-3-0 libx11-xcb1 libxcomposite1 libxrandr2 libatk1.0-0 \
    chromium \
  && rm -rf /var/lib/apt/lists/*

# Node 18 (official NodeSource setup)
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
  && apt-get install -y nodejs \
  && npm install -g npm@latest \
  && rm -rf /var/lib/apt/lists/*

# Install rustup and pin toolchain
RUN curl https://sh.rustup.rs -sSf | sh -s -- -y --default-toolchain ${RUST_TOOLCHAIN} \
  && . $HOME/.cargo/env \
  && rustup default ${RUST_TOOLCHAIN} \
  && rustup component add rustfmt clippy || true

ENV PATH=$HOME/.cargo/bin:$PATH

# Quick user setup: devcontainer uses 'vscode' user by default
# Ensure python3 points to python3.9
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.9 1 || true

# Clean up
RUN apt-get clean || true

# Workspace
WORKDIR /workspace

# Default user set by devcontainer.json (vscode)