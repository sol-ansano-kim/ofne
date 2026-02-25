# 0.2.1
- Prioritize cie_xyz_d65_scene over cie_xyz_d65_display when resolving aka:xyzd65
- Updated parameter widget to use QScrollArea


# 0.2.0
- Added ability to dismiss the pixel inspector with Ctrl + Right Click
- Added shortcut N to create a new note
- The PythonExpression node now accepts 4 inputs
- Moved cli/ui.py to bin/ofne
- bin/ofne now accepts scene files as input
- Updated the OCIO node: removed the role:* default color space entries and added aka:* defaults
- Viewer now automatically casts incoming NumPy data to 32‑bit if it is not already 32‑bit
- Scene files are now always saved in UTF‑8 encoding
- Added support for Path Parameters


# 0.1.1
- Pixel inspector can now be set using Ctrl + Left Click


# 0.1.0
- Initial release
