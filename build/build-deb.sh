#!/bin/sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
VERSION=$(python3 -c "import retrodeck; print(retrodeck.__version__)" 2>/dev/null || echo 0.1.0)
OUT="$ROOT/build/retrodeck_${VERSION}_amd64"
rm -rf "$OUT" "$ROOT/build/retrodeck_${VERSION}_amd64.deb"
mkdir -p "$OUT/DEBIAN" "$OUT/usr/lib/retrodeck/assets" "$OUT/usr/bin" "$OUT/usr/share/applications" "$OUT/usr/share/icons/hicolor/scalable/apps"
cp -r "$ROOT/retrodeck" "$OUT/usr/lib/retrodeck/"
cp "$ROOT/assets/retrodeck-ambience.wav" "$ROOT/assets/retrodeck-ui-confirm.wav" "$OUT/usr/lib/retrodeck/assets/"
cat > "$OUT/usr/bin/retrodeck" <<'EOF'
#!/bin/sh
export PYTHONPATH=/usr/lib/retrodeck${PYTHONPATH:+:$PYTHONPATH}
exec python3 -m retrodeck "$@"
EOF
chmod 755 "$OUT/usr/bin/retrodeck"
cp "$ROOT/packaging/retrodeck.desktop" "$OUT/usr/share/applications/retrodeck.desktop"
cp "$ROOT/assets/retrodeck.svg" "$OUT/usr/share/icons/hicolor/scalable/apps/retrodeck.svg"
cat > "$OUT/DEBIAN/control" <<EOF
Package: retrodeck
Version: $VERSION
Section: games
Priority: optional
Architecture: amd64
Depends: python3 (>= 3.10)
Maintainer: RetroDeck Project <retrodeck@example.invalid>
Description: Lightweight Linux emulation frontend
 RetroDeck indexes games from multiple folders and launches configured emulators.
EOF
dpkg-deb --build --root-owner-group "$OUT" "$ROOT/build/retrodeck_${VERSION}_amd64.deb"
rm -rf "$OUT"
printf '%s\n' "$ROOT/build/retrodeck_${VERSION}_amd64.deb"
