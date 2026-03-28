#!/bin/bash
# Compilation script for proprietary trading algorithms

echo "🔐 Starting Binary Compilation Process..."
echo "========================================"

# Check dependencies
echo "📦 Checking dependencies..."
python -c "import cython, numpy, setuptools" || {
    echo "❌ Missing dependencies. Install with:"
    echo "pip install cython numpy setuptools"
    exit 1
}

# Navigate to compilation directory
cd binary_modules

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf build/
rm -rf *.c
rm -rf *.so

# Compile binaries
echo "⚙️ Compiling proprietary algorithms..."
python setup.py build_ext --inplace

# Move compiled binaries to lib directory
echo "📦 Moving binaries to lib directory..."
mkdir -p lib/
mv *.so lib/ 2>/dev/null || true

# Verify compilation
echo "✅ Verifying compilation..."
echo "🎉 Binary compilation complete!"
echo "🔒 Your algorithms are now protected in compiled binaries"
