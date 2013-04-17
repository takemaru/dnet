# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

from dnet import Network, Configs
import unittest

class TestNetwork(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_tutorial(self):
        nw = Network('test/results/data.yaml')
        self.assertTrue(isinstance(nw, Network))

        configs = nw.enumerate()
        self.assertTrue(isinstance(configs, Configs))
        self.assertEqual(len(configs), 111)
        self.assertEqual(configs.len(), 111)

        for config in configs:
            self.assertTrue(isinstance(config, list))

        i = 1
        sum = 0.0
        for config in configs.rand_iter():
            sum += nw.loss(config)
            if i == 10:
                break
            i += 1
        self.assertAlmostEqual(sum / 10, 78790.8, 0)

        filtered_configs = configs.including('switch_0002').excluding('switch_0003')
        self.assertEqual(len(filtered_configs), 15)

        self.assertAlmostEqual(nw.loss(configs.choice()), 88684.7, 0)

        results = nw.optimize(configs)
        self.assertAlmostEqual(results['minimum_loss'], 69734.3, 0)
        self.assertAlmostEqual(results['loss_without_root_sections'], 46128.5, 0)
        self.assertAlmostEqual(results['lower_bound_of_minimum_loss'], 67028.8, 0)
        self.assertEqual(results['open_switches'], ['switch_0004', 'switch_0007', 'switch_0012', 'switch_0015'])

    def test_fukui_tepco(self):
        nw = Network('test/data', format='fukui-tepco')

        configs = nw.enumerate()
        self.assertEqual(len(configs), 111)        

        results = nw.optimize(configs)
        self.assertAlmostEqual(results['minimum_loss'], 69734.3, 0)
        self.assertEqual(results['open_switches'], ['switch_0005', 'switch_0306', 'switch_1058', 'switch_1069'])


if __name__ == '__main__':
    unittest.main()
