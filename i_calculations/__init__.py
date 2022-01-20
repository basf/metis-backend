
import random
import string


class Calc_setup(object):

    def __init__(self):
        """
        """

    def generate_input(self):
        """ Just a mockup
        showing the calculation input generation
        """
        output = ''

        for _ in range(random.randint(1, 20)):
            output += ''.join([random.choice(string.ascii_uppercase)
                for _ in range(random.randint(1, 20))])
            output += "\n"

        return output

    def preprocess(self, ase_obj, name):

        return {
            '1.input': self.generate_input(),
            '2.input': self.generate_input(),
            '3.input': self.generate_input(),
        }


if __name__ == "__main__":

    setup = Calc_setup()
    print(setup.generate_input())