import unittest
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.services.search_service import search

class TestSearchLogic(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.ctx = self.app.app_context()
        self.ctx.push()

    def tearDown(self):
        self.ctx.pop()

    def test_overqualified_search_explicit_course(self):
        """
        User searches for 'Geospatial Engineering' (Cutoff ~36) with 48 points.
        Current logic hides this because 48 - 10 = 38 (Floor), and 36 < 38.
        This test expects the course to be FOUND because the user asked for it explicitly.
        """
        print("\nTesting Explicit Course Search (Overqualified)...")
        results = search(
            course_name="BACHELOR OF SCIENCE (GEOSPATIAL ENGINEERING)",
            institution=['UNIVERSITY OF NAIROBI'],
            user_points=48
        )
        found = any(r['name'] == 'BACHELOR OF SCIENCE (GEOSPATIAL ENGINEERING)' for r in results)
        print(f"Found: {found} (Results: {len(results)})")
        self.assertTrue(found, "Should find course even if overqualified when explicitly searching")

    def test_browsing_clustering_logic(self):
        """
        User browses a Cluster with 48 points. 
        Here, hiding very low courses (e.g. cutoff 15) might be acceptable, 
        but we should ensure we don't hide reasonable options.
        """
        pass 

if __name__ == '__main__':
    unittest.main()
