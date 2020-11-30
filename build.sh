#!/bin/bash

pipenv run pyinstaller --clean *.spec

codesign -s aaron.ciuffo@gmail.com ./dist/folderAudit

pushd ./dist

tar cvzf ../folderAudit_latest.tgz .
popd

#mv /Volumes/GoogleDrive/Team\ Drives/ASH\ Student\ Cumulative\ Folders/PortfolioCreator\ Application/*.zip /Volumes/GoogleDrive/Team\ Drives/ASH\ Student\ Cumulative\ Folders/PortfolioCreator\ Application/Old\ Versions
#zip -j /Volumes/GoogleDrive/Team\ Drives/ASH\ Student\ Cumulative\ Folders/PortfolioCreator\ Application/portfolioCreator_$DATESTR.zip ./dist/portfolioCreator

