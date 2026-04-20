#!/bin/sh
set -e

# Inject runtime environment variables into env.js
envsubst '${VITE_API_URL}' < /usr/share/nginx/html/env.js > /tmp/env.js
mv /tmp/env.js /usr/share/nginx/html/env.js

exec nginx -g 'daemon off;'
