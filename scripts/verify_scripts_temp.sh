#!/bin/bash

echo "=== Python Scripts Verification ==="
for f in *.py; do
    if [ -f "$f" ]; then
        if python3 -c "import py_compile; py_compile.compile('$f', cfile='/dev/null', doraise=True)" 2>/dev/null; then
            echo "[PASS] $f"
        else
            echo "[FAIL] $f"
            # Run again to show error
            python3 -m py_compile "$f"
        fi
    fi
done

echo ""
echo "=== Shell Scripts Verification ==="
for f in *.sh; do
    if [ -f "$f" ]; then
        if bash -n "$f"; then
            echo "[PASS] $f"
        else
            echo "[FAIL] $f"
        fi
    fi
done
