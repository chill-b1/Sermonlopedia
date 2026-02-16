# Start from the public, pre-built Docker Image provided by the Wiki.js team.
# This image already contains Node.js, the application code, and all dependencies installed.
FROM ghcr.io/requarks/wiki:2

# Set the Wiki.js application working directory inside the container.
WORKDIR /wiki

# The base Wiki.js image already exposes port 3000, but it's good practice to keep it.
EXPOSE 3000

# The base Wiki.js image already defines the entrypoint and command to run the wiki.
# To keep this simple and rely on the base image's configuration, you can often omit CMD.
# However, if you want to explicitly run the start script, it is usually "npm start"
# or "node server.js" in the base image. For the Wiki.js image, simply running the
# container is enough to execute its default entrypoint.

# You can add personalized files, configurations, or utility installations below this line.
# Example:
# COPY ./my-custom-config.yml /wiki/config.yml
# RUN apt-get update && apt-get install -y my-favorite-utility