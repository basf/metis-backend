import os
import sys
import json

from yascheduler import Yascheduler

from metis_backend.calculations.xrpd import get_pattern, export_pattern, get_topas_output, get_topas_error
from metis_backend.datasources import Data_type
from metis_backend.datasources.fmt import is_ase_obj
from metis_backend.structures.topas import ase_to_topas, get_topas_keyword
from metis_backend.structures.fullprof import ase_to_fullprof


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

    def preprocess(self, calc_obj, engine, name, **kwargs):
        # FIXME avoid engine file names here
        error = None

        if engine == "topas":

            ext_input = ""

            if is_ase_obj(calc_obj):
                control_input = self.get_input(engine)
                struct_input = ase_to_topas(calc_obj)

            else:
                control_input = calc_obj
                struct_input = ""

            for keyword in ('xdd "', "macro filename "):
                if keyword in control_input:
                    fname = get_topas_keyword(control_input, keyword)

                    if kwargs.get("db") and not kwargs.get("merged"):
                        item = kwargs["db"].search_item(os.path.basename(fname), name=True)
                        if not item or item["type"] != Data_type.pattern:
                            return None, "Included file %s not found" % fname

                        try: ext_input = export_pattern(json.loads(item["content"]))
                        except Exception: return None, "Sorry cannot show erroneous format"

                    control_input = control_input.replace(fname, "input.xy") # NB see yascheduler.conf
                    break

            for keyword in ('out "', "macro outname "):
                if keyword in control_input:
                    fname = get_topas_keyword(control_input, keyword)
                    control_input = control_input.replace(fname, "calc.txt") # NB see yascheduler.conf
                    break

            if kwargs.get("merged"):
                compiled = {
                    "merged": control_input.replace('#include "structure.inc"', struct_input)
                }

            else:
                compiled = {
                    "calc.inp": control_input,
                    "structure.inc": struct_input,
                    "input.xy": ext_input,
                }

        elif engine == "fullprof":

            if not is_ase_obj(calc_obj):
                return None, "FullProf inputs not supported"

            atoms_input, cell_input = ase_to_fullprof(calc_obj)
            template = self.get_input(engine)
            template = template.replace("{{template.title}}", "Metis")
            template = template.replace("{{template.phase}}", atoms_input)
            template = template.replace("{{template.cell}}", cell_input)
            compiled = {
                "merged" if kwargs.get("merged") else "calc.pcr": template
            }

        else:
            compiled = {
                "1.input": self.get_input("dummy"),
                "2.input": self.get_input("dummy") * 2,
                "3.input": self.get_input("dummy") * 3,
            }

        return compiled, error

    def postprocess(self, engine, data_folder):
        output = dict(metadata={}, content=None, type=Data_type.property)

        parsers = {
            "topas": (get_pattern, get_topas_output, get_topas_error),
            "fullprof": (get_pattern, ),
        }
        default_parsers = (lambda x: {"content": 42}, ) # FIXME?

        used_parsers = parsers.get(engine, default_parsers)
        main_output_found = None

        for item in os.listdir(data_folder):
            item_path = os.path.join(data_folder, item)

            if not os.path.isfile(item_path):
                continue

            for parser in used_parsers:
                result = parser(item_path)
                if not result:
                    continue

                main_output_found = item_path
                break

            if main_output_found:
                break

        else:
            return None, f"Cannot find any results expected for {engine} in {data_folder}"

        output["metadata"]["path"] = main_output_found
        output["content"] = result["content"]
        if result.get("type"): output["type"] = result["type"]

        return output, None
