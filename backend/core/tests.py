from django.test import TestCase

# Create your tests here.


from decimal import Decimal
from types import SimpleNamespace

from django.test import SimpleTestCase

from core.bloom import bloom_petals, petal_length, risk_score


class BloomTests(SimpleTestCase):
    def _row(self, name, level=None, confidence='0.9'):
        zone = SimpleNamespace(zone_name=name)
        prediction = SimpleNamespace(risk_level=level, confidence_score=Decimal(confidence)) if level else None
        return {'zone': zone, 'prediction': prediction}

    def test_scores_stay_inside_their_level_band(self):
        self.assertTrue(62 <= risk_score('HIGH', 0) <= risk_score('HIGH', 1) <= 100)
        self.assertTrue(40 <= risk_score('MEDIUM', 0) <= risk_score('MEDIUM', 1) <= 60)
        self.assertTrue(0 <= risk_score('LOW', 1) <= risk_score('LOW', 0) <= 35)
        self.assertEqual(risk_score('UNKNOWN', 0), 0)

    def test_higher_risk_means_a_longer_petal(self):
        self.assertLess(petal_length(risk_score('LOW', 0.9)), petal_length(risk_score('MEDIUM', 0.9)))
        self.assertLess(petal_length(risk_score('MEDIUM', 0.9)), petal_length(risk_score('HIGH', 0.9)))

    def test_petals_are_sorted_riskiest_first_and_named_without_sub_county(self):
        petals = bloom_petals([
            self._row('Embakasi East Sub-County', 'LOW'),
            self._row('Kibra Sub-County', 'HIGH'),
            self._row('Starehe Sub-County', 'MEDIUM'),
            self._row('Nowhere Sub-County'),
        ])
        self.assertEqual([p['name'] for p in petals], ['Kibra', 'Starehe', 'Embakasi East', 'Nowhere'])
        self.assertEqual(petals[-1]['level'], 'UNKNOWN')
        self.assertEqual(petals[-1]['label_text'], 'No data')

    def test_no_zones_means_no_petals(self):
        self.assertEqual(bloom_petals([]), [])
