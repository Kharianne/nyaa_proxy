import unittest
from utils import IntegerValidator

param_list = [
    ('10', None, None, 10, "Validation without boundaries and valid int"),
    ('abc', None, None, False, "Validation without boundaries and invalid int"),
    ('10', 0, None, 10, "Valid integer higher than min boundary"),
    ('10', 11, None, False, "Valid integer lower than given min boundary"),
    ('4', 4, None, 4, "Valid integer equal to min boundary"),
    ('25', None, 30, 25, "Valid integer lower than max boundary"),
    ('45', None, 40, False, "Valid integer higher than max boundary"),
    ('-5', -8, 10, -5, "Valid integer within max and min boundary"),
    ('7', 0, 5, False, "Valid integer outside max and min boundary"),
    ('-1', 0, None, False, "Valid integer lower than min boundary and min is 0"),
    ('10', 0, 0, False, "Valid integer outside min and max boundary and min and max is 0")
]


class TestIntegerValidation(unittest.TestCase):

    def test_integer_validation(self):
        for _input, _min, _max, expt, msg in param_list:
            with self.subTest(msg=msg):
                self.assertEqual(
                    IntegerValidator(mn=_min, mx=_max).validate(_input),
                    expt)


if __name__ == '__main__':
    unittest.main()
