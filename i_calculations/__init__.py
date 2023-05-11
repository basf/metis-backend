import os
import sys
import json

from yascheduler import Yascheduler

from i_calculations.xrpd import get_pattern
from i_data import Data_type
from i_structures.topas import ase_to_topas
from i_structures.fullprof import ase_to_fullprof


_scheduler_status_mapping = {
    Yascheduler.STATUS_TO_DO: 25,
    Yascheduler.STATUS_RUNNING: 50,
    Yascheduler.STATUS_DONE: 100,
}

SUPPORTED_ENGINES = ["dummy", "topas", "fullprof"]


class Calc_setup:
    schemata = {}
    templates = {}

    for engine in SUPPORTED_ENGINES:
        with open(
            os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "schemata/%s.json" % engine
            ),
            "r",
        ) as f:
            schemata[engine] = json.loads(f.read())

        with open(
            os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "templates/%s.tpl" % engine
            ),
            "r",
        ) as f:
            templates[engine] = f.read()

    def __init__(self):
        pass

    def get_input(self, engine):
        return Calc_setup.templates.get(engine, Calc_setup.templates["dummy"])

    def get_schema(self, engine):
        return Calc_setup.schemata.get(engine, Calc_setup.schemata["dummy"])

    def preprocess(self, ase_obj, engine, name, **kwargs):
        # FIXME avoid engine file names here
        error = None

        if engine == "topas":

            control_input = self.get_input(engine)
            struct_input = ase_to_topas(ase_obj)

            if kwargs.get("merged"):
                result = {
                    "merged": control_input.replace('#include "structure.inc"', struct_input)
                }
            else:
                result = {
                    "calc.inp": control_input,
                    "structure.inc": struct_input,
                }

        elif engine == "fullprof":

            atoms_input, cell_input = ase_to_fullprof(ase_obj)
            template = self.get_input(engine)
            template = template.replace("{{template.title}}", "Metis")
            template = template.replace("{{template.phase}}", atoms_input)
            template = template.replace("{{template.cell}}", cell_input)
            result = {
                "merged" if kwargs.get("merged") else "calc.pcr": template
            }

        else:
            result = {
                "1.input": self.get_input("dummy"),
                "2.input": self.get_input("dummy") * 2,
                "3.input": self.get_input("dummy") * 3,
            }

        return result, error

    def postprocess(self, engine, data_folder):
        output = dict(metadata={}, content=None, type=Data_type.property)

        parsers = {
            "topas": get_pattern,
            "fullprof": get_pattern,
        }
        default_parser = lambda x: {"content": 42}
        parser = parsers.get(engine, default_parser)
        main_file_asset = None

        for item in os.listdir(data_folder):
            item_path = os.path.join(data_folder, item)
            if not os.path.isfile(item_path):
                continue

            result = parser(item_path)
            if not result:
                continue

            main_file_asset = item_path
            break

        else:
            return (
                None,
                f"Cannot find any results expected for {engine} in {data_folder}",
            )

        output["metadata"]["path"] = main_file_asset
        output["content"] = result["content"]
        if result.get("type"):
            output["type"] = result["type"]

        return output, None


if __name__ == "__main__":
    from ase.spacegroup import crystal

    # test_obj = crystal(
    #    ('Sr', 'Ti', 'O', 'O'),
    #    basis=[(0, 0.5, 0.25), (0, 0, 0), (0, 0, 0.25), (0.255, 0.755, 0)],
    #    spacegroup=140, cellpar=[5.511, 5.511, 7.796, 90, 90, 90], primitive_cell=True
    # )

    setup = Calc_setup()
    # print(setup.get_input('hi'))
    # print(setup.preprocess(test_obj, 'topas', 'Metis test'))
