#!/usr/bin/env bash

set -eo pipefail

GRIDCOIN_SOURCE_DIR="$1"

# A bit primitive, we can get much better type hints when the new RPC system is ported.

VERSION=$(grep 'define(_CLIENT_VERSION' $GRIDCOIN_SOURCE_DIR/configure.ac | grep -oE "[0-9]+" | paste -s -d "." | sed 's/.0$//g')

COMMANDS=$(grep -oE '\s*{\s*"[a-zA-Z0-9_]+"\s*,\s*&[a-zA-Z0-9_]+\s*,\s*cat_[a-z]+\s*}' $GRIDCOIN_SOURCE_DIR/src/rpc/server.cpp | grep -oE '"[a-zA-Z0-9]+"')

cat <<EOF
    # Generated for Gridcoin $VERSION

    COMMANDS: Final[frozenset[str]] = frozenset({$(paste -s -d ',' <<< "$COMMANDS")})

EOF

while read command; do

cat <<EOF
    def $command(self, *args: Any) -> T: ...
EOF

done <<< $(sed 's/"//g' <<< $COMMANDS)
