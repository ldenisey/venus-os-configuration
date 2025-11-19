#!/bin/bash
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")

build() {
    if [ -f "$1/CONTROL/prepkg.sh" ]; then
        echo "Executing prepkg.sh script"
        "$1/CONTROL/prepkg.sh"
    fi
    opkg-build "$1"
}

# Build package only if changes are detected
for dir in "$SCRIPT_DIR"/*/; do
    [ -d "$dir" ] || continue

    echo ""
    echo "Evaluating $dir"

    PKG_NAME=$(basename "$dir")
    PKG_HASH_FILE="$SCRIPT_DIR/$PKG_NAME.hash"

    # Compute current hash
    CURRENT_HASH=$(find "$dir" -type f -exec sha256sum {} \; | sort | sha256sum | awk '{print $1}')

    if [ -f "$PKG_HASH_FILE" ]; then
        OLD_HASH=$(cat "$PKG_HASH_FILE")
        if [ "$CURRENT_HASH" != "$OLD_HASH" ]; then
            echo "Hash changed in $PKG_NAME, rebuilding package..."
            build "$dir"
            echo "$CURRENT_HASH" > "$PKG_HASH_FILE"
        else
            echo "No changes in $PKG_NAME, skipping build."
        fi
    else
        echo "No .hash file in $PKG_NAME, building package..."
        build "$dir"
        echo "$CURRENT_HASH" > "$PKG_HASH_FILE"
    fi
done

# Rebuild index files
echo ""
echo "Rebuilding index files..."
opkg-make-index -p Packages "$SCRIPT_DIR"
