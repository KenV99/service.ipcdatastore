#!/usr/bin/bash
rm -rf "C:\Temp\html"
mkdir "C:\Temp\html"
cp -rf ./_build/html/* "C:\Temp\html"
cp .nojekyll "C:\Temp\html"
cp .gitignore "C:\Temp\html"
git commit -a -m "Commit before gh-pages update"
git checkout gh-pages
rm -rf *
cp -rf "C:\Temp\html\*" .
git add -A
git commit -a -m "Update gh-pages"
git push origin gh-pages
git checkout master
exit