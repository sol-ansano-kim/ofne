def MainWindow(scene=None, parent=None):
    from . import window

    return window.OFnUIMain(scenePath=scene, parent=parent)
