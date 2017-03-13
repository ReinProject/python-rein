import unittest

from rein.lib.rating import calculate_trust_score

# Test cases have to follow certain conventions
# List of dicts / lists of dicts
# Each dict represents a rating, containing the keys 
# Rater msin, User msin, Rating
# There must be ratings listing SourceMsin as rater
# The people rated by SourceMsin must have rated (or not rated) DestMsin
###############################################
# Test case 1 flow chart
#               5/5                      4/5
#Link One  <------------+ Source   +-------------> Link Three
# +                         +                              +
# |                         |3/5                           |
# |                         v                              |
# |                       Link Two                         |
# |                         +                              |
# |                         |                              |
# |                         |5/5                           |
# |                         |                              |
# |                         v                              |
# |                                                        |
# +--------------------->  Dest  <-------------------------+
#      5/5                                 5/5

test_case_1 = [
    {
        'Rater msin': 'SourceMsin',
        'User msin': 'LinkOneMsin',
        'Rating': 5
    },
    {
        'Rater msin': 'SourceMsin',
        'User msin': 'LinkTwoMsin',
        'Rating': 3
    },
    {
        'Rater msin': 'SourceMsin',
        'User msin': 'LinkThreeMsin',
        'Rating': 4
    },
    {
        'Rater msin': 'LinkOneMsin',
        'User msin': 'DestMsin',
        'Rating': 5
    }, 
    {
        'Rater msin': 'LinkTwoMsin',
        'User msin': 'DestMsin',
        'Rating': 5
    },
    {
        'Rater msin': 'LinkThreeMsin',
        'User msin': 'DestMsin',
        'Rating': 5
    }
]

class TestTrustScore(unittest.TestCase):
    def test_trust_score(self):
        """Tests trust score calculation"""

        trust_score_1 = calculate_trust_score(test=True, test_ratings=test_case_1)
        self.assertEqual(trust_score_1['score'], 4)
        self.assertEqual(trust_score_1['links'], 3)
