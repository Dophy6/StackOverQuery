import mysql.connector, json, datetime, sys, os
from multiprocessing import Process, Queue

START_DATE = datetime.datetime(2014,1,1)
END_DATE = datetime.datetime(2015,1,1)
#YYYY-MM-DD HH:MM:SS datetime mysql format

CORE_NUMBER = os.cpu_count()

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

def main_func(proc_number,questions_queue,answers_queue,comments_queue,postlinks_queue,postreferGH_queue):
    mydb = mysql.connector.connect(
        host = "localhost",
        user = "santo",
        passwd = "root",
        database = "SistemiDistribuiti"
    )
    cursor = mydb.cursor()
    
    BLOCK_DIM = 1000
    
    questionIDs = []
    answersIDs = []
    
    while True:
        multiplier = proc_number
        limit = BLOCK_DIM*multiplier
        
        cursor.execute("SELECT * FROM Post WHERE PostTypeId = 1 AND CreationDate BETWEEN {} AND {} LIMIT {},{}".format(datetime_parser(START_DATE,True),datetime_parser(END_DATE,True),limit,BLOCK_DIM))
        questions = rev_fetch_all(cursor=cursor,arraysize=250,table="Post")
        
        questionIDs = (str(list(map(lambda x: x["Id"] ,questions))))[1:-1]
        questions_queue.put(questions)
        
        if len(questions) < BLOCK_DIM:
            break
        else:
            multiplier += CORE_NUMBER

    print("PROCESS {} has {} questions.\n".format(proc_number,len(questionIDs)))

    while True:
        limit= [0,BLOCK_DIM]
        cursor.execute("SELECT * FROM Answers WHERE ParentId IN ({}) LIMIT {},{}".format(questionIDs, limit[0],limit[1]))
        answers = rev_fetch_all(cursor=cursor,arraysize=250,table="Post")

        questionIDs += ", " + (str(list(map(lambda x: str(x["Id"]) ,answers))))[1:-1]
        answers_queue.put(answers)
        
        if len(answers) < BLOCK_DIM:
            break
        else:
            limit[0]+=BLOCK_DIM
            limit[1]+=BLOCK_DIM
    
    print("PROCESS {} has {} posts.\n".format(proc_number,len(questionIDs)))

    while True:
        limit= [0,BLOCK_DIM]
        cursor.execute("SELECT * FROM Comments WHERE PostId IN ({}) LIMIT {},{}".format(questionIDs, limit[0],limit[1]))
        comments = rev_fetch_all(cursor=cursor,arraysize=250,table="Comments")

        comments_queue.put(comments)
        
        if len(comments) < BLOCK_DIM:
            break
        else:
            limit[0]+=BLOCK_DIM
            limit[1]+=BLOCK_DIM
    
    print("PROCESS {} has finished comments.\n".format(proc_number))
    
    while True:
        limit= [0,BLOCK_DIM]
        cursor.execute("SELECT * FROM PostLinks WHERE PostId IN ({}) LIMIT {},{}".format(questionIDs, limit[0],limit[1]))
        post_links = rev_fetch_all(cursor=cursor,arraysize=250,table="PostLinks")

        postlinks_queue.put(post_links)
        
        if len(post_links) < BLOCK_DIM:
            break
        else:
            limit[0]+=BLOCK_DIM
            limit[1]+=BLOCK_DIM
    
    print("PROCESS {} has finished post links.\n".format(proc_number))

    while True:
        limit= [0,BLOCK_DIM]
        cursor.execute("SELECT * FROM PostReferenceGH WHERE PostId IN ({}) LIMIT {},{}".format(questionIDs, limit[0],limit[1]))
        post_GH = rev_fetch_all(cursor=cursor,arraysize=250,table="PostReferenceGH")

        postreferGH_queue.put(post_GH)
        
        if len(post_GH) < BLOCK_DIM:
            break
        else:
            limit[0]+=BLOCK_DIM
            limit[1]+=BLOCK_DIM
    
    print("PROCESS {} has finished PostReferenceGH.\n".format(proc_number))
    

if __name__ == '__main__':
    process_pool = []
    questions_queue = Queue()
    answers_queue = Queue()
    comments_queue = Queue()
    postlinks_queue = Queue()
    postreferGH_queue = Queue()
    
    for i in range(2*CORE_NUMBER):
        p = Process(target=main_func, args=(i,questions_queue,answers_queue,comments_queue,postlinks_queue,postreferGH_queue))
        process_pool.append(p)
        p.start()
    
    for p in process_pool:
        p.join()

    print("Starting saving questions")
    questions = []
    for q in questions_queue.get():
        questions += q
    with open("Questions.json","a") as f:
        json.dump(questions,f)
    questions = None
    del questions
    
    print("Starting saving answers")
    answers = []
    for q in answers_queue.get():
        answers += q
    with open("Answers.json","a") as f:
        json.dump(answers,f)
    answers = None
    del answers

    print("Starting saving comments")
    comments = []
    for q in comments_queue.get():
        comments += q
    with open("Comments.json","a") as f:
        json.dump(comments,f)
    comments = None
    del comments

    print("Starting saving post links")
    post_links = []
    for q in postlinks_queue.get():
        post_links += q
    with open("PostLinks.json","a") as f:
        json.dump(post_links,f)
    post_links = None
    del post_links

    print("Starting saving PostReferenceGH")
    post_GH = []
    for q in postreferGH_queue.get():
        post_GH += q
    with open("PostReferenceGH.json","a") as f:
        json.dump(post_GH,f)
    post_GH = None
    del post_GH
