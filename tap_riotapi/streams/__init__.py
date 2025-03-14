from .tft_player_streams import (
    TFTPlayerByNameStream,
    TFTPlayerMatchHistoryStream,
    TFTPlayerMatchDetailStream,
)
from .ranked_tft_apex_league_streams import (
    ApexTierRankedLadderStream,
    ApexTierRankedLadderMatchHistoryStream,
    ApexTierRankedLadderMatchDetailStream,
)
from .ranked_tft_normal_league_streams import (
    NormalTierRankedLadderStream,
    NormalTierRankedLadderMatchHistoryStream,
    NormalTierRankedLadderMatchDetailStream,
)

TFT_PLAYER_STREAMS = [
    TFTPlayerByNameStream,
    TFTPlayerMatchHistoryStream,
    TFTPlayerMatchDetailStream,
]

NORMAL_TIER_STREAMS = [
    NormalTierRankedLadderStream,
    NormalTierRankedLadderMatchHistoryStream,
    NormalTierRankedLadderMatchDetailStream,
]

APEX_TIER_STREAMS = [
    ApexTierRankedLadderStream,
    ApexTierRankedLadderMatchHistoryStream,
    ApexTierRankedLadderMatchDetailStream,
]
