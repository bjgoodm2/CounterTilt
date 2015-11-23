import countertilt as ct
from riotwatcher import EUROPE_WEST
from pprint import pprint
from unittest import TestCase


class TestRWAndCT(TestCase):
    w = ct.RiotWatcher(ct.API_KEY)

    # check if we have API calls remaining
    def test_requests_remaining(self):
        self.assertTrue(self.w.can_make_request())

    # test our new abbrev_platforms dictionary
    def test_abbrev_platforms(self):
        self.assertEquals(ct.abbrev_platforms['eune'], 'EUN1')

    def test_get_summoner(self):
        me = self.w.get_summoner(name='KING TRICK')
        self.assertEquals(me['id'], 19988289)

    # try grabbing some mastery pages -- if trick changes mastery page names this will fail in future
    def test_masteries(self):
        me = self.w.get_summoner(name='KING TRICK')
        my_mastery_pages = self.w.get_mastery_pages([me['id']])[str(me['id'])]
        self.assertEquals(my_mastery_pages['pages'][0]['name'], 'UDYR UTILITY')

    def test_ranked_stats(self):
        me = self.w.get_summoner(name='KING TRICK')
        my_ranked_stats = self.w.get_ranked_stats(me['id'])
        self.assertEquals(my_ranked_stats['champions'][0]['id'], 111)

    def test_ranked_stats_season(self):
        me = self.w.get_summoner(name='KING TRICK')
        my_ranked_stats_season_4 = self.w.get_ranked_stats(me['id'], season=4)
        self.assertEquals(my_ranked_stats_season_4['champions'][0]['id'], 41)

    # static list of champs
    def test_static_champ_list(self):
        static_champ_list = self.w.static_get_champion_list()
        self.assertEquals(static_champ_list['data']['Aatrox']['title'], 'the Darkin Blade')

    # request data from EUW
    def test_euw_summoner(self):
        froggen = self.w.get_summoner(name='froggen', region=EUROPE_WEST)
        self.assertEquals(froggen['id'], 19531813)

    def test_get_img_url(self):
        summoner = self.w.get_summoner(name='Tiltlorrd')
        match_list = self.w.get_match_list(summoner['id'], begin_index=0, end_index=10)
        for match in match_list['matches']:
            match['img'] = ct.get_champion_image_url(match['champion'])
        # self.assertTrue('.png' in match_list[0]['img'])
