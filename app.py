from copyreg import constructor
from lib2to3.pgen2 import driver
from re import A
from urllib import response
from flask import Flask, jsonify, send_file, request, url_for
from wsgiref.validate import validator
# import numpy as np
# import pandas as pd
# import matplotlib
# import matplotlib.pyplot as plt
# from matplotlib.collections import LineCollection
# from matplotlib import cm
import fastf1
from fastf1.core import Laps
from fastf1 import utils
from fastf1 import plotting
plotting.setup_mpl()
from timple.timedelta import strftimedelta
import unicodedata
from flask import Flask
from flask_cors import CORS, cross_origin
import os
import pymysql
from dotenv import load_dotenv
import secrets
import ergast_py
from datetime import datetime, date
from passlib.hash import sha256_crypt

app = Flask(__name__)
# app = application
CORS(app)


HOST = os.getenv('HOST')
PORT = 3306
USER = 'admin'
# PASSWORD = os.environ['PASSWORD']
PASSWORD = os.getenv('PASSWORD')
DB = 'Table1'

@app.route('/')
def root():
    return "DONE"

@app.route('/get_races')
def get_races():
    a = fastf1.get_event_schedule(1950,include_testing=False, force_ergast=False)
    races = []
    for i in a["Location"].tolist():
        nData = unicodedata.normalize('NFKD', i).encode('ASCII', 'ignore')
        races.append(nData.decode())
    
    return jsonify(races=races)

@app.route('/get_image')
def get_image():
    
    return send_file('test.png', mimetype='image/png')


@app.route("/drivers")
def drivers():
    e = ergast_py.Ergast()
    standings = []
    race_results = e.season(2022).get_driver_standing()
    for i in race_results.driver_standings:
        standings.append([i.position, str(i.driver.given_name) + " " + str(i.driver.family_name), i.constructors[0].name, int(i.points)])

    return jsonify(result= standings)
 
@app.route('/getRaceResults', methods = ['GET', 'POST'])
def getRaceResults():
    data = request.get_json()
    e = ergast_py.Ergast()
    race_results = e.season(int(data["year"])).round(int(data["race"])).get_result().results

    results = []
    poleTime = race_results[0].time
    for result in race_results:     
        time = ""
        if result.position == 1:
            time = "1:"+ poleTime.strftime("%M")+":"+poleTime.strftime("%S")+":"+poleTime.strftime("%f")[:3]
        elif result.time == None:
            time = e.driver(result.driver.driver_id).status(str(result.status)).get_status().status
        else:
            time = "+" + str((datetime.combine(date.today(), result.time) - datetime.combine(date.today(), poleTime)).total_seconds())
            
        results.append([result.position, result.number, str(result.driver.given_name) + " " + str(result.driver.family_name), result.constructor.name, time, int(result.points)])

    return jsonify(result = results)


@app.route('/getQualiResults', methods = ['GET', 'POST'])
def getQualiResults():
    data = request.get_json()
    e = ergast_py.Ergast()
    quali_results = e.season(int(data["year"])).round(int(data["race"])).get_qualifying().qualifying_results

    results = []

    for i in quali_results:
        if i.qual_1 != None:
            quali1 = i.qual_1.strftime("%M:%S:%f")[:-3]
        else:
            quali1 = None
        if i.qual_2 != None:
            quali2 = i.qual_2.strftime("%M:%S:%f")[:-3]
        else:
            quali2 = None
        if i.qual_3 != None:
            quali3 = i.qual_3.strftime("%M:%S:%f")[:-3]
        else:
            quali3 = None
        
        results.append([i.position, str(i.driver.given_name) + " " + str(i.driver.family_name), i.constructor.name, quali1, quali2, quali3])
    # print(results)
    return jsonify(result = results)


 
@app.route('/sendYear', methods = ['GET', 'POST'])
def sendYear():
    
    # fastf1.Cache.enable_cache('./cache')

    data = request.get_json()

    e = ergast_py.Ergast()
    races = []
    count = 1
    latestRound = e.season(2022).round().get_race().round_no

    if int(data["year"]) == -1:
        race_results = e.season().get_races()
    else:
        race_results = e.season(int(data["year"])).get_races()
    
    for race in race_results:
        if count <= latestRound:
            races.append({count : race.race_name})
            count += 1

    return jsonify(races=races[::-1])

@app.route('/signUp', methods = ['POST'])
def signUp():

    data = request.get_json()
    
    load_dotenv() 

    conn = pymysql.connect(
            host= HOST, 
            port = PORT,
            user = USER, 
            password = PASSWORD,
            db = DB,
            )
    

    passwrd = sha256_crypt.hash(data["pass"])



    cur=conn.cursor()
    cur.execute("INSERT INTO users (fname, lname, email, pass) VALUES (%s, %s, %s, %s )", (data["firstName"], data["lastName"], data["email"], passwrd))
    userID = cur.lastrowid
    conn.commit()
    cur.execute("INSERT INTO league_teams (userID, leagueID, teamID) VALUES (%s, 13, null)", (userID))
    conn.commit()

    return "done"

@app.route('/logIn', methods = ['GET', 'POST'])
def logIn():

    data = request.get_json()
    
    load_dotenv()

    conn = pymysql.connect(
            host= HOST, 
            port = PORT,
            user = USER, 
            password = PASSWORD,
            db = DB,
            )

    cur=conn.cursor()
    cur.execute("SELECT userID FROM users WHERE email = %s", (data["email"]))
    result=cur.fetchone()
    if result==None: 
        return jsonify(loginVerification=False)
    userID=result[0]
    # print(userID)
    cur.execute("SELECT pass FROM users WHERE userID = %s", (userID))
    result=cur.fetchone()
    passwrd=result[0]

    if sha256_crypt.verify(data["pass"], passwrd) == False:
        return jsonify(loginVerification=False)

    token=secrets.token_urlsafe(10)
    cur.execute("UPDATE users SET token = %s WHERE email = %s", (token, data["email"]))
    conn.commit()
    return jsonify(loginVerification=True, token=token)
    # else:
    #     conn.commit()
    #     return jsonify(loginVerification=False)

@app.route('/getUserName', methods = ['GET', 'POST'])
def getUserName():

    data = request.get_json()
    
    load_dotenv()

    conn = pymysql.connect(
            host= HOST, 
            port = PORT,
            user = USER, 
            password = PASSWORD,
            db = DB,
            )

    cur=conn.cursor()

    cur.execute("SELECT fname, lname FROM users WHERE token = %s", (data["token"]))
    result=cur.fetchall()

    return jsonify(name=result[0][0] + " " + result[0][1])  

@app.route('/driversInfo', methods = ['GET', 'POST'])
def driversInfo():
    
    load_dotenv()

    conn = pymysql.connect(
            host= HOST, 
            port = PORT,
            user = USER, 
            password = PASSWORD,
            db = DB,
            )

    cur=conn.cursor()
    cur.execute("SELECT * FROM drivers")
    result=cur.fetchall()

    driversList = []
    constructorsList =[]

    for drivers in result:
        driversList.append({"id": drivers[0], "driver": drivers[1], "driverImg": drivers[2], "cost": drivers[3]})

    cur.execute("SELECT * FROM constructors")
    result=cur.fetchall()

    for constructors in result:
        constructorsList.append({"id": constructors[0], "constructor": constructors[1], "constructorImg": constructors[2], "cost": constructors[3]})

    return jsonify(driverList=driversList, constructorList=constructorsList) 

@app.route('/saveTeam', methods = ['POST'])
def saveTeam():
    
    data = request.get_json()
    
    load_dotenv()

    conn = pymysql.connect(
            host= HOST, 
            port = int(PORT),
            user = USER, 
            password = PASSWORD,
            db = DB,
            )

    cur=conn.cursor()
    cur.execute("SELECT * FROM teams WHERE teamName = %s", (data["teamName"]))
    isTeam = len(cur.fetchall())
    
    teamList = {"slot1":"", "slot2":"", "slot3":"", "slot4":"", "slot5":"", "slot6":""}
    i = 1

    for info in data["team"]:
        if (info["id"] < 21):
            teamList["slot" + str(i)] = info["id"]
            i += 1
        elif (info["id"] > 100):
            teamList["slot6"] = info["id"]
            i += 1

    if (isTeam==0):

        cur.execute("INSERT INTO teams (slot1, slot2, slot3, slot4, slot5, slot6, maxBudget, teamName) VALUES (%s, %s, %s, %s, %s, %s, %s, %s )", (teamList["slot1"], teamList["slot2"], teamList["slot3"], teamList["slot4"], teamList["slot5"], teamList["slot6"], data["budget"], data["teamName"]))
        conn.commit()

        cur.execute("SELECT * FROM teams")
        teamID = cur.fetchall()[len(cur.fetchall())-1][0]

        cur.execute("SELECT userID FROM users WHERE token = %s", (data["token"]))
        userID = cur.fetchall()[0][0]
        cur.execute("INSERT INTO league_teams (userID, leagueID, teamID) VALUES (%s, null, %s)", (userID, teamID))
        conn.commit()

    elif (isTeam>0):
        
        cur.execute("UPDATE teams SET slot1 = %s, slot2 = %s, slot3 = %s, slot4 = %s, slot5 = %s, slot6 = %s, maxBudget = %s WHERE teamName = %s", (teamList["slot1"], teamList["slot2"], teamList["slot3"], teamList["slot4"], teamList["slot5"], teamList["slot6"], data["budget"], data["teamName"]))
        conn.commit()

    return jsonify(teamList=data)  

@app.route('/getUsersTeams', methods = ['POST'])
def getUsersTeams():

    data = request.get_json()

    if data["token"] == None:
        return jsonify(teamList=None) 
    
    load_dotenv()

    conn = pymysql.connect(
            host= HOST, 
            port = int(PORT),
            user = USER, 
            password = PASSWORD,
            db = DB,
            )

    teamList = {}

    cur=conn.cursor()
    
    budget = 100,000,000

    cur.execute("SELECT userID FROM users WHERE token = %s", (data["token"]))
    userID=cur.fetchall()[0][0]
    cur.execute("SELECT teamID FROM league_teams WHERE userID = %s", (userID))
    userTeamss = [i[0] for i in cur.fetchall()]
    cur.execute("SELECT * FROM teams WHERE teamID IN %s;", (userTeamss,))
    result=cur.fetchall()

    currentTeam = []
    
    for team in result:
        for i in range(2,10):
            if (i<7):
                #driver
                if (team[i] != 0):
                    cur.execute("SELECT * FROM drivers WHERE id = %s", (team[i]))
                    result=cur.fetchall()[0]
                    currentTeam.append({"cost":result[3], "driver":result[1], "driverImg":result[2], "id":result[0]})

            elif (i==7):
                #constructor
                if (team[i] != 0):
                    cur.execute("SELECT * FROM constructors WHERE id = %s", (team[i]))
                    result=cur.fetchall()[0]
                    currentTeam.append({"cost":result[3], "constructor":result[1], "constructorImg":result[2], "id":result[0]})

            elif (i==8):
                #budget
                budget=team[i]
                currentTeam.append({"budget":budget})

            elif (i==9):
                #teamName
                teamName = str(team[i])   
                teamList[teamName] = currentTeam 
                currentTeam = []

    userTeamss = list(filter(None, userTeamss))


    return jsonify(teamList=teamList, budget=budget, teamIDs=userTeamss)  

@app.route('/deleteTeam', methods = ['POST'])
def deleteTeam():

    data = request.get_json()
    # print(data)
    load_dotenv()

    conn = pymysql.connect(
            host= HOST, 
            port = int(PORT),
            user = USER, 
            password = PASSWORD,
            db = DB,
            )

    cur=conn.cursor()
    cur.execute("SELECT teamID FROM teams WHERE teamName = %s", (data["teamName"]))
    teamID = cur.fetchall()[0][0]

    cur.execute("DELETE FROM league_teams WHERE teamID = %s", (teamID))
    conn.commit()

    cur.execute("DELETE FROM teams WHERE teamName = %s", (data["teamName"]))
    conn.commit()

    return "done"

@app.route('/createLeague', methods = ['POST'])
def createLeague():

    data = request.get_json()
    
    load_dotenv() 

    conn = pymysql.connect(
            host= HOST, 
            port = PORT,
            user = USER, 
            password = PASSWORD,
            db = DB,
            )

    cur=conn.cursor()
    cur.execute("SELECT * FROM leagues WHERE leagueName = %s", (data["leagueName"]))
    isLeague = len(cur.fetchall())
    
    if (isLeague==0):

        cur.execute("INSERT INTO leagues (leagueName, leaguePass) VALUES (%s, %s)", (data["leagueName"], data["leaguePass"]))
        conn.commit()

        #gets the most recent leagueID
        cur.execute("SELECT * FROM leagues")
        leagueID = cur.fetchall()[len(cur.fetchall())-1][0]

        cur.execute("SELECT userID FROM users WHERE token = %s", (data["token"]))
        userID = cur.fetchall()[0][0]
        cur.execute("INSERT INTO league_teams (userID, leagueID, teamID) VALUES (%s, %s, null)", (userID, leagueID))
        conn.commit()

    elif (isLeague>0):
        print("already league")

    return "done"


@app.route('/getUsersLeagues', methods = ['POST'])
def getUsersLeagues():

    data = request.get_json()
    if data["token"] == None:
        return jsonify(leaguesList=None) 

    load_dotenv()

    conn = pymysql.connect(
            host= HOST, 
            port = int(PORT),
            user = USER, 
            password = PASSWORD,
            db = DB,
            )

    cur=conn.cursor()

    cur.execute("SELECT userID FROM users WHERE token = %s", (data["token"]))
    userID=cur.fetchall()[0][0]
    cur.execute("SELECT leagueID FROM league_teams WHERE userID = %s", (userID))
    userleagues = [i[0] for i in cur.fetchall()]
    # print(userleagues)
    cur.execute("SELECT * FROM leagues WHERE leagueID IN %s;", (userleagues,))
    result=cur.fetchall()

    leaguesList = []

    for league in result:
        leaguesList.append({"leagueID": league[0], "leagueName":league[1]})

    return jsonify(leaguesList=leaguesList)  

@app.route('/leaveLeague', methods = ['POST'])
def leaveLeague():

    data = request.get_json()
    
    load_dotenv()

    conn = pymysql.connect(
            host= HOST, 
            port = int(PORT),
            user = USER, 
            password = PASSWORD,
            db = DB,
            )

    cur=conn.cursor()

    cur.execute("DELETE FROM league_teams WHERE leagueID = %s", (data["leagueID"]))
    conn.commit()

    return "done"

@app.route('/joinLeague', methods = ['POST'])
def joinLeague():

    data = request.get_json()
    
    load_dotenv() 

    conn = pymysql.connect(
            host= HOST, 
            port = PORT,
            user = USER, 
            password = PASSWORD,
            db = DB,
            )

    cur=conn.cursor()
    cur.execute("SELECT * FROM leagues WHERE leaguePass = %s", (data["leaguePass"]))
    league = cur.fetchall()

    if (league!=()):

        leagueID = league[0][0]

        cur.execute("SELECT userID FROM users WHERE token = %s", (data["token"]))
        userID = cur.fetchall()[0][0]
        cur.execute("INSERT INTO league_teams (userID, leagueID, teamID) VALUES (%s, %s, null)", (userID, leagueID))
        conn.commit()

    elif (league==()):
        return "There is no league"

    return "done"

@app.route('/getPoints', methods = ['POST'])
def getPoints():
    data = request.get_json()
    e = ergast_py.Ergast()
    points = {}
    try:
        race_results = e.season().round(int(data["race"])).get_result().results
        quali_results = e.season().round(int(data["race"])).get_qualifying().qualifying_results
    except:
        race_results = e.season().round().get_result().results
        quali_results = e.season().round().get_qualifying().qualifying_results
    for i in race_results:
        if i.constructor.name not in points.keys():
            points[i.constructor.name] = int(i.points)
        else:
            points[i.constructor.name] += int(i.points)
        
        driverName = str(i.driver.given_name) + " " + str(i.driver.family_name)
        points[driverName] = int(i.points)
        if i.fastest_lap.rank == 1:
            points[driverName] += 5
        if (str(i.status)[0] == "1" and len(str(i.status))<3):
            points[driverName] += 1
        else:
            points[driverName] -= 10
    for j in quali_results:
        driverName = str(j.driver.given_name) + " " + str(j.driver.family_name)
        if j.qual_3 != None:
            points[driverName] += 3
        elif j.qual_2 != None:
            points[driverName] += 2
        elif j.qual_1 != None:
            points[driverName] += 1
        else:
            points[driverName] -= 5
        if j.position <= 10:
            points[driverName] += 11-j.position
    # print(points)

    return jsonify(points=points)  

@app.route('/getCosts', methods = ['POST'])
def getCosts():
    
    load_dotenv()

    conn = pymysql.connect(
            host= HOST, 
            port = PORT,
            user = USER, 
            password = PASSWORD,
            db = DB,
            )

    cur=conn.cursor()
    costs = {}
    cur.execute("SELECT driver, cost FROM drivers")
    drivers = cur.fetchall()
    for i in drivers:
        costs[i[0]] = i[1]
    cur.execute("SELECT constructor, cost FROM constructors")
    constructors = cur.fetchall()
    for i in constructors:
        costs[i[0]] = i[1]

    # print(costs)
    return jsonify(costs=costs)  

@app.route('/getLeagueInfo', methods = ['POST'])
def getLeagueInfo():

    data = request.get_json()
    
    load_dotenv() 

    conn = pymysql.connect(
            host= HOST, 
            port = PORT,
            user = USER, 
            password = PASSWORD,
            db = DB,
            )

    cur=conn.cursor()
    cur.execute("SELECT leagueName FROM leagues WHERE leagueID = %s", (data["leagueID"]))
    leagueName = cur.fetchall()[0][0]

    cur.execute("SELECT userID FROM league_teams WHERE leagueID = %s", (data["leagueID"]))
    leagueMembers = [i[0] for i in cur.fetchall()]

    # cur.execute("SELECT fname FROM users WHERE userID IN %s", (leagueMembers,))
    # leagueMembersNames = [i[0] for i in cur.fetchall()]

    memberTeamsList = {}
    # print(leagueMembers)
    # print(leagueMembersNames)
    
    for member in leagueMembers:
        cur.execute("SELECT teamID FROM league_teams WHERE userID = %s AND leagueID = %s",(member, data["leagueID"]))
        memberTeam = cur.fetchall()[0][0]
        # print(memberTeam)
        if memberTeam != None:

            cur.execute("SELECT fname FROM users WHERE userID = %s", (member))
            memberName = cur.fetchall()[0][0]

            cur.execute("SELECT slot1, slot2, slot3, slot4, slot5, slot6 FROM teams WHERE teamID = %s",(memberTeam))
            teamList = cur.fetchall()[0]

            cur.execute("SELECT driver, driverImg FROM drivers WHERE id IN %s",(teamList,))

            # memberTeamsList[leagueMembersNames[leagueMembers.index(member)]] = [{i[0]:i[1]} for i in cur.fetchall()]
            memberTeamsList[memberName] = [{i[0]:i[1]} for i in cur.fetchall()]
            

            cur.execute("SELECT constructor, constructorImg FROM constructors WHERE id = %s", (teamList[5]))
            constructor = cur.fetchall()
            
            
            if constructor!=():
                # memberTeamsList[leagueMembersNames[leagueMembers.index(member)]].append({constructor[0][0]:constructor[0][1]})
                memberTeamsList[memberName].append({constructor[0][0]:constructor[0][1]})
        # print(memberTeamsList)

    cur.execute("SELECT userID FROM users WHERE token = %s", (data["token"]))
    userID = cur.fetchall()[0][0]

    cur.execute("SELECT fname FROM users WHERE userID = %s", (userID))
    fname=cur.fetchall()[0][0]
    
    return jsonify(memberTeamsList=memberTeamsList, leagueName=leagueName, fname=fname)  

@app.route('/addToLeague', methods = ['POST'])
def addToLeague():
    
    load_dotenv()
    data = request.get_json()
    conn = pymysql.connect(
            host= HOST, 
            port = PORT,
            user = USER, 
            password = PASSWORD,
            db = DB,
            )

    # print(data["leagueID"])
    # print(data["token"])
    # print(data["teamID"])

    cur=conn.cursor()
    cur.execute("SELECT userID FROM users WHERE token = %s", (data["token"]))
    userID = cur.fetchall()[0][0]
    cur.execute("UPDATE league_teams SET teamID = %s WHERE userID = %s and leagueID = %s", (data["teamID"], userID, data["leagueID"]))
    conn.commit()

    return jsonify(nothing="") 

@app.route('/removeFromLeague', methods = ['POST'])
def removeFromLeague():
    
    load_dotenv()
    data = request.get_json()
    conn = pymysql.connect(
            host= HOST, 
            port = PORT,
            user = USER, 
            password = PASSWORD,
            db = DB,
            )

    cur=conn.cursor()
    cur.execute("SELECT userID FROM users WHERE token = %s", (data["token"]))
    userID = cur.fetchall()[0][0]
    cur.execute("UPDATE league_teams SET teamID = NULL WHERE userID = %s and leagueID = %s", (userID, data["leagueID"]))
    conn.commit()

    return jsonify(nothing="") 

if __name__ == "__main__":
    app.run(debug=True)


