import os
import datetime
from argparse import ArgumentParser, Namespace
import pkgutil

import requests

from typ import ContributionData


class ContributionGraphGenerator:
    def __init__(self, args: Namespace):
        self.dataDir = args.data
        self.outputDir = args.output
        self.apiEndpoint = args.apiEndpoint
        self.noCache = args.noCache
        self.username = args.USERNAME[0]
        self.year = args.YEAR
        self.openscadPath = args.openscad
        self.inkscapePath = args.inkscape

        self.styleName = args.style
        self.styleParams = args.styleParams

        self.workdir = os.path.join(self.outputDir, f"{self.username}-{self.year}")

        # import all styles from styles directory
        self.styles = {}
        for importer, module_name, _ in pkgutil.iter_modules(["styles"], "."):
            mod = importer.find_spec(module_name).loader.load_module(module_name)
            style = getattr(mod, "__style__", ())
            if style:
                self.styles[style.name] = style

    def fetchData(self, username: str) -> dict:
        if not os.path.exists(self.dataDir):
            os.makedirs(self.dataDir)

        fn = os.path.join(self.dataDir, f"{username}.json")
        if (not self.noCache) and os.path.exists(fn):
            with open(fn, "r") as f:
                data = ContributionData.model_validate_json(f.read())
                return data

        response = requests.get(f"{self.apiEndpoint}/{username}")
        if response.status_code != 200:
            raise Exception(f"Failed to fetch data from {self.apiEndpoint}")

        data = ContributionData.model_validate_json(response.text)
        open(fn, "w").write(data.model_dump_json(indent=2))

        return data

    def generate(self) -> None:
        contribs = []
        data = self.fetchData(self.username)
        for contrib in data.contributions:
            date = datetime.datetime.fromisoformat(contrib.date)
            if date.year != self.year:
                continue
            contribs.append(contrib)

        if not os.path.exists(self.workdir):
            os.makedirs(self.workdir, exist_ok=True)

        style = self.styles[self.styleName](
            self.workdir,
            self.styleParams,
            toolPaths={
                "openscad": self.openscadPath,
                "inkscape": self.inkscapePath,
            },
            username=self.username,
        )
        style.generate(contribs)

    @classmethod
    def main(cls) -> None:
        defaultOpenscadPath = (
            "openscad"
            if os.name != "nt"
            else "C:\\Program Files\\OpenSCAD (Nightly)\\openscad.com"
        )
        defaultInkscapePath = (
            "inkscape"
            if os.name != "nt"
            else "C:\\Program Files\\Inkscape\\bin\\inkscape.com"
        )

        parser = ArgumentParser()
        parser.add_argument("--data", help="Path to the data directory", default="data")
        parser.add_argument(
            "--output",
            help="Path to the output directory",
            default="output",
        )
        parser.add_argument(
            "--apiEndpoint",
            help="API endpoint to use",
            default="https://github-contributions-api.jogruber.de/v4",
        )
        parser.add_argument(
            "--noCache",
            action="store_true",
            help="Disable caching of fetched data",
        )
        parser.add_argument(
            "--style",
            help="Style parameters for the graph",
            default="github",
        )
        parser.add_argument(
            "--styleParams",
            help="Style parameters for the graph in JSON format",
            default="{}",
        )
        parser.add_argument(
            "--openscad",
            help="Path to the OpenSCAD executable",
            default=defaultOpenscadPath,
        )
        parser.add_argument(
            "--inkscape",
            help="Path to the Inkscape executable",
            default=defaultInkscapePath,
        )
        parser.add_argument(
            "USERNAME",
            help="GitHub username to fetch contributions for",
            nargs=1,
        )
        parser.add_argument(
            "YEAR",
            help="Year for generate",
            type=int,
            nargs="?",
            default=datetime.datetime.now().year - 1,
        )

        args = parser.parse_args()
        generator = cls(args)
        # print(generator.fetchData(args.USERNAME[0]))
        generator.generate()


if __name__ == "__main__":
    ContributionGraphGenerator.main()
