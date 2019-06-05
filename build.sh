#!/bin/bash
APPNAME="folderAudit"
DATESTR=`date +%F_%H.%M`

pipenv run  pyinstaller --clean *.spec
#mv /Volumes/GoogleDrive/Team\ Drives/ASH\ Student\ Cumulative\ Folders/PortfolioCreator\ Application/*.zip /Volumes/GoogleDrive/Team\ Drives/ASH\ Student\ Cumulative\ Folders/PortfolioCreator\ Application/Old\ Versions
#zip -j /Volumes/GoogleDrive/Team\ Drives/ASH\ Student\ Cumulative\ Folders/PortfolioCreator\ Application/portfolioCreator_$DATESTR.zip ./dist/portfolioCreator

