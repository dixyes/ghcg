from xml.etree import ElementTree


def newSVGRoot(width: int, height: int) -> ElementTree.Element:
    """Create a new SVG root element with the appropriate namespace."""
    # docstring
    svg = ElementTree.Element(
        "svg",
        xmlns="http://www.w3.org/2000/svg",
        viewBox=f"0 0 {width} {height}",
        width=str(width),
        height=str(height),
        version="1.1",
    )
    return svg


if __name__ == "__main__":
    svg_root = newSVGRoot(100, 100)
    print(ElementTree.tostring(svg_root, encoding="unicode"))
