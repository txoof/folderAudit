# folderAudit
Audit a google drive folder and all sub-folders for ownership, size and other properties.

This is particularly useful when preparing to move a folder into a Google Shared Drive

## Building
There appears to be some sort of [bug](https://github.com/googleapis/google-api-python-client/issues/876#issuecomment-708379457) in the `google-api-python-client` when used with pyinstaller.

The following needs to be added to the `.spec` file:
```
from PyInstaller.utils.hooks import copy_metadata # import the utils.hooks.copy_metadata
extra_files = copy_metadata('google-api-python-client') # gather the appropriate metadata
extra_files.append(('./resources', './resources')) # append any other datas 

a = Analysis(['folderAudit.py'],

             pathex=['./'], # set to ./ to avoid path issues
             binaries=[],
             datas=extra_files, # add the extra_files here
             hiddenimports=['google-api-python-client', 'googleapiclient'], # this does not appear to work, but included for completeness
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
```

