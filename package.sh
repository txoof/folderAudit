#!/bin/bash

#pushd ./dist

#tar cvzf ../folderAudit_latest.tgz .

#popd

#git commit -m "refresh tgz" ./folderAudit_latest.tgz

~/bin/develtools/pycodesign.py folderAudit_codesign.ini
if [ $? -eq 0 ] 
then
  git commit -m "refresh package"  folderAudit.pkg
  git push
fi
  echo codesign failed

