# Log format
Some of the most seen file system operations are listed below, files are always logged as inodes, use juicefs info [INODE] to lookup information on inode.

# Basic format, may vary for different operations:
# [UID,GID,PID] [operation] [arguments (vary for different operations)]: [OK] [debug info] <duration (s)>

# open, arguments (inode, flags)
[uid:0,gid:0,pid:1631098] open (38597810,0x8000): OK (38597810,[-rw-r--r--:0100644,1,0,0,1650446639,1650446639,1650446639,212]) (direct_io:0,keep_cache:1) [handle:00007869] <0.010293>

# read, arguments (inode, size, offset, file-handler)
[uid:0,gid:0,pid:0] read (148199375,69632,1439510528,18333): OK (69632) <0.001047>

# getattr, arguments (inode)
[uid:0,gid:0,pid:1631098] getattr (1): OK (1,[drwxrwxrwx:0040777,19977521,0,0,1634886025,1663052916,1663052916,9265059409920]) <0.000002>

# statfs, arguments (inode)
[uid:0,gid:0,pid:1240206] statfs (1): OK (47474945257472,62476217520128,1165873,4293801422) <0.000345>

# setattr, arguments (inode, setmask, mode)
[uid:0,gid:0,pid:1631098] setattr (45758905,0x1,[mode=-rw-r--r--:00644;]): OK (45758905,[-rw-r--r--:0100644,1,0,0,1664165438,1664165438,1664165438,4096]) <0.011076>

# create, arguments (parent-inode, name, mode, umask)
[uid:0,gid:0,pid:1631098] create (1,.temp.sh.swp,-rw-------:0100600,00000,0x280C2): OK (45758905,[-rw-------:0100600,1,0,0,1664165438,1664165438,1664165438,0]) [handle:00007868] <0.011117>

# write, arguments (inode, size, offset, file-handler)
[uid:0,gid:0,pid:1631098] write (45758905,4096,0,18333): OK <0.000040>

# unlink, arguments (parent-inode, name)
[uid:0,gid:0,pid:1631098] unlink (1,temp.sh~): OK <0.011033>

# flush, arguments (inode, file-handler)
[uid:0,gid:0,pid:1631098] flush (45758905,18333): OK <0.030459>