#!/bin/bash

if [ -d "dist" ]; then
	rm -rf dist
fi

# Build avec PowerShell :
SPEC_TARGET=gui SPEC_MODE=onedir pyinstaller analyse_hebreu.spec --noconfirm
