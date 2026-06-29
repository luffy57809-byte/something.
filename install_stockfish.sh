#!/bin/bash
mkdir -p bin
if [ ! -f bin/stockfish ]; then
    echo "Downloading Stockfish..."
    wget -q https://github.com/official-stockfish/Stockfish/releases/download/sf_16/stockfish-ubuntu-x86-64.tar -O /tmp/stockfish.tar
    tar -xf /tmp/stockfish.tar -C /tmp/
    cp /tmp/stockfish/stockfish-ubuntu-x86-64 bin/stockfish
    chmod +x bin/stockfish
    echo "Stockfish installed at bin/stockfish"
fi
