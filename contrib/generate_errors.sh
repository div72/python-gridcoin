#!/usr/bin/env bash

set -eo pipefail

GRIDCOIN_SOURCE_DIR="$1"

# A bit primitive, we can get much better type hints when the new RPC system is ported.

VERSION=$(grep 'define(_CLIENT_VERSION' $GRIDCOIN_SOURCE_DIR/configure.ac | grep -oE "[0-9]+" | paste -s -d "." | sed 's/.0$//g')

ERRORS=$(grep -ozP 'enum RPCErrorCode\s*{[^{]*?}' ~/dev/Gridcoin-Research/src/rpc/protocol.h | grep -aoE 'RPC_[a-zA-Z0-9_]+\s*=\s*-[0-9]+' | sed -E -e 's/\s*=\s*/ /g' -e 's/_([a-zA-Z0-9])([a-zA-Z0-9]+)/\u\1\L\2\E/g' -e 's/RPC([a-zA-Z0-9]+)/\1Error/g' -e 's/ErrorError/Error/g' -e 's/TypeError/RPCTypeError/g')

echo "# Generated for Gridcoin $VERSION"

while read error_name error_code; do

cat <<EOF
class $error_name(WalletRPCException, code=$error_code):
  pass

EOF

done <<< "$ERRORS"
