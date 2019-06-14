#!/usr/bin/python3
#IMPORTANT! Before starting this script, please check if db table's names match with your dump


import mysql.connector, json, datetime, sys, os
from multiprocessing import Process, Queue

START_DATE = datetime.datetime(2014,1,1)
END_DATE = datetime.datetime(2015,1,1)
#YYYY-MM-DD HH:MM:SS datetime mysql format
READER_CORE_NUMBER = os.cpu_count()/4 if os.cpu_count()/4 >= 1 else 1
WRITER_CORE_NUMBER = os.cpu_count() - READER_CORE_NUMBER

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

def main_func(proc_number,questions_queue,answers_queue,comments_queue,postlinks_queue,postreferGH_queue,logger):
    mydb = mysql.connector.connect(
        host = "localhost",
        user = "santo",
        passwd = "root",
        database = "SistemiDistribuiti"
    )
    cursor = mydb.cursor()
    
    BLOCK_DIM = 1000
    
    questionIDs = []
    
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
            multiplier += WRITER_CORE_NUMBER
    
    for i in range(READER_CORE_NUMBER):
        questions_queue.put("DONE{}".format(i))
    logger.write("\nPROCESS {} - has {} questions.\n".format(proc_number,len(questionIDs)))

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
    
    for i in range(READER_CORE_NUMBER):
        answers_queue.put("DONE{}".format(i))
    logger.write("\nPROCESS {} - has {} posts.\n".format(proc_number,len(questionIDs)))

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
    
    for i in range(READER_CORE_NUMBER):
        comments_queue.put("DONE{}".format(i))
    logger.write("\nPROCESS {} - has finished comments.\n".format(proc_number))
    
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
    
    for i in range(READER_CORE_NUMBER):
        postlinks_queue.put("DONE{}".format(i))
    logger.write("\nPROCESS {} - has finished post links.\n".format(proc_number))

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

    for i in range(READER_CORE_NUMBER):
        postreferGH_queue.put("DONE{}".format(i))
    logger.write("\nPROCESS {} - has finished PostReferenceGH.\n".format(proc_number))
    
def read_queues(questions_queue,answers_queue,comments_queue,postlinks_queue,postreferGH_queue,logger,proc_number):
    queues=[questions_queue,answers_queue,comments_queue,postlinks_queue,postreferGH_queue]
    queues_obj = ["questions","answers","comments","postlinks","postreferGH"]
    container = []
    for i in range(len(queues)):
        done = 0
        logger.write("\nREADER {} - is starting iterating {}\n".format(proc_number, queues_obj[i]))
        
        while True:
            objs = queues[i].get()
            if str(res).startswith("DONE"):
                if objs == "DONE{}".format(proc_number):
                    done += 1
                    if done >= WRITER_CORE_NUMBER:
                        break
                else:
                    queues[i].put(objs)
                    continue
            else:
                container += objs
        
        logger.write("\nREADER {} - is start saving to json file: {}.json\n".format(proc_number, queues_obj[i]))
        with open("{}.json".format(queues_obj[i]),"a") as f:
            json.dump(container,f)
        container = None

if __name__ == '__main__':
    print("Process writer number: {}, Process reader number: {}".format(WRITER_CORE_NUMBER,READER_CORE_NUMBER))
    process_pool = []
    questions_queue = Queue()
    answers_queue = Queue()
    comments_queue = Queue()
    postlinks_queue = Queue()
    postreferGH_queue = Queue()

    for i in range(WRITER_CORE_NUMBER):
        print("Process {} started..\n".format(i))
        p = Process(target=main_func, args=(i,questions_queue,answers_queue,comments_queue,postlinks_queue,postreferGH_queue,sys.stdout))
        process_pool.append(p)
        p.start()
    for i in range(READER_CORE_NUMBER):
        print("Process reader started..\n")
        reader = Process(target=read_queues, args=(questions_queue,answers_queue,comments_queue,postlinks_queue,postreferGH_queue,sys.stdout))
        process_pool.append(reader)
        reader.start()
    
    for p in process_pool:
        p.join()




