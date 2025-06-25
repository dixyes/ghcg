import datetime
from typing import Literal
import xml.etree.ElementTree
from xml.etree.ElementTree import ElementTree, Element
import os.path
import subprocess
from concurrent.futures import ThreadPoolExecutor
from zipfile import ZipFile

from pydantic import BaseModel, Field

from filaments import bw4levels, bwc4levels
from scad import SINGLE_FILA_MODULE
from svg import newSVGRoot
from typ import ColorFilamentLayer, Contribution, DatedContribution, Style


class GithubStyleParams(BaseModel):
    colorScheme: Literal["light", "dark"] = "light"
    colorOverride: dict[str, list[ColorFilamentLayer]] = {}
    font: str = (
        '-apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans", Helvetica, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji"'
    )
    metricOverride: dict[str, int] = {}
    showLegend: bool = True
    showWeek: bool = True
    showMonth: bool = True
    backgroundColor: str = "ffffff"


class GithubStyle(Style):
    name = "github"
    params: GithubStyleParams

    colors = {
        "light": {
            "background": [],
            "border": bw4levels(4),
            "level0": bw4levels(3),
            "level1": bwc4levels("00FF00", 1),
            "level2": bwc4levels("00FF00", 2),
            "level3": bwc4levels("00FF00", 3),
            "level4": bwc4levels("00FF00", 4),
            "text": [ColorFilamentLayer(l=4, c="000000")],
        }
    }

    metrics = {
        # in pixels, 96 dpi
        "tileWidth": 10,
        "tileBorder": 0.5,
        "tileBorderRadius": 2,
        "tileGap": 3,
        "legendTileGap": 4,
        "border": 1,
        "borderRadius": 6,
        "fontSize": 12,
        "lineHeight": 18,
        "horizonalMargin": 16,
        "verticalMargin": 8,
        "weekTextPadding": 6,
        # width / height
        "fontAspectRatio": 0.5,
    }

    def getColor(self, key: str) -> list[ColorFilamentLayer]:
        if key in self.params.colorOverride:
            return self.params.colorOverride[key]
        return self.colors[self.params.colorScheme].get(key, [])

    def getMetric(self, key: str) -> int | float:
        if key in self.params.metricOverride:
            return self.params.metricOverride[key]
        return self.metrics.get(key, 20)

    def __init__(
        self,
        workdir: str,
        params: str,
        toolPaths: dict[str, str],
        username: str,
    ):
        self.workdir = workdir
        self.params = GithubStyleParams.model_validate_json(params)
        self.toolPaths = toolPaths
        self.username = username

    def drawSVGTile(
        self, x: int, y: int, drawColor: str, svg: Element, borderSVG: Element
    ) -> None:
        # draw tile border
        borderSVG.append(
            Element(
                "rect",
                rx=str(self.getMetric("tileBorderRadius")),
                ry=str(self.getMetric("tileBorderRadius")),
                x=str(x),
                y=str(y),
                width=str(self.getMetric("tileWidth")),
                height=str(self.getMetric("tileWidth")),
                style=f"fill:none;stroke:#d1d9e0;stroke-width:{self.getMetric('tileBorder')};stroke-miterlimit: 1;",
            )
        )
        # draw tile
        svg.append(
            Element(
                "rect",
                rx=str(
                    self.getMetric("tileBorderRadius")
                    - self.getMetric("tileBorder") / 2
                ),
                ry=str(
                    self.getMetric("tileBorderRadius")
                    - self.getMetric("tileBorder") / 2
                ),
                x=str(x + self.getMetric("tileBorder") / 2),
                y=str(y + self.getMetric("tileBorder") / 2),
                width=str(self.getMetric("tileWidth") - self.getMetric("tileBorder")),
                height=str(self.getMetric("tileWidth") - self.getMetric("tileBorder")),
                style=f"fill:#{drawColor};stroke:none;",
            )
        )

    def generateSVGs(self, datedContribs: list[DatedContribution]) -> None:
        width = (
            (self.getMetric("border") * 2)
            + (self.getMetric("horizonalMargin") * 2)
            + (
                self.params.showWeek
                and (
                    self.getMetric("fontSize") * self.getMetric("fontAspectRatio") * 3
                    + self.getMetric("weekTextPadding")
                )
                or 0
            )
            + (self.getMetric("tileWidth") * 53)
            + (self.getMetric("tileGap") * 52)
        )

        height = (
            (self.getMetric("border") * 2)
            + (self.getMetric("verticalMargin") * 2)
            + (self.params.showMonth and self.getMetric("lineHeight") or 0)
            + (self.params.showLegend and self.getMetric("lineHeight") or 0)
            + (self.getMetric("tileWidth") * 7)
            + (self.getMetric("tileGap") * 6)
        )

        backgroundSVG = newSVGRoot(width=width, height=height)
        borderSVG = newSVGRoot(width=width, height=height)
        level0SVG = newSVGRoot(width=width, height=height)
        level1SVG = newSVGRoot(width=width, height=height)
        level2SVG = newSVGRoot(width=width, height=height)
        level3SVG = newSVGRoot(width=width, height=height)
        level4SVG = newSVGRoot(width=width, height=height)
        levelSVGs = [
            level0SVG,
            level1SVG,
            level2SVG,
            level3SVG,
            level4SVG,
        ]
        textSVG = newSVGRoot(width=width, height=height)
        drawColors = [
            "eff2f5",  # level 0
            "aceebb",  # level 1
            "4ac26b",  # level 2
            "2da44e",  # level 3
            "116329",  # level 4
        ]

        gridTopLeft = [
            self.getMetric("border") + self.getMetric("horizonalMargin"),
            self.getMetric("border") + self.getMetric("verticalMargin"),
        ]
        # if show week, add space for week text
        gridTopLeft[0] += (
            self.params.showWeek
            and (
                self.getMetric("fontSize") * self.getMetric("fontAspectRatio") * 3
                + self.getMetric("weekTextPadding")
            )
            or 0
        )
        # if show month, add space for month text
        gridTopLeft[1] += self.params.showMonth and self.getMetric("lineHeight") or 0

        # draw border
        borderSVG.append(
            Element(
                "rect",
                rx=str(self.getMetric("borderRadius")),
                ry=str(self.getMetric("borderRadius")),
                x="0",
                y="0",
                width=str(width),
                height=str(height),
                style=f"fill:none;stroke:#d1d9e0;stroke-width:{self.getMetric('border')};stroke-miterlimit: 1;",
            )
        )

        # draw background
        backgroundSVG.append(
            Element(
                "rect",
                rx=str(self.getMetric("borderRadius")),
                ry=str(self.getMetric("borderRadius")),
                x="0",
                y="0",
                width=str(width),
                height=str(height),
                style=f"fill:#FFFFFF;stroke:none;",
            )
        )

        # draw week text
        if self.params.showWeek:
            halfTileWidth = self.getMetric("tileWidth") / 2
            weekText = Element(
                "text",
                x=str(self.getMetric("border") + self.getMetric("horizonalMargin")),
                y=str(gridTopLeft[1] + (3 * halfTileWidth) + self.getMetric("tileGap")),
                style=f"font-family:'{self.params.font}';font-size:{self.getMetric('fontSize')}px;"
                + "fill:#000000;text-anchor:start;dominant-baseline:middle;",
            )
            weekText.text = "Mon"
            textSVG.append(weekText)

            weekText = Element(
                "text",
                x=str(self.getMetric("border") + self.getMetric("horizonalMargin")),
                y=str(
                    gridTopLeft[1]
                    + (7 * halfTileWidth)
                    + (3 * self.getMetric("tileGap"))
                ),
                style=f"font-family:'{self.params.font}';font-size:{self.getMetric('fontSize')}px;"
                + "fill:#000000;text-anchor:start;dominant-baseline:middle;",
            )
            weekText.text = "Wed"
            textSVG.append(weekText)

            weekText = Element(
                "text",
                x=str(self.getMetric("border") + self.getMetric("horizonalMargin")),
                y=str(
                    gridTopLeft[1]
                    + (11 * halfTileWidth)
                    + (5 * self.getMetric("tileGap"))
                ),
                style=f"font-family:'{self.params.font}';font-size:{self.getMetric('fontSize')}px;"
                + "fill:#000000;text-anchor:start;dominant-baseline:middle;",
            )
            weekText.text = "Fri"
            textSVG.append(weekText)

        legendY = height - self.getMetric("border") - self.getMetric("verticalMargin")
        # draw legend
        if self.params.showLegend:
            moreWidth = (
                self.getMetric("fontSize") * self.getMetric("fontAspectRatio") * 4
            )
            more = Element(
                "text",
                x=str(
                    width
                    - self.getMetric("border")
                    - self.getMetric("horizonalMargin")
                    - moreWidth
                ),
                y=str(legendY),
                style=f"font-family:'{self.params.font}';font-size:{self.getMetric('fontSize')}px;"
                + "fill:#000000;text-anchor:start;dominant-baseline:text-bottom;",
            )
            more.text = "More"
            textSVG.append(more)

            legendsX = (
                width
                - self.getMetric("border")
                - self.getMetric("horizonalMargin")
                - moreWidth
                - (5 * self.getMetric("tileWidth"))
                - (5 * self.getMetric("legendTileGap"))
            )
            legendsY = legendY - self.getMetric("tileWidth")
            for i in range(5):
                drawColor = drawColors[i]
                svg = levelSVGs[i]
                self.drawSVGTile(
                    x=legendsX
                    + i
                    * (self.getMetric("tileWidth") + self.getMetric("legendTileGap")),
                    y=legendsY,
                    drawColor=drawColor,
                    svg=svg,
                    borderSVG=borderSVG,
                )

            # draw less
            less = Element(
                "text",
                x=str(legendsX - self.getMetric("legendTileGap") - moreWidth),
                y=str(legendY),
                style=f"font-family:'{self.params.font}';font-size:{self.getMetric('fontSize')}px;"
                + "fill:#000000;text-anchor:start;dominant-baseline:text-bottom;",
            )
            less.text = "Less"
            textSVG.append(less)

        lastMonth = -1
        weekIndex = 1
        for contrib in datedContribs:
            _, __, weekDay = contrib.date.isocalendar()
            # Github use Sunday as the first day of the week
            if weekDay == 7:
                weekDay = 0
                weekIndex += 1
            x = gridTopLeft[0] + (weekIndex - 1) * (
                self.getMetric("tileWidth") + self.getMetric("tileGap")
            )
            y = gridTopLeft[1] + weekDay * (
                self.getMetric("tileWidth") + self.getMetric("tileGap")
            )

            # draw month label
            if self.params.showMonth and weekDay == 1:  # only draw on Monday
                if contrib.date.month != lastMonth:
                    monthText = Element(
                        "text",
                        x=str(x),
                        y=str(
                            self.getMetric("border")
                            + self.getMetric("verticalMargin")
                            + (self.getMetric("lineHeight") / 2)
                        ),
                        style=f"font-family:'{self.params.font}';font-size:{self.getMetric('fontSize')}px;"
                        + "fill:#000000;text-anchor:start;dominant-baseline:middle;",
                    )
                    monthText.text = contrib.date.strftime("%b")
                    textSVG.append(monthText)
                lastMonth = contrib.date.month

            # draw tile
            drawColor = drawColors[contrib.level]
            svg = levelSVGs[contrib.level]
            self.drawSVGTile(
                x=x,
                y=y,
                drawColor=drawColor,
                svg=svg,
                borderSVG=borderSVG,
            )

        # write svgs
        with open(f"{self.workdir}/background.svg", "wb") as f:
            ElementTree(backgroundSVG).write(f, encoding="utf-8", xml_declaration=True)
        with open(f"{self.workdir}/border.svg", "wb") as f:
            ElementTree(borderSVG).write(f, encoding="utf-8", xml_declaration=True)
        with open(f"{self.workdir}/level0.svg", "wb") as f:
            ElementTree(level0SVG).write(f, encoding="utf-8", xml_declaration=True)
        with open(f"{self.workdir}/level1.svg", "wb") as f:
            ElementTree(level1SVG).write(f, encoding="utf-8", xml_declaration=True)
        with open(f"{self.workdir}/level2.svg", "wb") as f:
            ElementTree(level2SVG).write(f, encoding="utf-8", xml_declaration=True)
        with open(f"{self.workdir}/level3.svg", "wb") as f:
            ElementTree(level3SVG).write(f, encoding="utf-8", xml_declaration=True)
        with open(f"{self.workdir}/level4.svg", "wb") as f:
            ElementTree(level4SVG).write(f, encoding="utf-8", xml_declaration=True)
        with open(f"{self.workdir}/text.svg", "wb") as f:
            ElementTree(textSVG).write(f, encoding="utf-8", xml_declaration=True)

        # for debug
        mergedSVG = newSVGRoot(width=width, height=height)
        for svg in [
            backgroundSVG,
            borderSVG,
            level0SVG,
            level1SVG,
            level2SVG,
            level3SVG,
            level4SVG,
            textSVG,
        ]:
            for elem in svg:
                mergedSVG.append(elem)
        with open(f"{self.workdir}/merged.svg", "wb") as f:
            ElementTree(mergedSVG).write(f, encoding="utf-8", xml_declaration=True)

    def pathSVGs(self) -> list[str]:
        executor = ThreadPoolExecutor(max_workers=os.cpu_count())
        futures = []

        for regionName in self.colors.get("light").keys():
            cmd = [
                self.toolPaths["inkscape"],
                os.path.join(self.workdir, f"{regionName}.svg"),
                "--actions=select-all;object-stroke-to-path;export-text-to-path;export-plain-svg",
                "--export-filename="
                + os.path.join(self.workdir, f"pathed_{regionName}.svg"),
            ]
            # print(f"Running: {' '.join(cmd)}")
            # subprocess.run(cmd, check=True)
            futures.append(
                executor.submit(
                    subprocess.run,
                    cmd,
                    check=True,
                )
            )

        for future in futures:
            future.result()

    def generate3MF(self) -> list[str]:
        content3MF = "// generated by ghcg\n\n"
        content3MF += "layer = 0.2;\n"  # TODO: make this a parameter
        content3MF += "thickness = 2;\n"  # TODO: make this a parameter
        content3MF += f"\n// filaments\n"

        filaments = []
        for regionName in self.colors.get("light").keys():
            colorLayers = self.getColor(regionName)
            if not colorLayers:
                continue
            for colorLayer in colorLayers:
                lowerC = colorLayer.c.lower()
                if lowerC not in filaments:
                    filaments.append(lowerC)

        filaments.sort()

        for index, filamentColor in enumerate(filaments):
            content3MF += f"filament{filamentColor} = {index};\n"
        content3MF += f"backgroundFila = filament{self.params.backgroundColor};\n"

        content3MF += "\n// colors\ncolorMaps = [\n"
        for regionName in self.colors.get("light").keys():
            content3MF += f'    [\n        "{regionName}",\n        [\n'
            layers = self.getColor(regionName)
            currentLayer = 0
            for layer in layers:
                # print(f"Adding {layer.l} layers of color {layer.c} to {regionName}")
                lowerC = layer.c.lower()
                content3MF += (
                    f"            [ {currentLayer}, {layer.l}, filament{lowerC} ],\n"
                )
                currentLayer += layer.l
            content3MF += f"        ]\n    ],\n"
        content3MF += "];\n"

        content3MF += SINGLE_FILA_MODULE % (len(filaments) - 1)

        # write the main scad file
        filamentNames = []
        for filementColor in filaments:
            if filementColor == self.params.backgroundColor:
                continue
            content3MF += (
                f'\ncolor("#{filementColor}") singleFila(filament{filementColor});\n'
            )
            filamentNames.append(f"{filementColor}")
        # backgroundFila
        content3MF += f"\nbackgroundFila();\n"
        filamentNames.append(self.params.backgroundColor)

        with open(f"{self.workdir}/object.scad", "w") as f:
            f.write(content3MF)

        # generate 3MF files
        cmd = [
            self.toolPaths["openscad"],
            "--enable",
            "lazy-union",
            "--backend",
            "Manifold",
            f"{self.workdir}/object.scad",
            "-o",
            f"{self.workdir}/object_.3mf",
        ]
        subprocess.run(cmd, check=True)

        return filamentNames

    def renameObjects(self, year: int, filamentLists: list[str]) -> None:
        with ZipFile(f"{self.workdir}/object_.3mf", "r") as zin:
            with ZipFile(f"{self.workdir}/object.3mf", "w") as zout:
                zout.comment = zin.comment  # preserve the comment
                for item in zin.infolist():
                    if item.filename != "3D/3dmodel.model":
                        zout.writestr(item, zin.read(item.filename))
                        continue
                    with zin.open("3D/3dmodel.model", "r") as modelFile:
                        xml.etree.ElementTree.register_namespace(
                            "",
                            "http://schemas.microsoft.com/3dmanufacturing/core/2015/02",
                        )
                        root = xml.etree.ElementTree.parse(modelFile)
                        title = root.find(
                            './/{http://schemas.microsoft.com/3dmanufacturing/core/2015/02}metadata[@name="Title"]'
                        )
                        title.text = f"{self.username} {year}"
                        for i, filamentColor in enumerate(filamentLists):
                            objectElem = root.find(
                                './/{http://schemas.microsoft.com/3dmanufacturing/core/2015/02}object[@name="'
                                + f"OpenSCAD Model {i + 1}"
                                + '"]'
                            )
                            objectElem.set("name", f"#{filamentColor}")

                        with zout.open("3D/3dmodel.model", "w") as outFile:
                            root.write(outFile, encoding="utf-8", xml_declaration=True)

    def generate(self, contribs: list[Contribution]) -> str:
        datedContribs: list[DatedContribution] = []
        for contrib in contribs:
            date = datetime.date.fromisoformat(contrib.date)
            datedContribs.append(
                DatedContribution(date=date, count=contrib.count, level=contrib.level)
            )

        datedContribs.sort(key=lambda x: x.date)

        self.generateSVGs(datedContribs)
        self.pathSVGs()
        filamentNames = self.generate3MF()
        self.renameObjects(
            year=datedContribs[0].date.year,
            filamentLists=filamentNames,
        )


__style__ = GithubStyle
