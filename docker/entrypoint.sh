#!/bin/bash

set -e

if [ -z "$@" ]; then
  exec /usr/bin/supervisord -c /etc/supervisor/supervisord.conf --nodaemon
else
  PATH=/usr/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin exec $@
fi
