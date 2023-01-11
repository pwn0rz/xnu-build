#! /usr/bin/env python3
import os

KDKROOT = '/Library/Developer/KDKs/KDK_13.1_22C65.kdk/'

WORK_DIR = os.environ.get('PWD')
BUILD_DIR = os.environ.get('BUILD_DIR', f'{WORK_DIR}/build')
FAKEROOT_DIR = os.environ.get('FAKEROOT_DIR', f'{WORK_DIR}/fakeroot')
DATABASE_DIR = os.environ.get('DATABASE_DIR', f'{WORK_DIR}/xnu-codeql')

# TARGET_CONFIGS may stop codeql command expandingg
BUILD_CMD = f'{WORK_DIR}/x.py'

# start with a clean build
os.system(f'rm -rf {BUILD_DIR}')
os.system(f'rm -rf {FAKEROOT_DIR}')
os.system(f'rm -rf {DATABASE_DIR}')

os.system(f'codeql database create "{DATABASE_DIR}" --language=cpp -v --command="{BUILD_CMD}"')