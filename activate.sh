#!/bin/bash
# Expose conda environment headers and libs to the C/C++ compiler
export CFLAGS="-I${CONDA_PREFIX}/include ${CFLAGS}"
export CXXFLAGS="-I${CONDA_PREFIX}/include ${CXXFLAGS}"
export LDFLAGS="-L${CONDA_PREFIX}/lib -Wl,-rpath,${CONDA_PREFIX}/lib ${LDFLAGS}"