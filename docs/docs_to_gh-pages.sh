#!/usr/bin/bash
git commit -a -m "Commit before gh-pages update"
git checkout gh-pages
git rm -rf *
cp -rf "C:\Temp\html\*" .
git add -A
git commit -a -m "Update gh-pages"
git push origin gh-pages
git checkout master
exit