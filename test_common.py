import unittest
from datetime import date
from config import YF_ETF_SERIES
from tools.agent_tools import get_order_detail


class TestCommon(unittest.TestCase):

    def test_get_order_detail(self):
        self.assertEqual(get_order_detail("12345", "rmorris@gmail.com"),True)
 
if __name__ == '__main__':
    unittest.main()