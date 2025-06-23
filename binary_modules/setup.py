#!/usr/bin/env python3
"""
Setup script for compiling proprietary trading algorithms
"""

from setuptools import setup, Extension
from Cython.Build import cythonize
import numpy
import os

# Compiler directives for optimization
compiler_directives = {
    'language_level': 3,
    'boundscheck': False,
    'wraparound': False,
    'cdivision': True,
    'initializedcheck': False,
    'nonecheck': False,
    'embedsignature': True
}

# Extensions to compile
extensions = [
    Extension(
        "ai_models_core",
        ["protected_source/ai_models_core.pyx"],
        include_dirs=[numpy.get_include()],
        extra_compile_args=['-O3', '-ffast-math'],
        define_macros=[('NPY_NO_DEPRECATED_API', 'NPY_1_7_API_VERSION')]
    ),
    Extension(
        "risk_management",
        ["protected_source/risk_management.pyx"],
        include_dirs=[numpy.get_include()],
        extra_compile_args=['-O3', '-ffast-math'],
        define_macros=[('NPY_NO_DEPRECATED_API', 'NPY_1_7_API_VERSION')]
    ),
    Extension(
        "signal_generation",
        ["protected_source/signal_generation.pyx"],
        include_dirs=[numpy.get_include()],
        extra_compile_args=['-O3', '-ffast-math'],
        define_macros=[('NPY_NO_DEPRECATED_API', 'NPY_1_7_API_VERSION')]
    ),
    Extension(
        "backtesting_core",
        ["protected_source/backtesting_core.pyx"],
        include_dirs=[numpy.get_include()],
        extra_compile_args=['-O3', '-ffast-math'],
        define_macros=[('NPY_NO_DEPRECATED_API', 'NPY_1_7_API_VERSION')]
    )
]

setup(
    name="proprietary-trading-algorithms",
    ext_modules=cythonize(extensions, compiler_directives=compiler_directives),
    include_dirs=[numpy.get_include()],
    zip_safe=False
)
