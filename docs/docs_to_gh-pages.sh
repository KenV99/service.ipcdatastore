#!/usr/bin/bash
rm -rf "C:\Temp\html"
mkdir "C:\Temp\html"
cp -rf ./_build/html/* "C:\Temp\html"
git commit -a -m "Commit before gh-pages update"
git checkout gh-pages
ls
exit