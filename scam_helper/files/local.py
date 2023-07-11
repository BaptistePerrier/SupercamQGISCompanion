import pandas as pd
import numpy as np
import os
import json

from .. import misc

def readLocalConfig():
    return pd.read_json(os.path.join(misc.constants.LOCALFOLDER, "config", "local.json"))

def writeLocalConfig(config):
    local_JSONconfig = open(os.path.join(misc.constants.LOCALFOLDER,"config", "local.json"), 'w')
    local_JSONconfig.write(config.to_json())
    local_JSONconfig.close()

def buildLocalMasterlist(masterlistPath, positioner):
    def pdShotEntries2Dict(pdEntry):
        rDict = {
            "sclk" : list(pdEntry.sclk),
            "focus_position_mm" : list(pdEntry.focus_position_mm),
            "primary_mirror_temp" : list(pdEntry.primary_mirror_temp),
            "rsm_az" : list(pdEntry.rsm_az),
            "rsm_el" : list(pdEntry.rsm_el),
            "inst_az" : list(pdEntry.inst_az),
            "inst_el" : list(pdEntry.inst_el),
            "solar_az" : list(pdEntry.solar_az),
            "solar_el" : list(pdEntry.solar_el),
            "edr_fname" : list(pdEntry.edr_fname),
            "cdr_fname" : list(pdEntry.cdr_fname),
            "binfile" : list(pdEntry.binfile)
        }
        return rDict

    masterlist = pd.read_csv(masterlistPath, usecols=[
        "sol",
        "seqid",
        "sclk",
        "targetname",
        "tdb_name",
        "type",
        "primary_mirror_temp",
        "focus_position_mm",
        "focus_position_steps",
        "binfile",
        "edr_fname",
        "cdr_fname",
        "rsm_az",
        "rsm_el",
        "inst_az",
        "inst_el",
        "solar_az",
        "solar_el"
    ], dtype={
        "sol" : int,
        "seqid" : str,
        "sclk" : int,
        "targetname" : str,
        "tdb_name" : str,
        "type" : str,
        "primary_mirror_temp" : float,
        "focus_position_mm" : int,
        "focus_position_steps" : int,
        "binfile" : str,
        "edr_fname" : str,
        "cdr_fname" : str,
        "rsm_az" : float,
        "rsm_el" : float,
        "inst_az" : float,
        "inst_el" : float,
        "solar_az" : float,
        "solar_el" : float
    })
    
    # Open input data files for the positioning of rover
    positioner.openRoverPositioningFiles()

    geojson_points = {"type" : "FeatureCollection", "features" : []}

    names = masterlist.tdb_name.unique()
    for name in names:
        if not name == "SCCT":
            shots = masterlist[masterlist["tdb_name"]==name]
            RMIs = shots[shots["type"]=="RMI"].sort_values(by="sclk")
            if len(RMIs.sclk.values) > 0:
                point = {
                    "type" : "Feature", 
                    "geometry" : {
                        "type" : "Point",
                        "coordinates" : []
                    },
                    "properties" : {}
                }

                point["properties"]["name"] = name
                point["properties"]["sclk"] = int(RMIs.sclk.values[0])
                point["properties"]["seqid"] = RMIs.seqid.values[0]

                roverCoordinates = positioner.retrieveRoverPosition(point["properties"]["sclk"])

                point["properties"]["roverCoordinates_source"] = roverCoordinates["source"]
                point["properties"]["roverCoordinates"] = roverCoordinates["coordinates"]

                _shotsWithInstAz = shots.inst_az.dropna()
                if not _shotsWithInstAz.empty:
                    point["properties"]["meanAzimuth"] = _shotsWithInstAz.mean()
                else:
                    point["properties"]["meanAzimuth"] = 0 # Assuming the instrument is pointing north if not specified

                _shotsWithInstEl = shots.inst_el.dropna()
                if not _shotsWithInstEl.empty:
                    point["properties"]["meanElevation"] = _shotsWithInstEl.mean()
                else:
                    point["properties"]["meanElevation"] = 0

                _shotsFocusPositionMm = shots.focus_position_mm.dropna()                    
                if not _shotsFocusPositionMm.empty:
                    point["properties"]["meanFocusPosition_mm"] = _shotsFocusPositionMm.mean()
                else:
                    point["properties"]["meanFocusPosition_mm"] = 2 # Assuming the measure is made at 2 meters if not specified

                shotCoordinates = positioner.retrieveShotPosition(point["properties"]["meanAzimuth"], point["properties"]["meanFocusPosition_mm"], point["properties"]["roverCoordinates"])
                
                # Check if the point has coordinates
                point["geometry"]["coordinates"] = shotCoordinates
                if np.isnan(point["geometry"]["coordinates"][0]) or np.isnan(point["geometry"]["coordinates"][1]):
                    # If not, it is useless to retrieve further data like IRS, LIBS ...
                    continue

                point["properties"]["shots"] = {}
                _LIBSShots = shots[shots["type"] == "LIBS"]
                if not _LIBSShots.empty:
                    point["properties"]["shots"]["LIBS"] = pdShotEntries2Dict(_LIBSShots)

                _IRSShot = shots[shots["type"] == "IRS"]
                if not _IRSShot.empty:
                    point["properties"]["shots"]["IRS"] = pdShotEntries2Dict(_IRSShot)

                _VISShot = shots[shots["type"] == "VIS"]
                if not _VISShot.empty:
                    point["properties"]["shots"]["VIS"] = pdShotEntries2Dict(_VISShot)

                _RAMANShot = shots[shots["type"] == "RAMAN"]
                if not _RAMANShot.empty:
                    point["properties"]["shots"]["RAMAN"] = pdShotEntries2Dict(_RAMANShot)

                geojson_points["features"].append(point)

    # Free memory after use of data files
    positioner.closeRoverPositioningFiles()

    lastSclk = masterlist.sort_values(by="sclk").tail(1).sclk.values[0]
    return geojson_points, lastSclk

def readLocalMasterlist():
    with open(os.path.join(misc.constants.LOCALFOLDER, "local_data", "local_masterlist.geojson"), 'r') as f:
        localMasterlistRaw = json.load(f)

    return localMasterlistRaw

def writeLocalMasterlist(geojson_points):
    localMasterList_file = open(os.path.join(misc.constants.LOCALFOLDER, "local_data", "local_masterlist.geojson"), 'w+')
    json.dump(geojson_points, localMasterList_file)
    localMasterList_file.close()

def importPlannedTargets(plannedTargetsPath):
    localMasterlistRaw = readLocalMasterlist()
    localMasterlist = localMasterlistRaw["features"]

    with open(plannedTargetsPath, 'r') as f:
        plannedTargetsRaw = json.load(f)["features"]
    # Building correspondance dictionnary to faciliytate search
    plannedTargets = {}
    for entry in plannedTargetsRaw:
        plannedTargets[entry["properties"]["Name"]] = entry   

    for entry in localMasterlist:
        try:
            plannedTargetsCoordinates = plannedTargets[entry["properties"]["name"]]["geometry"]["coordinates"]
            entry["geometry"]["coordinates"] = plannedTargetsCoordinates
        except:
            pass # If the masterlist name is not found in Planned Targets, don't worry and go on

    writeLocalMasterlist(localMasterlistRaw)

def importSCAMLD(SCAMLDPath):
    localMasterlistRaw = readLocalMasterlist()
    localMasterlist = localMasterlistRaw["features"]

    with open(SCAMLDPath, 'r') as f:
        SCAMLDRaw = json.load(f)["features"]
    # Building correspondance dictionnary to faciliytate search
    SCAMLD = {}
    for entry in SCAMLDRaw:
        SCAMLD[entry["properties"]["description"]] = entry

    for entry in localMasterlist:
        try:
            SCAMLDCoordinates = SCAMLD[entry["properties"]["name"]]["geometry"]["coordinates"]
            entry["geometry"]["coordinates"] = SCAMLDCoordinates
        except:
            pass # If the masterlist name is not found in SCAMLD, don't worry and go on

    writeLocalMasterlist(localMasterlistRaw)

def importVisIRSpectralParameters(VisIRSPath):
    localMasterlistRaw = readLocalMasterlist()
    localMasterlist = localMasterlistRaw["features"]

    SPRaw = pd.read_csv(VisIRSPath)

    for entry in localMasterlist:
        try:
            spectralParameters = {
                "BD1420" : list(SPRaw[SPRaw["targetname"] == entry["properties"]["name"]].BD1420.replace(np.nan, None)),
                "BD1900_2" : list(SPRaw[SPRaw["targetname"] == entry["properties"]["name"]].BD1900_2.replace(np.nan, None)),
                "BD1920" : list(SPRaw[SPRaw["targetname"] == entry["properties"]["name"]].BD1920.replace(np.nan, None)),
                "BD1930" : list(SPRaw[SPRaw["targetname"] == entry["properties"]["name"]].BD1930.replace(np.nan, None)),
                "BD1940" : list(SPRaw[SPRaw["targetname"] == entry["properties"]["name"]].BD1940.replace(np.nan, None)),
                "BD2210" : list(SPRaw[SPRaw["targetname"] == entry["properties"]["name"]].BD2210.replace(np.nan, None)),
                "BD2280" : list(SPRaw[SPRaw["targetname"] == entry["properties"]["name"]].BD2280.replace(np.nan, None)),
                "BD2320" : list(SPRaw[SPRaw["targetname"] == entry["properties"]["name"]].BD2320.replace(np.nan, None)),
                "LCPINDEX2" : list(SPRaw[SPRaw["targetname"] == entry["properties"]["name"]].LCPINDEX2.replace(np.nan, None)),
                "HCPINDEX2" : list(SPRaw[SPRaw["targetname"] == entry["properties"]["name"]].HCPINDEX2.replace(np.nan, None)),
                "BD2530" : list(SPRaw[SPRaw["targetname"] == entry["properties"]["name"]].BD2530.replace(np.nan, None)),
                "SINDEX2" : list(SPRaw[SPRaw["targetname"] == entry["properties"]["name"]].SINDEX2.replace(np.nan, None)),
                "S2100_2500" : list(SPRaw[SPRaw["targetname"] == entry["properties"]["name"]].S2100_2500.replace(np.nan, None)),
                "S1350_1800" : list(SPRaw[SPRaw["targetname"] == entry["properties"]["name"]].S1350_1800.replace(np.nan, None)),
                "BD433" : list(SPRaw[SPRaw["targetname"] == entry["properties"]["name"]].BD433.replace(np.nan, None)),
                "BD545" : list(SPRaw[SPRaw["targetname"] == entry["properties"]["name"]].BD545.replace(np.nan, None)),
                "BD650" : list(SPRaw[SPRaw["targetname"] == entry["properties"]["name"]].BD650.replace(np.nan, None)),
                "R6744" : list(SPRaw[SPRaw["targetname"] == entry["properties"]["name"]].R6744.replace(np.nan, None)),
                "R7584" : list(SPRaw[SPRaw["targetname"] == entry["properties"]["name"]].R7584.replace(np.nan, None)),
                "S6744" : list(SPRaw[SPRaw["targetname"] == entry["properties"]["name"]].S6744.replace(np.nan, None)),
                "S7584" : list(SPRaw[SPRaw["targetname"] == entry["properties"]["name"]].S7584.replace(np.nan, None)),
                "S6075" : list(SPRaw[SPRaw["targetname"] == entry["properties"]["name"]].S6075.replace(np.nan, None)),
                "R6084" : list(SPRaw[SPRaw["targetname"] == entry["properties"]["name"]].R6084.replace(np.nan, None)),
                "S6084" : list(SPRaw[SPRaw["targetname"] == entry["properties"]["name"]].S6084)
            }
            entry["properties"]["VisIRspectralParameters"] = spectralParameters
        except Exception as e:
            pass # If the masterlist name is not found in SCAMLD, don't worry and go on

    writeLocalMasterlist(localMasterlistRaw)