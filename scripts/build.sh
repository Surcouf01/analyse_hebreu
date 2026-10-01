#!/bin/bash

if [ -d "dist" ]; then
	rm -rf dist
fi

# Build avec PowerShell :
SPEC_TARGET=gui SPEC_MODE=onefile pyinstaller analyse_hebreu.spec --noconfirm
