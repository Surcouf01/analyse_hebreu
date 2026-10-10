#!bash
version=`cat VERSION`
git tag v$version -d
git push origin --delete v$version
