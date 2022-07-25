
import random
import logging

from aiida.orm import Int, Code, load_node
from aiida.engine import submit, ProcessState
from aiida.common.exceptions import NotExistent
from aiida_dummy import DummyWorkChain


class Workflow_setup:

    @staticmethod
    def submit(*args):
        wf = DummyWorkChain.get_builder()
        wf.code = Code.get_from_string('Dummy@yascheduler')

        dice = random.randint(0, 200)
        wf.foobar = Int(dice)

        return submit(DummyWorkChain, **wf)


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
