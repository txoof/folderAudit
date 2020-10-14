# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# see link below for build DistributionNotFound issues
# https://github.com/googleapis/google-api-python-client/issues/876#issuecomment-617248185
from PyInstaller.utils.hooks import copy_metadata
extra_files = copy_metadata('google-api-python-client')
extra_files.append(('./resources', './resources'))

a = Analysis(['folderAudit.py'],

             pathex=['./'],
             binaries=[],
             datas=extra_files,
             hiddenimports=['google-api-python-client', 'googleapiclient'],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='folderAudit',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=True )
