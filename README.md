# Notice

This project might be more awesome: https://github.com/blacktop/darwin-xnu-build

# XNU Build Script

All files will be written into `fakeroot` instead of system path

```shell
# compile xnu kernel
./x.py

# make json compilation database
JSONDB=1 ./x.py

# compile codeql database
./ql.py
```
