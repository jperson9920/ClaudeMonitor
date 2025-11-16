# EPIC-10-STOR-02

Title: Security guidance — chrome-profile storage, file permissions, optional encryption

Epic: [`EPIC-10`](docs/JIRA/EPIC-LIST.md:104)

Status: TODO

## Description
Document concrete, implementable security best practices for storing and protecting the Chromium/Chrome profile used by the scraper, optional encryption for session/profile data, credential management, and recommended file-permission policies for Windows/macOS/Linux. Provide exact file paths, example commands, and small utility function signatures a developer can use to add optional encryption to the scraper workflow. The guidance must be actionable by a developer with zero context.

Scope:
- Define canonical profile location used by the project: `scraper/chrome-profile/` (development) and runtime locations for packaged apps.
- Provide OS-specific permission commands (PowerShell, chmod/chown).
- Provide an optional, minimal Python encryption utility (AES-GCM) with function signatures and example usage for encrypting session blobs or the profile archive before storing in disk/artifact.
- Guidance for credential handling (avoid hardcoding, use environment variables, OS keystores where available).

## Acceptance Criteria
- [ ] `docs/JIRA/SECURITY_PROFILE.md` created with explicit guidance for:
  - canonical dev profile path: `scraper/chrome-profile/`
  - runtime packaged-profile path suggestion: `data/profile/` inside application resource dir
  - OS-specific permission and ownership commands
- [ ] Example Python helper `scraper/utils/security.py` specified (doc includes exact imports and function signatures):
  - `def encrypt_file(path: str, key: bytes) -> str` — encrypts file, returns path to encrypted file
  - `def decrypt_file(enc_path: str, key: bytes) -> str` — decrypts and returns path to plaintext file
  - `def derive_key_from_password(password: str, salt: bytes = None) -> Tuple[bytes, bytes]` — returns (key, salt)
  - Include example PyPI imports: `from cryptography.hazmat.primitives.ciphers.aead import AESGCM`
- [ ] Permission examples included:
  - Windows PowerShell command to restrict directory to current user
    - `icacls .\scraper\chrome-profile /inheritance:r /grant:r "%USERNAME%:(OI)(CI)F" /T`
  - Linux/macOS CLI commands:
    - `chown $USER:$USER scraper/chrome-profile -R`
    - `chmod 700 scraper/chrome-profile -R`
- [ ] Guidance on credential management: documented examples for using environment variables, and an example for reading secrets from OS keyring (Python `keyring` usage snippet).
- [ ] Research references included: `docs/Research.md:48-52` (session persistence), `docs/Research.md:248-259` (profile directory), and `docs/Research.md:356-370` (session expiry rationale).

## Dependencies
- EPIC-03 (session manager and profile save/load implementation)
- EPIC-06 (bundling decisions — where profile lives in bundled app)
- EPIC-10-STOR-01 (packaging affects where profile/resources are located at runtime)

## Tasks (1–3 hours each)
- [ ] Create `docs/JIRA/SECURITY_PROFILE.md` describing profile locations, permissions and operational guidance (1.5h)
  - Path: `docs/JIRA/SECURITY_PROFILE.md`
- [ ] Add example Python helper signatures and code snippets to `docs/JIRA/SECURITY_PROFILE.md` and reference file `scraper/utils/security.py` (1.5h)
  - Example imports to include in docs:
    - `import os`
    - `from pathlib import Path`
    - `from cryptography.hazmat.primitives.ciphers.aead import AESGCM`
    - `from cryptography.hazmat.primitives.kdf.scrypt import Scrypt`
- [ ] Add CLI permission examples and verification commands (PowerShell, Linux/macOS) with exact commands and notes on effect (1.0h)
- [ ] Write example usage block showing:
  - Derive key from password
  - Encrypt session blob: `encrypt_file("scraper/chrome-profile/session.bin", key)`
  - Decrypt at runtime before launching scraper: `decrypt_file("scraper/chrome-profile/session.bin.enc", key)` (1.0h)
- [ ] Add migration notes for packaged apps: how to store encrypted profile in `src-tauri/resources/` and decrypt at first-run (1.0h)

## Estimate
Total: 6 hours

## Research References
- Session persistence rationale and persistence-related notes: `docs/Research.md:48-52`
- Profile directory guidance and layout: `docs/Research.md:248-259`
- Session expiry and long-term considerations: `docs/Research.md:356-370`

## Risks & Open Questions
- Risk: Encrypting the entire Chrome profile may break Chromium compatibility if partial or in-place changes are not handled correctly; recommended approach is encrypting exported session/cookies blobs instead of whole profile where possible.
- Risk: Key management is hard — storing encryption keys on disk reduces protection. Recommend using OS keystore (Keychain/Windows Credential Manager) where available; document fallbacks.
- Open question: For bundled apps, should the profile be placed inside app-resources (read-only) and copied to a writable user data directory on first run, or shipped directly as a writable resource? (Flag for Orchestrator)
- Open question: Acceptable UX trade-off between requiring user-provided password (better security) vs. using machine-bound keys (better UX). Decide default for v1.0.
- Open question: Should we recommend or automate integration with platform key stores (macOS Keychain / Windows DPAPI) or leave as developer opt-in?