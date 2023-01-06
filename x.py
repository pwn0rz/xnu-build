#! /usr/bin/env python3
import os
import pathlib
import re
import subprocess
import sys
from typing import List

'''
It's 2020s and let's using python as basic build system
'''

GITHUB_BASE = 'https://github.com/apple-oss-distributions'
GITHUB_RAW_BASE = 'https://raw.githubusercontent.com/apple-oss-distributions'

WORK_DIR = os.environ.get('PWD')
BUILD_DIR = os.environ.get('BUILD_DIR', f'{WORK_DIR}/build')
FAKEROOT_DIR = os.environ.get('FAKEROOT_DIR', f'{WORK_DIR}/fakeroot')

# upstream gits: https://raw.githubusercontent.com/apple-oss-distributions/distribution-macOS/macos-131/release.json
#MACOS_VERSION = 'macos-131'
KDKROOT = '/Library/Developer/KDKs/KDK_13.1_22C65.kdk/'
XNU_VERSION = 'xnu-8792.61.2'
LIBDISPATCH_VERSION = 'libdispatch-1412'
AVAILABILITYVERSIONS_VERSION = 'AvailabilityVersions-112'
LIBPLATFORM_VERSION = 'libplatform-288'
DTRACE_VERSION = 'dtrace-388'

def exec_cmd(cmd : List[str], at_dir=WORK_DIR):
    old_dir = os.curdir
    os.chdir(at_dir)
    output = subprocess.check_output(cmd).decode(sys.stdout.encoding).rstrip()
    os.chdir(old_dir)
    return output

def shell(cmd):
    r = os.system(cmd)
    if r != 0:
        print(f'Non-zero({r}) exit for command "{cmd}"')
        sys.exit(r)

def sed(filepath : str, line_pattern : str, replace_pattern : str, replace : str):
    f = open(filepath, 'r')
    old_lines = f.readlines()
    f.close()

    new_lines = []
    line_reg = re.compile(line_pattern)
    replace_reg = re.compile(replace_pattern)
    for i in old_lines:
        line = i
        if line_reg.match(i):
            line = replace_reg.sub(replace, i)
            print(f'{i} => {line}')
        new_lines.append(line)
        

    f = open(filepath, 'w+')
    f.writelines(new_lines)
    f.close()
    

def fetch_content(repo : str, tag : str):
    SOURCE_DIR = f'{WORK_DIR}/{repo}'
    REPO_DIR = f'{GITHUB_BASE}/{repo}.git'

    if pathlib.Path(SOURCE_DIR).exists():
        # do pull and 
        local_tag = exec_cmd(['git', 'describe', '--tags'], SOURCE_DIR)
        if local_tag == tag:
            return # already clone
        else:
            shell('rm -r {}') # delete and clone

    shell(f'git clone --branch {tag} {REPO_DIR} {SOURCE_DIR}')

# get source code
fetch_content('xnu', XNU_VERSION)
fetch_content('libdispatch', LIBDISPATCH_VERSION)
fetch_content('AvailabilityVersions', AVAILABILITYVERSIONS_VERSION)
fetch_content('libplatform', LIBPLATFORM_VERSION)
fetch_content('dtrace', DTRACE_VERSION)

# check kdk install
if not pathlib.Path(KDKROOT).exists():
    print(f'YOU MUST HAVE KDK INSTALLED AT {KDKROOT}')
    print('download from: https://developer.apple.com/download/more/')
    sys.exit(1)

KERNEL_FRAMEWORK_ROOT = '/System/Library/Frameworks/Kernel.framework/Versions/A'

# apply patches
# dtrace patch
sed(f'{WORK_DIR}/dtrace/config/base.xcconfig', '^SDKROOT = macosx.internal$', 'macosx.internal', 'macosx')
sed(f'{WORK_DIR}/dtrace/config/base.xcconfig', '^CODE_SIGN_IDENTITY.*', '.*', '')

# xnu headers patch
sed(f'{WORK_DIR}/xnu/bsd/sys/make_symbol_aliasing.sh', '^AVAILABILITY_PL=.*', r'\$\{.*\}', '${FAKEROOT}')

# libsyscall patch
sed(f'{WORK_DIR}/xnu/libsyscall/Libsyscall.xcconfig', '#include.*BSD.xcconfig.*', '.*', '')

# libfirehose_kernel patch
sed(f'{WORK_DIR}/libdispatch/xcodeconfig/libfirehose_kernel.xcconfig', '^HEADER_SEARCH_PATHS.*', '\$\(SDKROOT\)/System/Library/Frameworks/Kernel.framework/PrivateHeaders', '$(FAKEROOT)/System/Library/Frameworks/Kernel.framework/PrivateHeaders')
sed(f'{WORK_DIR}/libdispatch/xcodeconfig/libfirehose_kernel.xcconfig', '^HEADER_SEARCH_PATHS.*', '\$\(SDKROOT\)/usr/local/include', '$(FAKEROOT)/usr/local/include')

# xnu build patch
sed(f'{WORK_DIR}/xnu/makedefs/MakeInc.def', '^LDFLAGS_KERNEL_SDK\s=', 'SDKROOT', 'FAKEROOT')
sed(f'{WORK_DIR}/xnu/makedefs/MakeInc.def', '^INCFLAGS_SDK\s=', 'SDKROOT', 'FAKEROOT')

DSTROOT = f'{FAKEROOT_DIR}'
os.environ['FAKEROOT'] = FAKEROOT_DIR

# dtrace
if not pathlib.Path(f'{FAKEROOT_DIR}/usr/local/bin/ctfmerge').exists():
    SRCROOT = f'{WORK_DIR}/dtrace'
    OBJROOT = f'{BUILD_DIR}/dtrace.obj'
    SYMROOT = f'{BUILD_DIR}/dtrace.sym'
    os.chdir(f'{SRCROOT}')
    shell(f'xcodebuild install -target ctfconvert -target ctfdump -target ctfmerge ARCHS="arm64" OBJROOT={OBJROOT} SYMROOT={SYMROOT} DSTROOT={DSTROOT}')
    os.chdir(f'{WORK_DIR}')
else:
    print('skip building dtrace')

# AvailabilityVersions
if not pathlib.Path(f'{FAKEROOT_DIR}{KERNEL_FRAMEWORK_ROOT}/Headers/AvailabilityVersions.h').exists():
    print('building AvailabilityVersions...')
    SRCROOT = f'{WORK_DIR}/AvailabilityVersions'
    OBJROOT = f'{BUILD_DIR}/AvailabilityVersions.obj'
    SYMROOT = f'{BUILD_DIR}/AvailabilityVersions.sym'
    os.chdir(SRCROOT)
    shell(f'make install OBJROOT=${OBJROOT} SYMROOT={SYMROOT} DSTROOT={DSTROOT}')
    os.chdir(f'{WORK_DIR}')
else:
    print('skip building AvailabilityVersions...')

# XNU headers
if not pathlib.Path(f'{FAKEROOT_DIR}{KERNEL_FRAMEWORK_ROOT}/PrivateHeaders').exists():
    print('install XNU headers...')
    SRCROOT = f'{WORK_DIR}/xnu'
    OBJROOT = f'{BUILD_DIR}/xnu-hdrs.obj'
    SYMROOT = f'{BUILD_DIR}/xnu-hdrs.sym'
    os.chdir(SRCROOT)
    shell(f'make installhdrs SDKROOT=macosx TARGET_CONFIGS="RELEASE ARM64 VMAPPLE" OBJROOT={OBJROOT} SYMROOT={SYMROOT} DSTROOT={DSTROOT}')
    os.chdir(f'{WORK_DIR}')
else:
    print('skip installing XNU headers...')

# libsyscall headers
if not pathlib.Path(f'{FAKEROOT_DIR}/usr/include/os/proc.h').exists():
    print('install libsyscall headers...')
    SRCROOT = f'{WORK_DIR}/xnu/libsyscall'
    OBJROOT = f'{BUILD_DIR}/libsyscall.obj'
    SYMROOT = f'{BUILD_DIR}/libsyscall.sym'
    os.chdir(f'{SRCROOT}')
    shell(f'xcodebuild installhdrs -sdk macosx OBJROOT={OBJROOT} SYMROOT={SYMROOT} DSTROOT={DSTROOT} FAKEROOT={FAKEROOT_DIR}')
    os.chdir(f'{WORK_DIR}')
else:
    print('skip install libsyscall headers...')

# libplatform
print('install libplatform private headers...')
SRCROOT = f'{WORK_DIR}/libplatform'
os.chdir(f'{SRCROOT}')
shell(f'ditto {SRCROOT}/include ${DSTROOT}/usr/local/include')
shell(f'ditto {SRCROOT}/private ${DSTROOT}/usr/local/include')
os.chdir(f'{WORK_DIR}')

# libfirehose_kernel
if not pathlib.Path(f'{FAKEROOT_DIR}/usr/local/lib/kernel/libfirehose_kernel.a').exists():
    print('build libfirehose_kernel...')
    SRCROOT = f'{WORK_DIR}/libdispatch'
    OBJROOT = f'{BUILD_DIR}/libfirehose_kernel.obj'
    SYMROOT = f'{BUILD_DIR}/libfirehose_kernel.sym'
    os.chdir(f'{SRCROOT}')
    shell(f'xcodebuild install -target libfirehose_kernel -sdk macosx ARCHS="arm64e" VALID_ARCHS="arm64e" OBJROOT={OBJROOT} SYMROOT={SYMROOT} DSTROOT={DSTROOT} FAKEROOT={FAKEROOT_DIR}')
    os.chdir(f'{WORK_DIR}')

    # WTF is /usr/local/lib/kernel/liblibfirehose_kernel.a
    if pathlib.Path(f'{FAKEROOT_DIR}/usr/local/lib/kernel/liblibfirehose_kernel.a').exists():
        shell(f'mv {FAKEROOT_DIR}/usr/local/lib/kernel/liblibfirehose_kernel.a {FAKEROOT_DIR}/usr/local/lib/kernel/libfirehose_kernel.a')
else:
    print('skip build libfirehose_kernel...')

# xnu kernel
print('build xnu kernel...')
SRCROOT = f'{WORK_DIR}/xnu'
OBJROOT = f'{BUILD_DIR}/xnu.obj'
SYMROOT = f'{BUILD_DIR}/xnu.sym'
os.chdir(f'{SRCROOT}')
shell(f'make install SDKROOT=macosx TARGET_CONFIGS="RELEASE ARM64 VMAPPLE" LOGCOLORS=y BUILD_WERROR=0 BUILD_LTO=0 SRCROOT={SRCROOT} OBJROOT={OBJROOT} SYMROOT={SYMROOT} DSTROOT={DSTROOT} FAKEROOT={FAKEROOT_DIR} KDKROOT={KDKROOT}')

# this would make codeql/clangd/ccls happy
print('build json compilation database...')
OBJROOT = f'{BUILD_DIR}/xnu-compiledb.obj'
SYMROOT = f'{BUILD_DIR}/xnu-compiledb.sym'
os.system(f'make SDKROOT=macosx TARGET_CONFIGS="RELEASE ARM64 VMAPPLE" LOGCOLORS=y BUILD_WERROR=0 BUILD_LTO=0 BUILD_JSON_COMPILATION_DATABASE=1 SRCROOT={SRCROOT} OBJROOT={OBJROOT} SYMROOT={SYMROOT} DSTROOT={DSTROOT} FAKEROOT={FAKEROOT_DIR} KDKROOT={KDKROOT}')
JSON_COMPILE_DB = exec_cmd(['find', OBJROOT, '-name', 'compile_commands.json'], WORK_DIR)
print(f'copy json compilation database into {SRCROOT}...')
shell(f'cp -f {JSON_COMPILE_DB} {SRCROOT}')