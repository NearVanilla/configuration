ARG JAVA_VERSION=17
# We can't use alpine variants as they use musl instead of glibc
FROM eclipse-temurin:${JAVA_VERSION}-jdk-focal AS jre-build

# Create a custom Java runtime
RUN $JAVA_HOME/bin/jlink \
  --add-modules java.base \
  --strip-debug \
  --no-man-pages \
  --no-header-files \
  --compress=2 \
  --output /javaruntime

FROM debian:bullseye-slim AS base

SHELL ["/bin/bash", "-c"]

# Install all requirements first
COPY docker/apt-packages.list /tmp/apt-packages.list
RUN apt-get update \
  && xargs apt-get install -y < <(sed '/^#/d' /tmp/apt-packages.list) \
  && rm -rf /var/lib/apt/lists/*

# Install required software in requirements.txt
COPY docker/manager-requirements.txt /tmp/requirements.txt

RUN pip3 install -r /tmp/requirements.txt

# Setup java
ENV JAVA_HOME=/opt/java/openjdk
ENV PATH "${JAVA_HOME}/bin:${PATH}"
COPY --from=jre-build /javaruntime $JAVA_HOME

RUN useradd --create-home --uid 1000 runner


COPY docker/known_hosts docker/config_repo_ro_key /home/runner/.ssh/

RUN chown -R runner:runner /home/runner/.ssh

USER runner

# TODO: Find a better place for all these files
COPY manage.py /manage.py
COPY server_manager/ /server_manager/

# TODO: Configure entrypoint git to use it
COPY scripts/githooks/ /githooks/

COPY docker/entrypoint.sh /entrypoint.sh
ENTRYPOINT ["dumb-init", "--", "/entrypoint.sh"]

COPY docker/start.sh /start.sh

CMD ["/start.sh"]
