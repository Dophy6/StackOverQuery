#!/usr/bin/python3

import mysql.connector, json, datetime, sys, os
from multiprocessing import Process, Queue

with open("config.json","r") as f:
    CONFIG = json.load(f)

START_DATE = datetime.datetime.strptime(CONFIG["DB_MAKER"]["START_DATE"], "%Y-%m-%d") if CONFIG["DB_MAKER"]["START_DATE"] != None and CONFIG["DB_MAKER"]["START_DATE"] != "" else None
END_DATE = datetime.datetime.strptime(CONFIG["DB_MAKER"]["END_DATE"], "%Y-%m-%d") if CONFIG["DB_MAKER"]["END_DATE"] != None and CONFIG["DB_MAKER"]["END_DATE"] != "" else None
#YYYY-MM-DD HH:MM:SS datetime mysql format
READER_CORE_NUMBER = (int(os.cpu_count()/4) if int(os.cpu_count()/4) >= 1 else 1) if CONFIG["DB_MAKER"]["READER_CORE_NUMBER"] == "DEFAULT" else int(CONFIG["DB_MAKER"]["READER_CORE_NUMBER"])
WRITER_CORE_NUMBER = (int(os.cpu_count() - READER_CORE_NUMBER)) if CONFIG["DB_MAKER"]["WRITER_CORE_NUMBER"] == "DEFAULT" else int(CONFIG["DB_MAKER"]["WRITER_CORE_NUMBER"])

def datetime_parser(mydatetime, mysql=True):
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
        container = list(map(lambda x: "{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{}\n".format(x[0],x[1],x[2],x[3],datetime_parser(x[4]),datetime_parser(x[5]),x[6],x[7],x[8],x[9],x[10],x[11],x[12],datetime_parser(x[13]),datetime_parser(x[14]),x[15],x[16],x[17],x[18],x[19],datetime_parser(x[20]),datetime_parser(x[21])), container))
    elif table == "Comments":
        container = list(map(lambda x: "{},{},{},{},{},{},{}\n".format(x[0],x[1],x[2],x[3],datetime_parser(x[4]),x[5],x[6]), container))
    elif table == "PostLinks":
        container = list(map(lambda x: "{},{},{},{},{}\n".format(x[0],datetime_parser(x[1]),x[2],x[3],x[4]), container))
    elif table == "PostReferenceGH":
        container = list(map(lambda x: "{},{},{},{},{},{},{},{},{},{},{},{},{},{},{}".format(x[0],x[1],x[2],x[3],x[4],x[5],x[6],x[7],x[8],x[9],x[10],x[11],x[12],x[13],x[14]), container))

    return container

def main_func(proc_number,questions_queue,answers_queue,comments_queue,postlinks_queue,postreferGH_queue,logger):
    mydb = mysql.connector.connect(
        host = "localhost",
        user = "root",
        passwd = "root",
        database = "SistemiDistribuiti"
    )
    cursor = mydb.cursor()
    
    BLOCK_DIM = 1000
    
    questionIDs = []
    
    while True:
        multiplier = proc_number
        limit = BLOCK_DIM*multiplier
        
        cursor.execute("SELECT * FROM Posts WHERE PostTypeId = 1 AND CreationDate BETWEEN {} AND {} LIMIT {},{}".format(datetime_parser(START_DATE,True),datetime_parser(END_DATE,True),limit,BLOCK_DIM))
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
        cursor.execute("SELECT * FROM Posts WHERE ParentId IN ({}) LIMIT {},{}".format(questionIDs, limit[0],limit[1]))
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
            if str(objs).startswith("DONE"):
                if objs == "DONE{}".format(proc_number):
                    done += 1
                    if done >= WRITER_CORE_NUMBER:
                        break
                else:
                    queues[i].put(objs)
                    continue
            else:
                container += objs
        
        "".join(container)
        logger.write("\nREADER {} - is start saving to csv file: {}.csv\n".format(proc_number, queues_obj[i]))
        with open("{}.csv".format(queues_obj[i]),"w") as f:
            f.write(container)
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
        print("Process {} reader started..\n".format(i))
        reader = Process(target=read_queues, args=(questions_queue,answers_queue,comments_queue,postlinks_queue,postreferGH_queue,sys.stdout,i))
        process_pool.append(reader)
        reader.start()
    
    for p in process_pool:
        p.join()




