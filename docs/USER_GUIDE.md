# User guide

The dashboard, explorer, target information, terminal, operation log, and
progress panels are dockable through Qt's standard docking controls. Select a
profile in Device Database to inspect its support level. Only a profile with a
validated algorithm, declared operation, and matching firmware capability may
pass the programmer gate.

Opening a file is a local operation. Intel HEX files retain their lowest
address and fill gaps with `0xFF`; they are not silently treated as a
contiguous zero-based image.
