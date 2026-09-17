FROM debian:trixie-slim

ARG TARGETARCH
ARG TORRSERVER_VERSION=MatriX.142.LT-1.1.8
ARG TORRSERVER_AMD64_SHA256=90d1848082fc0e6df5b60f58b6338d9f36709c0c13c5f886d4dd53448647ad3d
ARG TORRSERVER_ARM64_SHA256=71a6c03fb92f725b44672f46ab2aa77cdb01ca3e2437eda4c7895f67f25860a4

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        ffmpeg \
        gstreamer1.0-libav \
        gstreamer1.0-plugins-bad \
        gstreamer1.0-plugins-base \
        gstreamer1.0-plugins-good \
        gstreamer1.0-plugins-ugly \
        gstreamer1.0-tools \
        libgcc-s1 \
        libstdc++6 \
    && case "$TARGETARCH" in \
        amd64) torrserver_sha="$TORRSERVER_AMD64_SHA256" ;; \
        arm64) torrserver_sha="$TORRSERVER_ARM64_SHA256" ;; \
        *) echo "Unsupported TorrServer-LT-gst architecture: $TARGETARCH" >&2; exit 1 ;; \
    esac \
    && curl --fail --location --retry 3 \
        "https://github.com/trinity-aml/TorrServer-LT/releases/download/${TORRSERVER_VERSION}/TorrServer-LT-linux-${TARGETARCH}-gst" \
        --output /usr/local/bin/torrserver \
    && echo "${torrserver_sha}  /usr/local/bin/torrserver" | sha256sum --check - \
    && chmod 0755 /usr/local/bin/torrserver \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /opt/ts/config

EXPOSE 8090 32000/tcp 32000/udp
VOLUME ["/opt/ts/config"]

ENTRYPOINT ["/usr/local/bin/torrserver"]
CMD ["--path", "/opt/ts/config", "--port", "8090", "--ip", "0.0.0.0", "--torrentaddr", ":32000"]
