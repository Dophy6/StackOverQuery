import mysql.connector, json, sys, webbrowser, os, datetime
from pprint import pprint
ARRAY_SIZE = 50
timer=None
# Connect to database
mydb = mysql.connector.connect(
    host = "localhost",
    user = "santo",
    passwd = "root",
    #database = "FilteredData"
    database = "SistemiDistribuiti"
)
cursor = mydb.cursor()

def datetime_parser(mydatetime, mysql=False):
    if mydatetime == None: return mydatetime
    return mydatetime.strftime("'%Y-%m-%d %H:%M:%S'") if mysql else mydatetime.strftime("%Y-%m-%d %H:%M:%S")

def rev_fetch_all(cursor,arraysize,table=None):
    container = []
    while True:
        temp = cursor.fetchmany(arraysize)
        if not temp:
            break
        container += temp
        
    if table == "Post":
        container = list(map(lambda x: {"Id":x[0],"PostTypeId":x[1],"AcceptedAnswerId":x[2],"ParentId":x[3],"CreationDate":datetime_parser(x[4]),"DeletionDate":datetime_parser(x[5]),"Score":x[6],"ViewCount":x[7],"Body":x[8],"OwnerUserId":x[9],"OwnerDisplayName":x[10],"LastEditorUserId":x[11],"LastEditorDisplayName":x[12],"LastEditDate":datetime_parser(x[13]),"LastActivityDate":datetime_parser(x[14]),"Title":x[15],"Tags":x[16],"AnswerCount":x[17],"CommentCount":x[18],"FavoriteCount":x[19],"ClosedDate":datetime_parser(x[20]),"CommunityOwnedDate":datetime_parser(x[21])}, container))
    elif table == "Comments":
        container = list(map(lambda x: {"Id":x[0],"PostId":x[1],"Score":x[2],"Text":x[3],"CreationDate":datetime_parser(x[4]),"UserDisplayName":x[5],"UserId":x[6]}, container))
    elif table == "PostLinks":
        container = list(map(lambda x: {"Id":x[0],"CreationDate":datetime_parser(x[1]),"PostId":x[2],"RelatedPostId":x[3],"LinkTypeId":x[4]}, container))
    elif table == "PostReferenceGH":
        container = list(map(lambda x: {"Id":x[0],"FileId":x[1],"Repo":x[2],"RepoOwner":x[3],"RepoName":x[4],"Branch":x[5],"Path":x[6],"FileExt":x[7],"Size":x[8],"Copies":x[9],"PostId":x[10],"PostTypeId":x[11],"CommentId":x[12],"SOUrl":x[13],"GHUrl":x[14]}, container))

    return container

def writeFile(info,type):
    if type == "question":
        json_text = json.dumps(info)
        print(json_text)
        
def openBrowser():
    url = "file:///home/santino/Scrivania/Uni/sistemiDistribuiti/Progetto/Database/main.html"
    webbrowser.open(url)

def searchAnswers(id = 0,question = 0):
    try:
        print("searching answers .. \n")
        timer = datetime.datetime.now()
        if id == 0:
            cursor.execute("SELECT * FROM Answers WHERE Body LIKE %s ORDER BY Score DESC",("%" + question + "%",))
        else:
            cursor.execute("SELECT * FROM Answers WHERE ParentId = %s ORDER BY Score DESC",(id,))
        print("Query answers: {}".format((datetime.datetime.now()-timer).total_seconds()))
        timer = datetime.datetime.now()
        result = rev_fetch_all(cursor, ARRAY_SIZE, "Post")
        print("Fetch answers: {}".format((datetime.datetime.now()-timer).total_seconds()))
        return result

    except mysql.connector.Error as error:
        print("Failed to get record from database: {}".format(error))

def searchPostLink(id):
    cursor.execute(" SELECT * FROM PostLink WHERE RelatedPostId = (%s) ",(id,))
    return rev_fetch_all(cursor, ARRAY_SIZE, "PostLinks")

def searchReferenceGH(id):
    print("Searching referenceGH")
    cursor.execute(" SELECT * FROM PostReferenceGH WHERE PostId = (%s) ",(id,))
    return rev_fetch_all(cursor, ARRAY_SIZE, "PostReferenceGH")

def searchQuestion(question = 0):
    try:
        cursor.execute("SELECT * FROM Post WHERE Title LIKE %s AND PostTypeId = 1 ORDER BY ViewCount DESC",("%" + question + "%",))
        result = rev_fetch_all(cursor, ARRAY_SIZE, "Post")
        for row in result:
            print("Id = ", row["Id"])
            print("Title: ", row["Title"])
            print("View: ", row["ViewCount"])
            print("Answers: ",row["AnswerCount"])
            print("Last Activity: ",row["LastActivityDate"])
            print("---------------")
            #writeFile(collection[str(row[0])],"question")
        if result == []:
            print("No results found.. \n\n")
        else:
            print("Insert ID for more information...")
            id = sys.stdin.readline().strip('\n')
            selected = list(filter(lambda x: x["Id"]==int(id),result))[0]
            selected["postLink"] = searchPostLink(id)
            selected["answers"] = searchAnswers(id)
            selected["comments"] = searchComment(id)
            selected["referenceGH"] = searchReferenceGH(id)        
            pprint(selected)
    except mysql.connector.Error as error:
        print("Failed to get record from database: {}".format(error))

def searchComment(id = 0, question = 0,):
    try:
        print("searching comments .. \n")
        if id == 0:
            cursor.execute("SELECT * FROM Comments WHERE Text LIKE %s ORDER BY Score DESC",("%" + question + "%",))
        else:
            cursor.execute("SELECT * FROM Comments WHERE PostId = (%s) ORDER BY Score DESC", (id,))
        
        return rev_fetch_all(cursor, ARRAY_SIZE, "Comments")
    except mysql.connector.Error as error:
        print("Failed to get record from database: {}".format(error))

def searchSnippets(snippet):
    print("Searching snippets... ")

    cursor.execute("SELECT * FROM Answers WHERE Body LIKE %s ORDER BY Score DESC",("%" + snippet + "%",))
    result = rev_fetch_all(cursor, ARRAY_SIZE, "Post")
    result = list(map(lambda x: [x["ParenId"],scraper(x["Body"])]))
    return result        


def choose(argument):
    print("Please enter the request..")
    question = sys.stdin.readline().strip('\n')
    
    if argument == '1':
        searchQuestion(question)
    elif argument == '2': 
        pprint(searchAnswers(0,question))
        
    elif argument == '3':
        searchComment(0,question)
    elif argument == '4':
        pprint((searchSnippets(question)))

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