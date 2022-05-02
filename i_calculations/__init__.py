
import sys
import os.path
import json

INCL_PATH = os.path.realpath(os.path.normpath(
    os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "../"
    )
))
if not INCL_PATH in sys.path:
    sys.path.insert(0, INCL_PATH)

from i_structures.topas import ase_to_topas


class Calc_setup:

    schemata = {}
    templates = {}

    for engine in ['topas', 'dummy']:

        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "schemata/%s.json" % engine), 'r') as f:
            schemata[engine] = json.loads(f.read())

        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates/%s.tpl" % engine), 'r') as f:
            templates[engine] = f.read()

    def __init__(self):
        """
        """

    def get_input(self, engine):
        return Calc_setup.templates.get(engine,
            Calc_setup.templates['dummy'])

    def get_schema(self, engine):
        return Calc_setup.schemata.get(engine,
            Calc_setup.schemata['dummy'])

    def preprocess(self, ase_obj, engine, name):

        if engine == 'topas':
            return {
                'input.pro': self.get_input(engine),
                'structure.inc': ase_to_topas(ase_obj),
            }

        else:
            return {
                '1.input': self.get_input('dummy'),
                '2.input': self.get_input('dummy'),
                '3.input': ase_to_topas(ase_obj),
            }


if __name__ == "__main__":

    setup = Calc_setup()
    print(setup.get_input('hello'))
