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
        

def openBrowser():
    url = "file:///home/santino/Scrivania/Uni/sistemiDistribuiti/Progetto/Database/main.html"
    webbrowser.open(url)

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
        answers = dict(map(lambda y: [str(y[0]),{"body": y[1],"snippets": y[2]["snippets"],"gh_repos": y[2]["gh_repos"],"docs": y[2]["docs"]}] , list(map(lambda x: [x[0],x[8],scraper(x[8])], result))))
        print("Fetch answers: {}".format((datetime.datetime.now()-timer).total_seconds()))
        return answers

    except mysql.connector.Error as error:
        print("Failed to get record from database: {}".format(error))

def searchPostLink(id):
    linkId = []
    postLinkId = {}
    cursor.execute(" SELECT * FROM PostLink WHERE RelatedPostId = (%s) ",(id,))
    result = cursor.fetchall()
    postLinkId = {
        "NumOfLink": len(result),
        "linkId": list(map(lambda x: x[2],result)) # Id di post che fanno rifermento al post analizzato
    }
    return postLinkId

def searchReferenceGH(id):
    print("Searching referenceGH")
    cursor.execute(" SELECT * FROM PostReferenceGH WHERE PostId = (%s) ",(id,))
    result = cursor.fetchall()
    return list(map(lambda x: {"repo": x[1],"branch": x[4],"copies": x[8],"SOUrl": x[11],"linkFile": x[12]},result))

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
        return dict(map(lambda x: [str(x[0]),{"postId": x[1],"score": x[2],"text": x[3]}] , result))

    except mysql.connector.Error as error:
        print("Failed to get record from database: {}".format(error))

def searchSnippets(snippet):
    print("Searching snippets... ")
    cursor.execute("SELECT * FROM Answers WHERE Body LIKE %s ORDER BY Score DESC",("%" + snippet + "%",))
    result = cursor.fetchall()
    return list(map(lambda x: (x[3],scraper(x[8])),result))       

def choose(argument):
    if argument not in ["1","2","3","4"]:
        print("\nFilter {} not available.\n".format(argument))
    else:
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
    return True if len(code)>15 and len(code.split()) > 1 and len(list(filter(lambda x: x not in code, [".",";","=","!","+","-","*",":","\"","\'","&","|","%"]))) > 0 else False

if __name__ == "__main__":
    main()