import mysql.connector, json, datetime, sys

START_DATE = datetime.datetime(2014,1,1)
END_DATE = datetime.datetime(2015,1,1)
#YYYY-MM-DD HH:MM:SS datetime mysql format

# Connect to database
mydb = mysql.connector.connect(
    host = "localhost",
    user = "santo",
    passwd = "root",
    #database = "FilteredData"
    database = "SistemiDistribuiti"
)

#Aumented max_allowed_packet from 16M to 32M in order to made query with big strings

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



print("Start collecting question from {} to {}\n\n".format(datetime_parser(START_DATE)[1:-9],datetime_parser(END_DATE)[1:-9]))
start = datetime.datetime.now()
timer = datetime.datetime.now()

cursor.execute("SELECT * FROM Post WHERE PostTypeId = 1 AND CreationDate BETWEEN {} AND {}".format(datetime_parser(START_DATE,True),datetime_parser(END_DATE,True)))

print("Querying for question ended in {} seconds, waiting for fetch...\n\n".format((datetime.datetime.now() - timer).total_seconds()))
timer = datetime.datetime.now()

questions = rev_fetch_all(cursor=cursor,arraysize=2000,table="Post")

print("Fetching for question ended in {} seconds.\nFounded {} records.\nStarting preparing question ID list...\n\n".format((datetime.datetime.now() - timer).total_seconds(),len(questions)))
timer = datetime.datetime.now()

questionIDs = (str(list(map(lambda x: x["Id"] ,questions))))[1:-1]
print(questionIDs)
print("Size of question ID list is {} MB\n\n".format(sys.getsizeof(questionIDs)/(1024*1024)))

print("Questions ID list made in {} seconds.\nStarting querying for answers of each question ID...(please, be patients)\n\n".format((datetime.datetime.now() - timer).total_seconds()))
timer = datetime.datetime.now()

cursor.execute("SELECT * FROM Answers WHERE ParentId IN ({})".format(questionIDs))

print("Querying for answers ended in {} seconds, waiting for fetch...\n\n".format((datetime.datetime.now() - timer).total_seconds()))
timer = datetime.datetime.now()

answers = rev_fetch_all(cursor=cursor,arraysize=2000,table="Post")

print("Fetching for answers ended in {} seconds.\nFounded {} records.\nStarting exporting posts to JSON file \"Post.json\" and preparing answers ID list...\n\n".format((datetime.datetime.now() - timer).total_seconds(),len(answers)))
timer = datetime.datetime.now()

postIDs = questionIDs + ", " + (str(list(map(lambda x: str(x["Id"]) ,answers))))[1:-1]
print("Size of post ID list is {} MB\n\n".format(sys.getsizeof(postIDs)/(1024*1024)))
questions += answers
answers = None
del answers
questionIDs = None
del questionIDs
with open("Post.json","a") as f:
    json.dump(questions,f)
questions = None
del questions

print("JSON export and Answers ID list made in {} seconds.\nStarting querying for comments of each post ID...(please, be patients)\n\n".format((datetime.datetime.now() - timer).total_seconds()))
timer = datetime.datetime.now()

cursor.execute("SELECT * FROM Comments WHERE PostId IN ({})".format(postIDs))

print("Querying for comments ended in {} seconds, waiting for fetch...\n\n".format((datetime.datetime.now() - timer).total_seconds()))
timer = datetime.datetime.now()

comments = rev_fetch_all(cursor=cursor,arraysize=2000,table="Comments")

print("Fetching for comments ended in {} seconds.\nFounded {} records.\nStarting exporting to JSON file \"Comments.json\"...\n\n".format((datetime.datetime.now() - timer).total_seconds(),len(comments)))
timer = datetime.datetime.now()

with open("Comments.json","a") as f:
    json.dump(comments,f)
comments = None
del comments

print("JSON export made in {} seconds.\nStarting querying for post links of each post ID...(please, be patients)\n\n".format((datetime.datetime.now() - timer).total_seconds()))
timer = datetime.datetime.now()

cursor.execute("SELECT * FROM PostLinks WHERE PostId IN ({})".format(postIDs))

print("Querying for post links ended in {} seconds, waiting for fetch...\n\n".format((datetime.datetime.now() - timer).total_seconds()))
timer = datetime.datetime.now()

post_links = rev_fetch_all(cursor=cursor,arraysize=2000,table="PostLinks")

print("Fetching for post links ended in {} seconds.\nFounded {} records.\nStarting exporting to JSON file \"PostLinks.json\"...\n\n".format((datetime.datetime.now() - timer).total_seconds(),len(post_links)))
timer = datetime.datetime.now()

with open("PostLinks.json","a") as f:
    json.dump(post_links,f)
post_links = None
del post_links

print("JSON export made in {} seconds.\nStarting querying for post reference GitHub of each post ID...(please, be patients)\n\n".format((datetime.datetime.now() - timer).total_seconds()))
timer = datetime.datetime.now()

cursor.execute("SELECT * FROM PostReferenceGH WHERE PostId IN ({})".format(postIDs))

print("Querying for post reference GitHub ended in {} seconds, waiting for fetch...\n\n".format((datetime.datetime.now() - timer).total_seconds()))
timer = datetime.datetime.now()

post_GH = rev_fetch_all(cursor=cursor,arraysize=2000,table="PostReferenceGH")

print("Fetching for post reference GitHub ended in {} seconds.\nFounded {} records.\nStarting exporting to JSON file \"PostReferenceGH.json\"...\n\n".format((datetime.datetime.now() - timer).total_seconds(),len(post_GH)))
timer = datetime.datetime.now()

with open("PostReferenceGH.json","a") as f:
    json.dump(post_GH,f)
post_GH = None
del post_GH

print("JSON export made in {} seconds.\n\n\nWork completed in {} minutes, well done!".format((datetime.datetime.now() - timer).total_seconds(),(datetime.datetime.now() - start).total_seconds()/60))
