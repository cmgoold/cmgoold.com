FROM lukemathwalker/cargo-chef:0.1.68-rust-latest AS chef
WORKDIR /cmgoold

FROM chef AS planner
COPY . .
RUN cargo chef prepare --recipe-path recipe.json

FROM chef AS builder
COPY --from=planner /cmgoold/recipe.json recipe.json
RUN cargo chef cook --release --recipe-path recipe.json

COPY . .
RUN cargo build --release --bin cmgoold

FROM debian:bookworm-slim AS runtime
WORKDIR /cmgoold
COPY --from=builder /cmgoold/target/release/cmgoold /usr/local/bin/
COPY --from=builder /cmgoold/assets/ /cmgoold/assets/
ENTRYPOINT ["/usr/local/bin/cmgoold"]
