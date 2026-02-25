# OFNE

OFNE is a node-based image processing software

![demo](https://github.com/user-attachments/assets/7393e76a-30c6-41bd-916f-263a291475ab)


## Viewport Controls
- F: Fit the viewport to the image
- Ctrl + Left Click: Place a Pixel Inspector
- Ctrl + Right Click: Remove the Pixel Inspector
- Middle Click or Alt + Left Click: Pan the viewport
- Mouse Wheel: Zoom in/out


## Node Graph Controls
- Tab: Create a new node
- F: Fit the graph to the all(selected) node(s)
- B: Bypass the selected node(s)
- N: Add a note for writing comments
- Delete: Delete selected node(s) or connection(s)
- Ctrl + C / Ctrl + V: Copy and Paste node(s)
- V: Connect the selected node to the Viewer
- Middle Click or Alt + Left Click: Pan the graph
- Mouse Wheel: Zoom in/out
- Drag & Drop an image file: Create a ReadImage node

## Path Parameter

A path parameter that supports embedding environment variables

Environment variables can be referenced using ${VAR_NAME}
```python
${TMP}/some_image.exr
```

${OFSN} refers to the directory of the currently opened scene file
```python
${OFSN}/some_image.exr
```

## PythonExpression

### Inputs

Automatically provided by the program

- inPackets : A container of input packets, Packets can be accessed by index e.g. inPackets.packet(0).data(). data() returns a NumPy array
- oiio : OpenImageIO library
- ocio : PyOpenColorIO library
- np : NumPy library
- Packet : Packet class

### Output

The expression must produce outPacket

- outPacket: A Packet constructed from the processed result

```python
in_data = inPackets.packet(0).data()
in_shape = in_data.shape
random_data = np.random.rand(in_shape[0], in_shape[1], in_shape[2]).astype(np.float32)
outPacket = Packet(data=in_data + random_data)
```


## Custom Plugin

### OFNE_PLUGIN_PATH
Custom plugins placed in directories listed in the OFNE_PLUGIN_PATH environment variable will be automatically discovered and loaded.


### Plugin class interface
- needs(): Returns the number of input packets the operator expects.
- packetable(): Returns whether the operator produces an output packet (packet-generating).
- operate(params, packetArray): The function that performs the computation. If packetable() is True, return a OFnPacket(...). If packetable() is False, return nothing (no packet)

/some/plugin/dir/my_awesome_plugin.py

```python
from ofne import plugin

class Multy2(plugin.OFnOp):
    def params(self):
        return [
            plugin.OFnParamBool("switch", default=True)
        ]

    def needs(self):
        # Number of input packets required
        return 1

    def packetable(self):
        # Whether this op produces an output Packet
        return True

    def operate(self, params, packetArray):
        # Access the first input packet's data (NumPy array)
        data = packetArray.packet(0).data()

        if not params.get("switch"):
            return plugin.OFnPacket(data=data)
        else:
            return plugin.OFnPacket(data=data * 2)
```

set OFNE_PLUGIN_PATH=/some/plugin/dir<br>
or<br>
export OFNE_PLUGIN_PATH=/some/plugin/dir<br>



## Requires
numpy

OpenImageIO (python binding)

OpenColorIO 2+ (python binding)

PySide 6.7+

## TODO
group, dot, packet viewer<br>
improve item selection<br>
cmd<br>
parameter update<br>
