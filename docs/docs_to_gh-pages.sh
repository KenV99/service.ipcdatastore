#!/usr/bin/bash
rm -rf "C:\Temp\html"
mkdir "C:\Temp\html"
cp -rf ./_build/html/* "C:\Temp\html"
git commit -a
git status
exit