# PhenoRelay

PhenoRelay is a Phenopacket-native library and service for searching local
collections and sharing policy-controlled results between institutions.

It is not a strict Beacon implementation. Sites retain their source GA4GH
Phenopacket v2 JSON and expose only the query capabilities and response detail
they choose.

PhenoRelay exposes both Rust and Python surfaces. Rust is the lightweight engine
path for deployable discovery. Python is the schema, evidence, documentation, and
agent-tooling path, and can also run local discovery utilities.

Initial discovery scope:

- cohort statistics;
- HPO phenotypes;
- MONDO diseases;
- genomic findings when present;
- MAXO and maxodiff medical actions.

## Development

Install a stable Rust toolchain and `uv`, then clone the repository:

```bash
git clone https://github.com/VarenyaJ/PhenoRelay.git
cd PhenoRelay
cargo test --workspace --locked
```

GitHub Actions runs checks on pull requests and pushes. Run the Rust checks
directly when needed:

```bash
cargo test --workspace --all-features --all-targets --locked
cargo fmt --all --check
cargo clippy --workspace --all-features --all-targets --locked -- -D warnings
RUSTDOCFLAGS="-D warnings -D rustdoc::broken_intra_doc_links" \
  cargo doc --workspace --all-features --no-deps --locked
```

Use `uv` for the Python surface. Do not install an unmanaged Python environment.

```bash
uv sync --extra dev --extra schema --extra docs
uv run phenorelay --help
uv run pytest
```

Keep each commit limited to one reviewable concern. Before committing, inspect the
staged patch:

```bash
git status --short
git diff --staged
git commit -m "add typed query outcomes"
```

Do not use `--no-verify`, amend around a failed hook, or add
`Co-Authored-By` lines. Push a new branch with upstream tracking:

```bash
git push -u origin <branch-name>
```

Subsequent pushes use `git push`. Do not force-push a shared branch without
explicit agreement.

## Debugging

Run one test with output visible:

```bash
cargo test -p phenorelay-core query_round_trips_through_json -- --nocapture
```

Enable a backtrace for a failing test or binary:

```bash
RUST_BACKTRACE=1 cargo test --workspace --all-features --all-targets --locked
RUST_BACKTRACE=full cargo test -p phenorelay-core <test-name> -- --nocapture
```

Use `cargo check` for a fast compiler pass and inspect resolved dependencies when
a version or feature is unexpected:

```bash
cargo check --workspace --all-features --all-targets --locked
cargo tree --workspace
cargo tree -e features -i <crate-name>
```

For an interactive native debugger, build tests without running them, copy the
reported test executable path, and open it with LLDB on macOS or GDB on Linux:

```bash
cargo test -p phenorelay-core --no-run
rust-lldb target/debug/deps/phenorelay_core-<hash>
```

Inside LLDB, use `breakpoint set --name <function>`, `run`, `bt`, and `frame
variable`. Replace `rust-lldb` with `rust-gdb` on Linux.

Do not print Phenopacket contents, bearer tokens, subject identifiers, or raw
federated queries while debugging. Structured server tracing and Python-extension
debugging instructions will be added with those implementation slices.
