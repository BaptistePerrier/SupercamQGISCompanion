class constants:
    SOLZEROSCLK = 666894164
    SOLSCLKDURATION = 88775.244147
    MARSEARTHTIMERATIO = 1.02749125170
    SCLKMARTIANHOUR = 3669
    SCLKMARTIANMINUTE = int(SCLKMARTIANHOUR / 60)

    LOCALFOLDER = None
    
class functions:
    def getSolFromsclk(sclk):
        return int((sclk - constants.SOLZEROSCLK) // constants.SOLSCLKDURATION)

    def getMartianTimeFromsclk(sclk):
        terrestrianSeconds = (sclk - constants.SOLZEROSCLK) % constants.SOLSCLKDURATION

        mHours = terrestrianSeconds // constants.SCLKMARTIANHOUR
        terrestrianSeconds = terrestrianSeconds % constants.SCLKMARTIANHOUR

        mMinutes = terrestrianSeconds // constants.SCLKMARTIANMINUTE
        terrestrianSeconds = terrestrianSeconds % constants.SCLKMARTIANMINUTE

        mSeconds = int(terrestrianSeconds / constants.MARSEARTHTIMERATIO)

        return "{:02d}:{:02d}:{:02d}".format(int(mHours), int(mMinutes), int(mSeconds))
            