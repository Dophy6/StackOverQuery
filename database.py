import mysql.connector
from bs4 import BeautifulSoup
import simplejson as json
import sys
import webbrowser, os
import time
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

def writeFile(info):
    f = open("main.html","w+")
    f.write(info)
    f.close
    time.sleep(5)
    openBrowser()

def extractSnippet(body):
    soup = BeautifulSoup(body,'html.parser')
    snippet = soup.find_all('code')

    for row in snippet:
        print(row)
        print("------------------------------------")



def openBrowser():
    url = "file:///home/santino/Scrivania/Uni/sistemiDistribuiti/Progetto/Database/main.html"
    webbrowser.open(url)

def searchAnswers(id = 0,question = 0):
    try:
        answers = {}
        print("searching answers .. \n")
        if id == 0:
            cursor.execute("SELECT * FROM PostOriginale WHERE PostTypeId = 2 AND Body LIKE %s ORDER BY Score DESC",("%" + question + "%",))
            result = cursor.fetchall()
            for row in result:
                print(row[8],"\n")
                print("RILEVANT INFORMATION")
                pprint(scraper(row[8]))
                print("-----------")
        else:
            cursor.execute("SELECT * FROM PostOriginale WHERE PostTypeId = 2 AND ParentId = %s ORDER BY Score DESC",(id,))
            result = cursor.fetchall()
            for row in result:
                #Inserire nel dizionario i risultati ottenuti dalla funzione scraper "code": codice, "Reference Docs": link, "Reference GH": link
                answers[str(row[0])] = {
                    "body": row[8]
                }
            return answers

    except mysql.connector.Error as error:
        print("Failed to get record from database: {}".format(error))


def searchPostLink(id):
    cursor.execute(" SELECT * FROM PostLink WHERE RelatedPostId = (%s) ",(id,))
    result = cursor.fetchall()
    print("Questo post viene richiamato {} volte in altre discussioni!\n".format(len(result)))
    #print(result)  Inserire anche quali sono gli Id dei post che fanno riferimento a questa domanda disponibili in result



def searchQuestion(question = 0):
    try:
        cursor.execute("SELECT * FROM Post WHERE Title LIKE %s AND PostTypeId = 1 ORDER BY ViewCount DESC",("%" + question + "%",))
        collection = {}
        result = cursor.fetchall()
        for row in result:
            print("Id =", row[0])
            #print("PostTypeId =", row[1])
            #print("Accepted Answer ID = ", row[2])
            print("Title: ", row[15])
            print("View: ", row[7])
            print("Answers: ",row[17])
            print("Last Activity",row[14])
            #print("Body = ",row[8])
            print("---------------")

            collection[str(row[0])] = {
                "title": row[15], 
                "viewCount": row[7],
                "answerCount": row[17],
                "commentCount": row[18],
                "lastActivityDate": row[14],
                "body": row[8],
                "postTypeId": row[1],
                "acceptedAnswerId": row[2]

            }
        if result == []:
            print("No results found.. \n\n")
        else:
            print("Insert ID for more information...")
            id = sys.stdin.readline().strip('\n')
            searchPostLink(id)
            collection[str(id)]["comments"] = searchComment(id)
            pprint(collection[id]["comments"])
            #extractSnippet(collection[id]["body"])
            #pprint(scraper(collection[id]["body"]))
            collection[str(id)]["answers"] = searchAnswers(id)
            pprint(collection[id])

    except mysql.connector.Error as error:
        print("Failed to get record from database: {}".format(error))

def searchComment(question = 0, id = 0):
    try:
        print("searching comments .. \n")

        if id == 0:
            cursor.execute("SELECT * FROM Comments WHERE Text LIKE %s ORDER BY Score DESC",("%" + question + "%",))
        else:
            cursor.execute("SELECT * FROM Comments WHERE PostId = %s ORDER BY Score DESC",(id))

        result = cursor.fetchall()
        if result == []:
            print("No comments found.. \n\n")
        else:
            comments = {}
            for row in result:
                comments[str(row[0])] = {
                    "postId": row[1],
                    "score": row[2],
                    "text": row[3]
                }
            return comments

    except mysql.connector.Error as error:
        print("Failed to get record from database: {}".format(error))



def choose(argument):
    print("Please enter the request..")
    question = sys.stdin.readline().strip('\n')
    
    if argument == '1':
        searchQuestion(question)
    elif argument == '2': 
        searchAnswers(0,question)
    elif argument == '3':
        searchComment(question,0)

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