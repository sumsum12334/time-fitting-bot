import discord
import os
import requests
import numpy as np
import random
import asyncio
import csv
import time
from skimage import io
import cv2
import urllib.request
from datetime import datetime
from pytz import timezone
import pymongo
from pymongo import ASCENDING, DESCENDING
from discord.ext import commands
import pandas as pd
import numpy as np

from discord_components import Button, Select, SelectOption, ComponentsBot
from dotenv import load_dotenv
import AI_discord

model,words,labels,data = AI_discord.setup('timefit')
wrong = ["Sorry I don't understand. Can you talk more clear?","Sorry, can you explain more?","I am not sure what you are saying. Could you please say again?"]
dbclient = pymongo.MongoClient(
    "mongodb+srv://pollywsleung:QQLyew67@chatbot.yeved.mongodb.net/myFirstDatabase?retryWrites=true&w=majority"
)
load_dotenv()
dbclient.drop_database('timefit')
db = dbclient.timefit
db2 = dbclient.Class

# intents = discord.Intents.default()
# intents.members = True
# timefitbot = discord.Client(intents=intents)
timefitbot = ComponentsBot('/')

format = "%Y-%m-%d %H:%M:%S"
format2 = "%Y-%m-%d %H:%M"

classlist_coll = "class_list_"
timefit_coll = "timefit_"

timefit = ["time", "timefit"]
matchinggp = ["match"]
setupgp = ["timefitsetup"]
outputcsvgp = ["outputcsv"]
selectmenugp = ["selectmenu"]
testgp = ["hi"]

text = {
    1: "Monday",
    2: "Tuesday",
    3: "Wednesday",
    4: "Thursday",
    5: "Friday",
    6: "Saturday",
    7: "Sunday"

}

async def get_message(message, origin, bot, private):
    def check(message):
        return message.content != origin

    try:
        msg = await bot.wait_for('message', timeout=60.0, check=check)
    except asyncio.TimeoutError:
        await private.send('Too slow reply.')
        return 'exit'
    else:
        await private.send('Ok')
        time.sleep(1)
        return msg


async def waiting(message, origin, mode, bot):
    def check(message):
        return message.content != origin

    msg = await bot.wait_for('message', check=check)

    await mode.send('Ok')

    time.sleep(1)
    return msg


def get_Output(final):
    result = "Grouping Result"
    for x in range(len(final)):
        header = "\n\nGroup " + str(x + 1) + "\n\n"

        temp = '\n'.join(
            str(a + 1) + ". " + str(final[x][a][0]) + "  " +
            str(final[x][a][1]) for a in range(len(final[x])))

        header += temp
        result += header

    return result


def check_identity(member,name):
  role_list = member.roles
  print(role_list)

  for role in role_list:
    if role.name == name:
      return True
  return False


async def output_avai(message, matching, avai, name,match_stud):

    if matching:
        # with open(name, 'w') as f:

        #     for k in avai.keys():
        #         f.write("%s %s\n" % (k, avai[k]))
        for i in range(1,8):
            while len(avai[i]) < 15:
                avai[i].append("")
        df = pd.DataFrame(avai) 
        # saving the dataframe 
        df.to_csv(name)
        with open(name, 'a') as f:
            f.write("\nMatching student:\n")
            for k in match_stud.keys():
                f.write("%s, %s\n" % (k,match_stud[k]))
    else:
        new_avai = {}
        for i, d in enumerate(avai):
            new_avai[i + 1] = d[1:]

        for i in range(1,8):
            while len(new_avai[i]) < 15:
                new_avai[i].append("")
        df = pd.DataFrame(new_avai) 
        # saving the dataframe 
        df.to_csv(name) 
        # for i in range(0,7):
        #     while len(avai[i]) < 16:
        #         avai[i].append("")
        # np.savetxt(name, 
        #    avai,
        #    delimiter =", ", 
        #    fmt ='% s')

    # await message.channel.send("Here is the csv file.")
    await message.send(file=discord.File(name))
    os.remove(name)
    return


async def output_csv(message):
    global occupied
    # timecollname = timefit_coll + message.guild.name
    # results = list(db[timecollname].find({}, {
    #     "no": 1,
    #     "avaitimeslot": 1,
    #     "_id": 0
    # }))
    if message.channel.name != "csv-receiving":
        await message.channel.send("Please go to the text channel 'csv-receiving' to output the csv.")
        return
        
    timecollname = timefit_coll + message.guild.name
    myquery = {"avaitimeslot":{"$ne": []}}
    results = list(db[timecollname].find(myquery, {
        "name": 1,
        "no": 1,
        "avaitimeslot": 1,
        "_id": 0
    }))
    noofstud = len(results)
    print(noofstud)
    if noofstud == 0:
      await message.channel.send("The students have not upload the timetable")
      return
    else:
      
      await message.channel.send(
    
          content="Whose available timeslots do you want to see?",
          components=[
              
              Select(
                
                  placeholder='Select Students:',
                  min_values=1,
                  max_values=noofstud+1,
                  options=[
                        
                        SelectOption(label=str(r["name"]+" "+r["no"]), value=r["no"]) 
                        for r in results
                        
                  ]+
                [SelectOption(label="All", value="all")],
                  
                  custom_id='SelectStudent')
            
          ])
      interaction = await timefitbot.wait_for(
          'select_option',
          check=lambda inter: inter.custom_id == 'SelectStudent' and inter.user
          == message.author)
      print("select student no:")
      print(interaction.values)
      await interaction.send("Ok, please wait...")
    if "all" in interaction.values:
        for r in results:
            no = r["no"]
            avai = r["avaitimeslot"]
            await output_avai(message.channel, False, avai,
                              "available_timeslot_" + no + ".csv","")
    else:
        for r in results:
            if r["no"] in interaction.values:
                
                no = r["no"]
                avai = r["avaitimeslot"]
                await output_avai(message.channel, False, avai,
                                "available_timeslot_" + no + ".csv","")
    occupied = False
    return


def intersection(list1, list2):
    result = []

    for value in list2:
        if value in list1:
            result.append(value)

    return result


# async def matching(message):
#     avai = []
#     dayDict = {}
#     timecollname = timefit_coll + message.guild.name
#     result = db[timecollname].find({}, {"avaitimeslot": 1, "_id": 0})

#     for r in result:
#         avai = (r["avaitimeslot"])
#         if not bool(dayDict):

#             for i, d in enumerate(avai):
#                 dayDict[i + 1] = d[1:]
#         else:
#             for i, d in enumerate(avai):
#                 inter = intersection(dayDict[i + 1], d[1:])
#                 dayDict[i + 1] = inter

#     print(dayDict)
#     await output_avai(message, True, dayDict, "match_availtimeslot.csv")
#     await message.channel.send("Here is the matched csv file.")
#     return


def match_time(t, SE):
    if SE == "e":
        t += 1
    return {
        1: 8,
        2: 9,
        3: 10,
        4: 11,
        5: 12,
        6: 13,
        7: 14,
        8: 15,
        9: 16,
        10: 17,
        11: 18,
        12: 19,
        13: 20,
        14: 21,
        15: 22,
        16: 23
    }.get(t, "no")


# async def setup(message):
#     print("enter setup function in timefit")
#     collname = classlist_coll + message.guild.name
#     myList = list(db2[collname].find({}))
#     timecollname = timefit_coll + message.guild.name
#     db[timecollname].insert_many(myList)
#     new = {"avaitimeslot": []}
#     db[timecollname].update_many({}, {"$set": new})
#     await message.channel.send(
#         "The timefit database is created. Students can upload the timetable by inputting 'time' in main channel."
#     )
#     return


async def time_fit(message):
    global occupied
    query = {"userid": message.author.id}
    print(message.author.id)
    timecollname = timefit_coll + message.guild.name
    result = list(db[timecollname].find(query, {
        "name": 1,
        "no": 1,
        "avaitimeslot": 1,
        "_id": 0
    }))
    print(result)
    name = result[0]["name"]
    no = result[0]["no"]
    if result[0]["avaitimeslot"] != []:
        await message.channel.send("You have submitted your timetable.")
        return

    origin = F"Hello, {name}. Please upload the timetable in png format."
    await message.author.send(origin)
    msg = await get_message(message, origin, timefitbot, message.author)
    try:
        url = msg.attachments[0].url
        name = msg.attachments[0].filename
        print(name)
    except:
        await message.channel.send("Wrong input!")
        return
    else:
        req = urllib.request.Request(url,
                                     headers={'User-Agent': 'Mozilla/5.0'})
        with open(name, "wb") as f:
            with urllib.request.urlopen(req) as r:
                f.write(r.read())

    image = cv2.imread(name)

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (3, 3), 0)
    thresh = cv2.threshold(blur, 127, 255,
                           cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

    # Morph open to remove noise and invert image
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    opening = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=1)
    # invert = 255 - opening
    # cv2.imshow('opening',opening)

    contours, hierarchy = cv2.findContours(opening, cv2.RETR_EXTERNAL,
                                           cv2.CHAIN_APPROX_SIMPLE)
    print('Total number of contours detected: ' + str(len(contours)))
    # cv2.drawContours(image,contours,2,(0,255,0),3)
    i = 0
    coorList = []
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)

        if cv2.contourArea(c) > 1500:

            print(x, " ", y, " ", x + w, " ", y + h)
            test = opening[y:y + h, x:x + w]
            black = int(np.sum(test == 0))
            white = int(np.sum(test == 255))
            if (black < white):
                coor1 = [x, y]
                coor2 = [x + w, y + h]
                temp = [coor1, coor2]
                print(temp)
                coorList.append(temp)
                i += 1
                print(i)
                # cv2.rectangle(image,(x,y), (x+w,y+h), (0,255,0), 5)

    coorList.sort()
    print(coorList)

    time = []
    day = []
    lesson = []
    x0 = coorList[0][0][0]
    y0 = coorList[0][0][1]
    i = 1
    while i < len(coorList):
        if coorList[i][0][0] == x0 or coorList[i][0][1] == y0:
            break
        i += 1

    if i >= len(coorList):
        x0 = coorList[1][0][0]
        y0 = coorList[1][0][1]
        coorList.remove(coorList[0])

    # print(x0,y0)

    for coor in coorList:
        print(coor[0][0], coor[0][1])
        print(coor[0][0] != x0)
        print(coor[0][1] != y0)
        print(coor[0][0] != x0 or coor[0][1] != y0)
        if coor[0][0] != x0 or coor[0][1] != y0:

            if coor[0][0] == x0:
                time.append(coor)

            elif coor[0][1] == y0:
                day.append(coor)

            else:
                lesson.append(coor)

    print('Day:\n', day, '\n')

    print('Time\n', time, '\n')

    print('Lesson\n', lesson, '\n')

    for d in day:
        cv2.rectangle(image, (d[0][0], d[0][1]), (d[1][0], d[1][1]),
                      (0, 255, 0), 5)

    # cv2.imshow('ttb',image)

    noavai = []

    for l in lesson:
        temp = []
        print(l)
        for y, d in enumerate(day):

            if l[0][0] <= d[0][0] + 10 and l[0][0] >= d[0][0] - 10:
                temp.append(y + 1)
                break

        for i, t in enumerate(time):

            if l[0][1] <= t[0][1] + 5 and l[0][1] >= t[0][1] - 5:
                temp.append(i + 1)

            if l[1][1] <= t[1][1] + 5 and l[1][1] >= t[1][1] - 5:
                temp.append(i + 1)
                break
        print(temp)
        st = match_time(temp[1], "s")
        et = match_time(temp[2], "e")
        temp[1] = st
        temp[2] = et
        print(temp)
        noavai.append(temp)

    print('Noavai\n', noavai, '\n')

    avai = []

    i = 0
    for d in range(1, 8):
        temp = []
        temptime = 8
        temp.append(d)

        while i < len(noavai):

            if noavai[i][0] != d:
                for j in range(temptime, 23):
                    temp.append(str(j) + "-" + str(j + 1))
                break
            else:
                while temptime < 23:

                    if temptime < noavai[i][1]:
                        temp.append(str(temptime) + "-" + str(temptime + 1))

                    if temptime >= noavai[i][2]:
                        break

                    temptime += 1
            i += 1
        if i >= len(noavai):
            for j in range(temptime, 23):
                temp.append(str(j) + "-" + str(j + 1))

        avai.append(temp)

    print(avai)
    myquery = {"userid": message.author.id}
    newvalues = {"$set": {"avaitimeslot": avai}}

    db[timecollname].update_one(myquery, newvalues)
    # await output_avai(message,False,avai,"available_timeslot_"+no+".csv")
    await message.author.send("The timetable is recorded successfully.")
    os.remove(name)
    occupied = False
    return


async def match_select(message):
    global occupied
    if message.channel.name != "matching":
        await message.channel.send("Please go to the text channel 'matching' for matching the timetable.")
        return
    timecollname = timefit_coll + message.guild.name
    myquery = {"avaitimeslot":{"$ne": []}}
    results = list(db[timecollname].find(myquery, {
        "name": 1,
        "no": 1,
        "avaitimeslot": 1,
        "_id": 0
    }))
    noofstud = len(results)
    print(noofstud)
    if noofstud == 0:
      await message.channel.send("The students have not upload the timetable")
      return
    else:
      
      await message.channel.send(
    
          content="Who do you want to match?",
          components=[
              
              Select(
                
                  placeholder='Select Students:',
                  min_values=1,
                  max_values=noofstud+1,
                  options=[
                        
                        SelectOption(label=str(r["name"]+" "+r["no"]), value=r["no"]) 
                        for r in results
                        
                  ]+
                [SelectOption(label="All", value="all")],
                  
                  custom_id='SelectStudent')
            
          ])
      interaction = await timefitbot.wait_for(
          'select_option',
          check=lambda inter: inter.custom_id == 'SelectStudent' and inter.user
          == message.author)
        
    
      print("select student no:")
      print(interaction.values)
      await interaction.send("OK, please wait...")

      avai = []
      dayDict = {}
      match_stud = {}
      if "all" in interaction.values:
        for r in results:
            match_stud[r["name"]] = r["no"]
            avai = (r["avaitimeslot"])
            if not bool(dayDict):
    
                for i, d in enumerate(avai):
                    dayDict[i + 1] = d[1:]
            else:
                for i, d in enumerate(avai):
                    inter = intersection(dayDict[i + 1], d[1:])
                    dayDict[i + 1] = inter

      else:
        for r in results:
          if r["no"] in interaction.values:
            match_stud[r["name"]] = r["no"]
            avai = (r["avaitimeslot"])
            if not bool(dayDict):
    
                for i, d in enumerate(avai):
                    dayDict[i + 1] = d[1:]
            else:
                for i, d in enumerate(avai):
                    inter = intersection(dayDict[i + 1], d[1:])
                    dayDict[i + 1] = inter
  
      print(dayDict)
    #   print(dayDict.items)
    #   await message.channel.send()
      outputList = "Available timeslot\n\n"
      for k in dayDict.keys():
        weekday = text.get(k)
        outputList += weekday + ": " 
        temp = ', '.join(
            dayDict[k][a] for a in range(1,len(dayDict[k])))
        outputList += temp + "\n"
      outputList += f"\nMatching Students:\n"
      temp = '\n'.join(
            f"{a} {match_stud[a]}" for a in match_stud.keys())
      outputList += temp
      
      print(outputList)
      await message.channel.send(outputList)
      await message.channel.send("The matching csv file is sent to the 'csv-receiving' text channel.")
      csv_receiving = discord.utils.get(message.guild.channels, name="csv-receiving")
      await csv_receiving.send("Here is the matched csv file.")
      await output_avai(csv_receiving, True, dayDict, "match_availtimeslot.csv",match_stud)
      
      occupied = False
      return

async def instruction(main):
  
    Embed = discord.Embed(title="Help page of time-fitting bot",
                            description="This is the chatbot which provides time fitting function. To convenice students and teachers use, please use the text channel in category 'TIME-FITTING' for time fitting function.",
                            color=discord.Color.blue())
    Embed.add_field(name = "Timetable upload",
                    value = "Students upload the timetable in text channel 'uploading'.\n\nExample of entering uploading timetable function:\nI want to upload the timetable",
                    inline = False)
    Embed.add_field(name = "Matching timetable",
                    value = "Teacher can match the students' timetable in text channel 'matching' with allowing to select different students.\n\nExample of entering matching timetable function:\nI want to match the timetable",
                    inline = False) 
    Embed.add_field(name = "Output students' timeslot",
                    value = "Teacher can output the students' available timeslot that extracted from timetable in text channel 'csv-receiving' with allowing to select different students.\n\nExample of entering output students' timeslot function:\nI want to output available timeslot",
                    inline = False)
    
    await main.send(embed=Embed)
    
    return

async def help(message):

    Embed = discord.Embed(title="Instruction",description="This is the chatbot which provides time fitting function. To convenice students and teachers use, please use the text channel in category 'TIME-FITTING' for time fitting function.", color=discord.Color.blue())
    await message.channel.send(embed=Embed)

@timefitbot.event
async def on_ready():
    print('We have logged in as {0.user}'.format(timefitbot))


@timefitbot.event
async def on_guild_join(guild):
    print(F"Joined in {guild}.")
    mainchannel = discord.utils.get(guild.channels, name="main")
    await instruction(mainchannel)
    print("enter setup function in timefit")
    collname = "class_list_" + guild.name
    myList = list(db2[collname].find({}))

    timecollname = "timefit_" + guild.name
    db[timecollname].insert_many(myList)
    new = {"avaitimeslot": []}
    db[timecollname].update_many({}, {"$set": new})

    await mainchannel.send(
        "The timefit database is created. Students can upload the timetable by talking with me in uploading channel."
    )

occupied = False
@timefitbot.event
async def on_message(message):
    global occupied
    if message.author == timefitbot.user:
        return
    if occupied:
        return 
    if message.channel.name != "uploading" and message.channel.name != "matching" and message.channel.name != "csv-receiving":
        return
    msg = message.content

    print("return to main")
    responses = AI_discord.chat(msg,model,words,labels,data)
    if responses != "wrong":
        print("responses = ")
        print(responses["responses"])
        await message.channel.send(random.choice(responses["responses"]))
        tag = responses["tag"]
        print("Tag = ")
        print(tag)
        if tag == "upload":
            if message.channel.name != "uploading":
                await message.channel.send("Please go to the text channel 'uploading' to start the process of uploading the timetable.")
                return
            if check_identity(message.author,"student"):
                occupied = True
                await time_fit(message)
            elif check_identity(message.author,"teacher"):
                await message.channel.send("Teacher does not need to upload the timetable.")
                return

        elif tag == "outputcsv":
            if check_identity(message.author,"student") or check_identity(message.author,"not verified"):
                await message.channel.send("You have no permission to output the csv file.")
                return
            if message.channel.name != "csv-receiving":
                await message.channel.send("Please go to the text channel 'csv-receiving' to start the process of outputting csv.")
                return
            occupied = True
            await output_csv(message)

        elif tag == "match":
            if check_identity(message.author,"student") or check_identity(message.author,"not verified"):
                await message.channel.send("You have no permission to match the timetable.")
                return
            if message.channel.name != "matching":
                await message.channel.send("Please go to the text channel 'matching' to start the process of matching the timetable.")
                return
            occupied = True
            await match_select(message)

        elif tag == "help":
            await instruction(message.channel)
    else:
        await message.channel.send(random.choice(wrong))



timefitbot.run(os.getenv('TOKEN2'))
