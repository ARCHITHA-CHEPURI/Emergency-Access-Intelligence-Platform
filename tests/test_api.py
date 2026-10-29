import unittest

from fastapi import HTTPException

from src import api


class EmergencyAccessApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.first_hotspot = api.hotspots_df.iloc[0]
        cls.junction_id = int(cls.first_hotspot["junction_id"])

    def test_summary_counts_cover_all_junctions(self):
        result = api.summary()

        self.assertEqual(result["total_junctions"], 5000)
        self.assertEqual(
            result["critical"] + result["high"] + result["medium"] + result["low"],
            result["total_junctions"],
        )
        self.assertEqual(result["risk_corridors"], len(api.corridors_df))

    def test_analytics_distance_bands_cover_all_junctions(self):
        result = api.analytics()

        self.assertEqual(
            sum(band["count"] for band in result["hospital_distance_bands"]),
            result["total_junctions"],
        )
        self.assertEqual(result["risk_distribution"], api.get_risk_counts())

    def test_search_is_case_insensitive(self):
        area = str(self.first_hotspot["area_name"])

        result = api.search_hotspots(q=area.lower())

        self.assertGreater(result["count"], 0)
        self.assertEqual(result["query"], area.lower())

    def test_unknown_risk_category_is_rejected(self):
        with self.assertRaises(HTTPException) as error:
            api.risk_category("unknown")

        self.assertEqual(error.exception.status_code, 400)

    def test_scenario_with_no_change_matches_baseline_score(self):
        result = api.simulate_intervention(
            self.junction_id,
            component="hospital_access_risk",
            reduction_pct=0,
        )

        self.assertAlmostEqual(
            result["current_risk_score"],
            float(self.first_hotspot["final_risk_score"]),
            places=4,
        )
        self.assertEqual(result["scenario_risk_score"], result["current_risk_score"])

    def test_scenario_reduces_selected_component_and_score(self):
        result = api.simulate_intervention(
            self.junction_id,
            component="hospital_access_risk",
            reduction_pct=25,
        )

        self.assertAlmostEqual(
            result["scenario_component_value"],
            result["current_component_value"] * 0.75,
            places=4,
        )
        self.assertLessEqual(result["scenario_risk_score"], result["current_risk_score"])
        self.assertIn("not a measured prediction", result["disclaimer"])

    def test_scenario_rejects_unknown_junction(self):
        with self.assertRaises(HTTPException) as error:
            api.simulate_intervention(999999999)

        self.assertEqual(error.exception.status_code, 404)

    def test_scenario_rejects_unknown_component(self):
        with self.assertRaises(HTTPException) as error:
            api.simulate_intervention(
                self.junction_id,
                component="unknown",
                reduction_pct=25,
            )

        self.assertEqual(error.exception.status_code, 400)

    def test_planning_report_is_downloadable_and_discloses_limitations(self):
        report = api.planning_report()
        content = report.body.decode("utf-8")

        self.assertEqual(report.media_type, "text/plain")
        self.assertIn("attachment;", report.headers["Content-Disposition"])
        self.assertIn("TOP 10 JUNCTIONS", content)
        self.assertIn("not for live dispatch or navigation", content)
        self.assertIn("Mapped hospitals: 2916", content)


if __name__ == "__main__":
    unittest.main()
