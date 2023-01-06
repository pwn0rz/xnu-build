#! /usr/bin/env python3
import os

KDKROOT = '/Library/Developer/KDKs/KDK_13.1_22C65.kdk/'

WORK_DIR = os.environ.get('PWD')
BUILD_DIR = os.environ.get('BUILD_DIR', f'{WORK_DIR}/build')
FAKEROOT_DIR = os.environ.get('FAKEROOT_DIR', f'{WORK_DIR}/fakeroot')

SRCROOT = f'{WORK_DIR}/xnu'
OBJROOT = f'{BUILD_DIR}/xnu-codeql.obj'
SYMROOT = f'{BUILD_DIR}/xnu-codeql.sym'
DSTROOT = f'{FAKEROOT_DIR}'

# TARGET_CONFIGS may stop codeql command expandingg
BUILD_CMD = f'make install SDKROOT=macosx ARCH_CONFIGS=ARM64 KERNEL_CONFIGS=RELEASE MACHINE_CONFIGS=VMAPPLE BUILD_WERROR=0 BUILD_LTO=0 SRCROOT={SRCROOT} OBJROOT={OBJROOT} SYMROOT={SYMROOT} DSTROOT={DSTROOT} FAKEROOT={FAKEROOT_DIR} KDKROOT={KDKROOT}'

DATABASE_DIR = f'{WORK_DIR}/xnu-codeql'

print(BUILD_CMD)
os.system(f'rm -rf {OBJROOT}')
os.system(f'rm -rf {SYMROOT}')
os.chdir(SRCROOT)
os.system(f'codeql database create {DATABASE_DIR} --overwrite --language=cpp --command="{BUILD_CMD}"')
