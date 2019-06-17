import mysql.connector
import json
import sys
import webbrowser, os
import datetime
from pprint import pprint

# Connect to database
mydb = mysql.connector.connect(
    host = "localhost",
    user = "santo",
    passwd = "root",
    #database = "FilteredData"
    database = "SistemiDistribuiti"
)
cursor = mydb.cursor()

def writeFile(info,type):
    if type == "question":
        with open('question.json', 'w') as f:
            json.dump(info,f, indent = 4)
    elif type == "moreInfo":
        with open('moreInfo.json', 'w') as f:
            json.dump(info, f, indent = 4)
    elif type == "answers":
        with open('answers.json', 'w') as f:
            json.dump(info, f, indent = 4)
    elif type == "comments":
        with open('comments.json', 'w') as f:
            json.dump(info, f, indent = 4)
    elif type == "snippets":
        with open('snippets.json', 'w') as f:
            json.dump(info, f, indent = 4)
        

def searchAnswers(id = 0,question = 0):
    try:
        answers = {}
        print("searching answers .. \n")
        timer = datetime.datetime.now()
        if id == 0:
            cursor.execute("SELECT * FROM Answers WHERE Body LIKE %s ORDER BY Score DESC",("%" + question + "%",))
        else:
            cursor.execute("SELECT * FROM Answers WHERE ParentId = %s ORDER BY Score DESC",(id,))
        print("Query answers: {}".format((datetime.datetime.now()-timer).total_seconds()))
        timer = datetime.datetime.now()
        result = cursor.fetchall()
        for row in result:
            info = scraper(row[8])
            answers[str(row[0])] = {
                "body": row[8],
                "snippets": info["snippets"],
                "gh_repos": info["gh_repos"],
                "docs": info["docs"]
            } 
        print("Fetch answers: {}".format((datetime.datetime.now()-timer).total_seconds()))
        return answers

    except mysql.connector.Error as error:
        print("Failed to get record from database: {}".format(error))

def searchPostLink(id):
    linkId = []
    postLinkId = {}
    cursor.execute(" SELECT * FROM PostLink WHERE RelatedPostId = (%s) ",(id,))
    result = cursor.fetchall()
    for row in result:
        linkId.append(row[2])   
    postLinkId = {
        "NumOfLink": len(result),
        "linkId": linkId # Id di post che fanno rifermento al post analizzato
    }
    return postLinkId

def searchReferenceGH(id):
    print("Searching referenceGH")
    referenceGH = []
    cursor.execute(" SELECT * FROM PostReferenceGH WHERE PostId = (%s) ",(id,))
    result = cursor.fetchall()

    for row in result:
        referenceGH.append({
            "repo": row[1],
            "branch": row[4],
            "copies": row[8],
            "SOUrl": row[11],
            "linkFile": row[12]
        })

    return referenceGH

def searchQuestion(question = 0):
    try:
        cursor.execute("SELECT * FROM Post WHERE Title LIKE %s AND PostTypeId = 1 ORDER BY ViewCount DESC",("%" + question + "%",))
        collection = {}
        result = cursor.fetchall()
        for row in result:
            print("Id =", row[0])
            print("PostTypeId =", row[1])
            #print("Accepted Answer ID = ", row[2])
            print("Title: ", row[15])
            print("View: ", row[7])
            print("Answers: ",row[17])
            print("LastActivity",row[14])
            #print("Body = ",row[8])
            print("---------------")


            collection[str(row[0])] = {
                "title": row[15], 
                "viewCount": row[7],
                "answerCount": row[17],
                "commentCount": row[18],
                "lastActivityDate": (str(row[14])),
                "body": row[8],
                "postTypeId": row[1],
                "acceptedAnswerId": row[2]
            }
        writeFile(collection,"question")
        if result == []:
            print("No results found.. \n\n")
        else:
            print("Insert ID for more information...")
            id = sys.stdin.readline().strip('\n')
            collection[str(id)]["postLink"] = searchPostLink(id)
            collection[str(id)]["answers"] = searchAnswers(id)
            collection[str(id)]["comments"] = searchComment(id)
            collection[str(id)]["referenceGH"] = searchReferenceGH(id)        
            writeFile(collection[id],"moreInfo")
            pprint(collection)
    except mysql.connector.Error as error:
        print("Failed to get record from database: {}".format(error))

def searchComment(id = 0, question = 0,):
    try:
        print("searching comments .. \n")
        if id == 0:
            cursor.execute("SELECT * FROM Comments WHERE Text LIKE %s ORDER BY Score DESC",("%" + question + "%",))
        else:
            cursor.execute("SELECT * FROM Comments WHERE PostId = (%s) ORDER BY Score DESC", (id,))

        result = cursor.fetchall()
        comments = {}
        for row in result:
            comments[str(row[0])] = {
                "postId": row[1],
                "score": row[2],
                "text": row[3]}

        return comments

    except mysql.connector.Error as error:
        print("Failed to get record from database: {}".format(error))

def searchSnippets(snippet):
    output = []
    print("Searching snippets... ")

    cursor.execute("SELECT * FROM Answers WHERE Body LIKE %s ORDER BY Score DESC",("%" + snippet + "%",))
    result = cursor.fetchall()
    for row in result:
        output.append((row[3],scraper(row[8])))
    return output        

def choose(argument):
    print("Please enter the request..")
    question = sys.stdin.readline().strip('\n')
    
    if argument == '1':
        searchQuestion(question)
    elif argument == '2': 
        result = (searchAnswers(0,question))
        pprint(result)
        writeFile(result,"answers")
    elif argument == '3':
        result = searchComment(0,question)
        pprint(result)
        writeFile(result,"comments")
    elif argument == '4':
        result = (searchSnippets(question))
        pprint(result)
        writeFile(result,"snippets")

def main():

    while True:
        print("Please choose the filter!")
        print("Press [1] to search a question")
        print("Press [2] to search an answers")
        print("Press [3] to search a comment")
        print("Press [4] to search code snap")
        x = sys.stdin.readline().strip('\n')
        choose(x)

def scraper(body):
    link = list(set(list(map(lambda x: (x.split("\""))[0], body.split("href=\"")))[1:]))
    code = list(set(list(filter(lambda x: is_code(x), list(map(lambda x: (x.split("</code>"))[0], body.split("<code>")))[1:]))))
    gh_link = list(set(list(filter(lambda x: "github.com/" in x, link))))
    link = (list(filter(lambda x: x not in gh_link, link)))
    return {"docs":link, "gh_repos":gh_link, "snippets":code}

def is_code(code):
    return True if len(code.split()) > 1 and len(list(filter(lambda x: x not in code, [".",";","=","!","+","-","*",":","\"","\'","&","|","%"]))) > 0 else False

if __name__ == "__main__":
    main()