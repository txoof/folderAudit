#!/bin/bash

pushd ./dist

tar cvzf ../folderAudit_latest.tgz .

popd

git commit -m "refresh tgz" ./folderAudit_latest.tgz
