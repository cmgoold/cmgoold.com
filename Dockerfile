FROM lukemathwalker/cargo-chef:latest-rust-1 AS chef
WORKDIR /cmgoold

FROM chef AS planner
COPY . .
RUN cargo chef prepare --recipe-path recipe.json

FROM chef AS builder
COPY --from=planner /cmgoold/recipe.json recipe.json
RUN cargo chef cook --release --recipe-path recipe.json
RUN apt update;
RUN apt install -y pkg-config libssl-dev

COPY . .
RUN cargo build --release --bin cmgoold

FROM debian:bookworm-slim AS runtime
RUN apt update; apt install -y libssl3 ca-certificates
WORKDIR /cmgoold
COPY --from=builder /cmgoold/target/release/cmgoold /usr/local/bin/
COPY --from=builder /cmgoold/assets/ /cmgoold/assets/
ENTRYPOINT ["/usr/local/bin/cmgoold"]
