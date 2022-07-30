
import random
import logging

from aiida.orm import Int, Code, load_node
from aiida.engine import submit, ProcessState
from aiida.common.exceptions import NotExistent


class Workflow_setup:

    @staticmethod
    def submit(engine, *args):
        return getattr(Workflow_setup, f'submit_{engine}', lambda: None)(*args)


    @staticmethod
    def submit_dummy(*args):

        from aiida_dummy import DummyWorkChain

        wf = DummyWorkChain.get_builder()
        wf.code = Code.get_from_string('Dummy@yascheduler')

        dice = random.randint(0, 200)
        wf.foobar = Int(dice)

        return submit(DummyWorkChain, **wf)


    @staticmethod
    def submit_pcrystal(input_data, ase_obj, meta):

        from mpds_aiida.workflows.aiida import AiidaStructureWorkChain
        from aiida.plugins import DataFactory

        wf = AiidaStructureWorkChain.get_builder()
        wf.metadata = dict(label=meta['name'])
        wf.structure = DataFactory('structure')(ase=ase_obj)
        return submit(AiidaStructureWorkChain, **wf)


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
