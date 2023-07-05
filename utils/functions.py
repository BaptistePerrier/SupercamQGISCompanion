from .constants import *

def getSolFromsclk(sclk):
        return int((sclk - SOLZEROSCLK) // SOLSCLKDURATION)

def getMartianTimeFromsclk(sclk):
    terrestrianSeconds = (sclk - SOLZEROSCLK) % SOLSCLKDURATION

    mHours = terrestrianSeconds // SCLKMARTIANHOUR
    terrestrianSeconds = terrestrianSeconds % SCLKMARTIANHOUR

    mMinutes = terrestrianSeconds // SCLKMARTIANMINUTE
    terrestrianSeconds = terrestrianSeconds % SCLKMARTIANMINUTE

    mSeconds = int(terrestrianSeconds / MARSEARTHTIMERATIO)

    return "{:02d}:{:02d}:{:02d}".format(int(mHours), int(mMinutes), int(mSeconds))
            