# Distributed systems project

This project developed for Linux based sytems, provides a tool capable of performing research on a StackoverFlow datadump relating it to a GitHub datadump bidirectionally.

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

### Hardware requirements

At least you need of:
* Dual core processor(suggested);
* 350 GB of free space of which:
	- 150 GB in your main partition;
	- 200 GB wherever you want, also mounted from external drive;
* 8 GB of RAM(suggested);

### Automatic project configuration

First enter your preferences in the configuration file(*config.json*) then, if you want, you can just type in your terminal:

```
sh project_installation.sh
```

It will ask you sudo password so it can install all dependences and download all datadump.
Otherwise you can continue with the following guidelines.
In both cases you have to enter your preferences in the configuration file(*config.json*), the fileds are:
	
* DOWNLOAD_PATH => the path of the directory where download and save all big files (except database), do not use back-slash at the end of the path;
* **START_DATE** => the date from which the questions will be taken on StackoverFlow;
* **END_DATE** => the date up to which the questions on StackoverFlow will be taken;
* **READER_CORE_NUMBER** => Number of processes to be allocated for reading the queues for the *database_maker_in_csv.py* script(at least 1, DEFAULT is meant as 25% of your processor cores number)
* **WRITER_CORE_NUMBER** => Number of processes to be allocated for writing the queues for the *database_maker_in_csv.py* script(at least 1, DEFAULT is meant as 75% of your processor cores number)

### Prerequisites

In order to use this application you need of:

* Python 3.x;
* pip3;
* Mysql;
* mysql.connect

You can install them by pasting the following lines in your terminal:

```
sudo apt-get install python3
yes | sudo apt install python3-pip
pip3 install mysql-connector-python
sudo apt-get install -y mysql-server
sudo systemctl enable mysql.service
```

### Installing

First of all you need to download datadump with the following lines:

```
sudo wget -O <your/path>/Posts.xml.7z "https://zenodo.org/record/2628274/files/Posts.xml.7z?download=1"
sudo wget -O <your/path>/PostReferenceGH.csv.7z "https://zenodo.org/record/2628274/files/PostReferenceGH.csv.7z?download=1"
sudo wget -O <your/path>/PostLinks.xml.7z "https://zenodo.org/record/2628274/files/PostLinks.xml.7z?download=1"
sudo wget -O <your/path>/Comments.xml.7z "https://zenodo.org/record/2628274/files/Comments.xml.7z?download=1"
```

Then you can un-zipp them and delete the .7z old files.
Before you can create the database, you need to set mysql **root** account with **root** password or simply change code blocks inside both .py scripts where credentials are required.
Let's create the database(it could take some time) by pasting these lines in your terminal:

```
mysql -u root -proot <<EOF
CREATE DATABASE SistemiDistribuiti;
USE SistemiDistribuiti;
CREATE TABLE Posts (Id INT(11) NOT NULL PRIMARY KEY, PostTypeId TINYINT(4), AcceptedAnswerId INT(11), ParentId INT(11), CreationDate DATETIME, DeletionDate DATETIME, Score INT(11), ViewCount INT(11), Body TEXT, OwnerUserId INT(11), OwnerDisplayName VARCHAR(40), LastEditorUserId INT(11), LastEditorDisplayName VARCHAR(40), LastEditDate DATETIME, LastActivityDate DATETIME, Title VARCHAR(250), Tags VARCHAR(150), AnswerCount INT(11), CommentCount INT(11), FavoriteCount INT(11), ClosedDate DATETIME, CommunityOwnedDate DATETIME);
CREATE TABLE Comments (Id INT(11) NOT NULL PRIMARY KEY, PostId INT(11), Score INT(11), Text TEXT, CreationDate DATETIME, UserDisplayName VARCHAR(40), UserId INT(11));
CREATE TABLE PostLinks (Id INT(11) NOT NULL PRIMARY KEY, CreationDate DATETIME, PostId INT(11), RelatedPostId INT(11), LinkTypeId TINYINT(4));
CREATE TABLE PostReferenceGH (Id INT(11) NOT NULL PRIMARY KEY, FileId VARCHAR(40), Repo VARCHAR(255), RepoOwner VARCHAR(255), RepoName VARCHAR(255), Branch VARCHAR(255), Path TEXT, FileExt VARCHAR(255), Size INT(11), Copies INT(11), PostId INT(11), PostTypeId TINYINT(4), CommentId INT(11), SOUrl TEXT, GHUrl TEXT);
LOAD XML LOCAL INFILE "<your/path>/Comments.xml"
INTO TABLE Comments(Id, PostId, Score, Text, CreationDate, UserDisplayName, UserId);
LOAD XML LOCAL INFILE "<your/path>/Posts.xml"
INTO TABLE Posts(Id, PostTypeId, AcceptedAnswerId, ParentId, CreationDate,DeletionDate, Score, ViewCount, Body, OwnerUserId, OwnerDisplayName, LastEditorUserId, LastEditorDisplayName, LastEditDate, LastActivityDate, Title, Tags, AnswerCount, CommentCount, FavoriteCount, ClosedDate, CommunityOwnedDate);
LOAD XML LOCAL INFILE "<your/path>/PostLinks.xml"
INTO TABLE PostLinks(Id, CreationDate, PostId, RelatedPostId, LinkTypeId);
LOAD DATA LOCAL INFILE "<your/path>/PostReferenceGH.csv"
INTO TABLE PostReferenceGH
FIELDS TERMINATED BY ','
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(FileId, Repo, RepoOwner, RepoName, Branch, Path, FileExt, Size, Copies, PostId, @CommentId, SOUrl, GHUrl);
ALTER TABLE Posts ADD INDEX (Date);
ALTER TABLE Posts ADD INDEX (ParentId);
ALTER TABLE PostLink ADD INDEX (PostId);
ALTER TABLE Comments ADD INDEX (PostId);
ALTER TABLE PostReferenceGH ADD INDEX (PostId);
EOF
```
Now you can delete previous extracted datadump(Posts.xml, PostReferenceGH.csv, PostLinks.xml, Comments.xml), write in *config.json* ```<your/path>``` in "DOWNLOAD_PATH" field and then start Python3 script called *database_maker_in_csv.py* that have no needs of input parameters(it could take some time). After script finished you can recreate database, now sliced for years, depending on how you set up the configuration file(fields START_DATE and END_DATE) by pasting these lines in your terminal:

```
mysql -u root -proot <<EOF
USE SistemiDistribuiti;
DROP TABLE [IF EXIST] [Posts], [Comments], [PostLinks], [PostReferenceGH];
CREATE TABLE Questions (Id INT(11) NOT NULL PRIMARY KEY, PostTypeId TINYINT(4), AcceptedAnswerId INT(11), ParentId INT(11), CreationDate DATETIME, DeletionDate DATETIME, Score INT(11), ViewCount INT(11), Body TEXT, OwnerUserId INT(11), OwnerDisplayName VARCHAR(40), LastEditorUserId INT(11), LastEditorDisplayName VARCHAR(40), LastEditDate DATETIME, LastActivityDate DATETIME, Title VARCHAR(250), Tags VARCHAR(150), AnswerCount INT(11), CommentCount INT(11), FavoriteCount INT(11), ClosedDate DATETIME, CommunityOwnedDate DATETIME);
CREATE TABLE Answers (Id INT(11) NOT NULL PRIMARY KEY, PostTypeId TINYINT(4), AcceptedAnswerId INT(11), ParentId INT(11), CreationDate DATETIME, DeletionDate DATETIME, Score INT(11), ViewCount INT(11), Body TEXT, OwnerUserId INT(11), OwnerDisplayName VARCHAR(40), LastEditorUserId INT(11), LastEditorDisplayName VARCHAR(40), LastEditDate DATETIME, LastActivityDate DATETIME, Title VARCHAR(250), Tags VARCHAR(150), AnswerCount INT(11), CommentCount INT(11), FavoriteCount INT(11), ClosedDate DATETIME, CommunityOwnedDate DATETIME);
CREATE TABLE Comments (Id INT(11) NOT NULL PRIMARY KEY, PostId INT(11), Score INT(11), Text TEXT, CreationDate DATETIME, UserDisplayName VARCHAR(40), UserId INT(11));
CREATE TABLE PostLinks (Id INT(11) NOT NULL PRIMARY KEY, CreationDate DATETIME, PostId INT(11), RelatedPostId INT(11), LinkTypeId TINYINT(4));
CREATE TABLE PostReferenceGH (Id INT(11) NOT NULL PRIMARY KEY, FileId VARCHAR(40), Repo VARCHAR(255), RepoOwner VARCHAR(255), RepoName VARCHAR(255), Branch VARCHAR(255), Path TEXT, FileExt VARCHAR(255), Size INT(11), Copies INT(11), PostId INT(11), PostTypeId TINYINT(4), CommentId INT(11), SOUrl TEXT, GHUrl TEXT);
LOAD DATA LOCAL INFILE "\"$DOWNLOAD_PATH/questions.csv\""
INTO TABLE Questions
FIELDS TERMINATED BY ','
LINES TERMINATED BY '\n'
(Id, PostTypeId, AcceptedAnswerId, ParentId, CreationDate,DeletionDate, Score, ViewCount, Body, OwnerUserId, OwnerDisplayName, LastEditorUserId, LastEditorDisplayName, LastEditDate, LastActivityDate, Title, Tags, AnswerCount, CommentCount, FavoriteCount, ClosedDate, CommunityOwnedDate);
LOAD DATA LOCAL INFILE "\"$DOWNLOAD_PATH/answers.csv\""
INTO TABLE Answers
FIELDS TERMINATED BY ','
LINES TERMINATED BY '\n'
(Id, PostTypeId, AcceptedAnswerId, ParentId, CreationDate,DeletionDate, Score, ViewCount, Body, OwnerUserId, OwnerDisplayName, LastEditorUserId, LastEditorDisplayName, LastEditDate, LastActivityDate, Title, Tags, AnswerCount, CommentCount, FavoriteCount, ClosedDate, CommunityOwnedDate);
LOAD DATA LOCAL INFILE "\"$DOWNLOAD_PATH/comments.csv\""
INTO TABLE Comments
FIELDS TERMINATED BY ','
LINES TERMINATED BY '\n'
(Id, PostId, Score, Text, CreationDate, UserDisplayName, UserId);
LOAD DATA LOCAL INFILE "\"$DOWNLOAD_PATH/postlinks.csv\""
INTO TABLE PostLinks
FIELDS TERMINATED BY ','
LINES TERMINATED BY '\n'
(Id, CreationDate, PostId, RelatedPostId, LinkTypeId);
LOAD DATA LOCAL INFILE "\"$DOWNLOAD_PATH/postreferGH.csv\""
INTO TABLE PostReferenceGH
FIELDS TERMINATED BY ','
LINES TERMINATED BY '\n'
(FileId, Repo, RepoOwner, RepoName, Branch, Path, FileExt, Size, Copies, PostId, CommentId, SOUrl, GHUrl);
ALTER TABLE Questions ADD FULLTEXT (Title);
ALTER TABLE Answers ADD INDEX (ParentId);
ALTER TABLE Answers ADD FULLTEXT (Body);
ALTER TABLE PostLinks ADD INDEX (RelatedPostId);
ALTER TABLE Comments ADD INDEX (PostId);
ALTER TABLE Comments ADD FULLTEXT (Text);
ALTER TABLE PostReferenceGH ADD INDEX (PostId);
EOF
```

Now you can use our project simply typing:

```
python3 database_manager.py
```

and, following the requests by typing your search key-words, you'll get the required results in json format as well as (partially) on terminal.

## Authors

* **Merola Fabio** - *Initial work* - [Dophy6](https://github.com/Dophy6/)

* **Isgrò Santino** - *Initial work* - [SantinoI](https://github.com/SantinoI)

## Data source and dataset guide lines

* [Sebastian Baltes - The SOTorrent Dataset](https://empirical-software.engineering/projects/sotorrent/)

* [Sebastian Baltes - SOTorrent: Reconstructing and Analyzing the Evolution of Stack Overflow Posts](https://empirical-software.engineering/publications/#msr18-sotorrent)
