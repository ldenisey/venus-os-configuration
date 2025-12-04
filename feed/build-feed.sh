#!/bin/bash
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")

build() {
    if [ -f "$1/src/CONTROL/prepkg.sh" ]; then
        echo "Executing prepkg.sh script"
        chmod +x "$1/src/CONTROL/prepkg.sh"
        "$1/src/CONTROL/prepkg.sh"
        ret=$?
        if [ $ret -ne 0 ]; then
            echo "prepkg.sh script failed"
            return $ret
        fi
    fi
    opkg-build "$1/src"
}

# Build package only if changes are detected
for dir in "$SCRIPT_DIR"/*; do
    [ -d "$dir" ] || continue

    echo ""
    echo "Evaluating $dir"

    PKG_NAME=$(basename "$dir")
    PKG_HASH_FILE="$SCRIPT_DIR/$PKG_NAME.hash"

    # Compute current hash
    CURRENT_HASH=$(find "$dir/src" -type f -exec sha256sum {} \; | sort | sha256sum | awk '{print $1}')

    OLD_HASH=""
    if [ -f "$PKG_HASH_FILE" ]; then
        OLD_HASH=$(cat "$PKG_HASH_FILE")
    fi
    if [ "$CURRENT_HASH" != "$OLD_HASH" ]; then
        echo "Hash changed in $PKG_NAME, rebuilding package..."
        build "$dir"
        ret=$?
        if [ $ret -ne 0 ]; then
            echo "Build failed for $PKG_NAME"
        else
            echo "$CURRENT_HASH" > "$PKG_HASH_FILE"
        fi
    else
        echo "No changes in $PKG_NAME, skipping build."
    fi
done

# Rebuild index files
echo ""
echo "Rebuilding index files..."
rm "$SCRIPT_DIR"/Package*
opkg-make-index -p "$SCRIPT_DIR/Packages" "$SCRIPT_DIR"
mv -f *.ipk "$SCRIPT_DIR/" # No opkg-make-index option to specify output dir
