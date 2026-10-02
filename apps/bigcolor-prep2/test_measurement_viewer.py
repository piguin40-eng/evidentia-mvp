import tempfile
import unittest
from pathlib import Path
import numpy as np
import trimesh
from prep_engine import analyze_case

class MeasurementViewerTest(unittest.TestCase):
    def run_case(self, scale=1, unit='mm', include=True):
        with tempfile.TemporaryDirectory() as tmp:
            pre = trimesh.creation.icosphere(subdivisions=2, radius=10 * scale)
            wax = trimesh.creation.icosphere(subdivisions=2, radius=10.5 * scale)
            a, b = Path(tmp)/'a.stl', Path(tmp)/'b.stl'
            pre.export(a); wax.export(b)
            return analyze_case(a,b,input_unit=unit,include_viewer=include)

    def test_known_half_mm_and_index_contract(self):
        analysis, table = self.run_case()
        m = analysis['measurement_viewer']
        self.assertEqual(m['status'],'ready')
        n = len(m['distances_mm'])
        self.assertEqual(len(m['positions']), n*3)
        self.assertEqual(len(m['teeth']), n)
        self.assertEqual(len(m['zones']), n)
        self.assertLess(max(m['indices']), n)
        np.testing.assert_allclose(m['distances_mm'], .5, atol=2e-5)
        self.assertAlmostEqual(np.median(m['distances_mm']),analysis['distance_summary_mm']['p50'],places=4)
        self.assertFalse(analysis['qa_gate']['can_use_for_clinical_decision'])

    def test_units_geometry_and_distances_mm(self):
        a, _ = self.run_case(.001,'m')
        m=a['measurement_viewer']
        np.testing.assert_allclose(m['distances_mm'], .5, atol=2e-5)
        self.assertAlmostEqual(max(m['positions']),10.5,places=4)

    def test_opt_in(self):
        a,_ = self.run_case(include=False)
        self.assertNotIn('measurement_viewer',a)

if __name__ == '__main__': unittest.main()
