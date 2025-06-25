
SINGLE_FILA_MODULE = '''

module singleFila(filaIndex) {
    for (colorIndex = [0 : len(colorMaps) - 1]) {
        colorMap = colorMaps[colorIndex];
        colorName = colorMap[0];
        layers = colorMap[1];
        for (data = layers) {
            startLayer = data[0];
            layerCount = data[1];
            if (
                filaIndex == data[2] &&
                backgroundFila != data[2]
            ) {
                translate([0, 0, thickness - ((startLayer + layerCount) * layer)])
                    // 0.01 is a hack to avoid the issue with CGALNefGeometry
                    linear_extrude(height = (layerCount * layer) + 0.01)
                        import(file = str("pathed_", colorName, ".svg"), dpi = 96);
            }
        }
    }
}

module backgroundFila() {
    difference() {
        linear_extrude(height = thickness)
            import(file = "pathed_background.svg", dpi = 96);
        union() {
            for (filaIndex = [0 : %d]) {
                if (filaIndex != backgroundFila) {
                    singleFila(filaIndex);
                }
            }
        }
    }
}

'''
