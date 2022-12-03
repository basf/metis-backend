
import random
import logging

from aiida.orm import Int, Code, load_node
from aiida.engine import submit, ProcessState
from aiida.common.exceptions import NotExistent
from aiida.plugins import DataFactory

from aiida_dummy import DummyWorkChain
from aiida_crystal_dft.workflows.base import BaseCrystalWorkChain


class Workflow_setup:

    @staticmethod
    def submit(engine, *args):
        return getattr(Workflow_setup, f'submit_{engine}', lambda: None)(*args)


    @staticmethod
    def submit_dummy(*args):

        wf = DummyWorkChain.get_builder()
        wf.code = Code.get_from_string('Dummy@yascheduler')

        dice = random.randint(0, 200)
        wf.foobar = Int(dice)

        return submit(DummyWorkChain, **wf)


    @staticmethod
    def submit_pcrystal(input_data, ase_obj, meta):

        wf = BaseCrystalWorkChain.get_builder()
        wf.metadata = dict(label=meta['name'])

        wf.code = Code.get_from_string('Pcrystal@yascheduler')
        wf.basis_family, _ = DataFactory('crystal_dft.basis_family').get_or_create('STO-3G') # FIXME use pcrystal_bs_path
        wf.structure = DataFactory('structure')(ase=ase_obj)

        # TODO
        #wf.parameters = crystal_calc_parameters
        #wf.options = DataFactory("dict")(dict={'resources': {"num_machines": 1, "num_mpiprocs_per_machine": 1}})

        return submit(BaseCrystalWorkChain, **wf)


    @staticmethod
    def check_process(uuid, logger=logging):

        try: node = load_node(uuid)
        except NotExistent:
            logger.error(f'Node {uuid} does not exist')
            return None

        try: state = node.process_state
        except AttributeError:
            logger.error(f'Node {uuid} is not a process')
            return None

        if state in (ProcessState.FINISHED, ProcessState.KILLED, ProcessState.EXCEPTED):
            return 100

        elif state in (ProcessState.WAITING, ProcessState.CREATED):
            return 20

        else: # ProcessState.RUNNING
            return 50
