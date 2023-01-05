#! /usr/bin/env python3
import os

KDKROOT = '/Library/Developer/KDKs/KDK_13.1_22C65.kdk/'

WORK_DIR = os.environ.get('PWD')
BUILD_DIR = os.environ.get('BUILD_DIR', f'{WORK_DIR}/build')
FAKEROOT_DIR = os.environ.get('FAKEROOT_DIR', f'{WORK_DIR}/fakeroot')

SRCROOT = f'{WORK_DIR}/xnu'
OBJROOT = f'{BUILD_DIR}/obj'
SYMROOT = f'{BUILD_DIR}/sym'
DSTROOT = f'{FAKEROOT_DIR}'

# TARGET_CONFIGS may stop codeql command expandingg
BUILD_CMD = f'make install SDKROOT=macosx ARCH_CONFIGS=ARM64 KERNEL_CONFIGS=RELEASE MACHINE_CONFIGS=VMAPPLE LOGCOLORS=y BUILD_WERROR=0 BUILD_LTO=0 SRCROOT={SRCROOT} OBJROOT={OBJROOT} SYMROOT={SYMROOT} DSTROOT={DSTROOT} FAKEROOT={FAKEROOT_DIR} KDKROOT={KDKROOT}'

print(BUILD_CMD)
os.system(f'rm -r {BUILD_DIR}')
os.system(f'codeql database create xnu-codeql --language=cpp  --source-root {SRCROOT} --command="{BUILD_CMD}"')