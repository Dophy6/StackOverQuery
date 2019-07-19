#!/bin/bash

echo "Install requirements"

sudo apt update
sudo apt install p7zip-full
yes |sudo apt  install jq
sudo apt install -y debconf-utils

export DEBIAN_FRONTEND="noninteractive"

echo "mysql-server mysql-server/root_password password root" | sudo debconf-set-selections
echo "mysql-server mysql-server/root_password_again password root" | sudo debconf-set-selections
sudo apt-get install -y mysql-server

#mysql_secure_installation


#sudo mysql <<EOF
#ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY 'progetto_distribuiti19';
#FLUSH PRIVILEGES;
#exit;
#EOF

sudo systemctl enable mysql.service
sudo apt-get install python3
yes | sudo apt install python3-pip
pip3 install mysql-connector-python
#pip install multiprocessing

DOWNLOAD_PATH=$(jq -r '.INSTALLATION.DOWNLOAD_PATH' config.json) 
echo "Download path is: "$DOWNLOAD_PATH
# Downloading dump

echo "Start to download Posts.xml.7z"
sudo wget -O $DOWNLOAD_PATH"/Posts.xml.7z" "https://zenodo.org/record/2628274/files/Posts.xml.7z?download=1"
echo "Start to download PostReferenceGH.csv.7z"
sudo wget -O $DOWNLOAD_PATH"/PostReferenceGH.csv.7z" "https://zenodo.org/record/2628274/files/PostReferenceGH.csv.7z?download=1"
echo "Start to download PostLinks.xml.7z"
sudo wget -O $DOWNLOAD_PATH"/PostLinks.xml.7z" "https://zenodo.org/record/2628274/files/PostLinks.xml.7z?download=1"
echo "Start to download Comments.xml.7z"
sudo wget -O $DOWNLOAD_PATH"/Comments.xml.7z" "https://zenodo.org/record/2628274/files/Comments.xml.7z?download=1"

echo "Un-zipping and deleting dump.7z"

7za e $DOWNLOAD_PATH"/Posts.xml.7z" -o$DOWNLOAD_PATH
sudo rm $DOWNLOAD_PATH"/Posts.xml.7z"
7za e $DOWNLOAD_PATH"/PostReferenceGH.csv.7z" -o$DOWNLOAD_PATH
sudo rm $DOWNLOAD_PATH"/PostReferenceGH.csv.7z"
7za e $DOWNLOAD_PATH"/PostLinks.xml.7z" -o$DOWNLOAD_PATH
sudo rm $DOWNLOAD_PATH"/PostLinks.xml.7z"
7za e $DOWNLOAD_PATH"/Comments.xml.7z" -o$DOWNLOAD_PATH
sudo rm $DOWNLOAD_PATH"/Comments.xml.7z"

echo "Creating database and importing data"

mysql -u root -proot <<EOF
CREATE DATABASE SistemiDistribuiti;
USE SistemiDistribuiti;
CREATE TABLE Posts (Id INT(11) NOT NULL PRIMARY KEY, PostTypeId TINYINT(4), AcceptedAnswerId INT(11), ParentId INT(11), CreationDate DATETIME, DeletionDate DATETIME, Score INT(11), ViewCount INT(11), Body TEXT, OwnerUserId INT(11), OwnerDisplayName VARCHAR(40), LastEditorUserId INT(11), LastEditorDisplayName VARCHAR(40), LastEditDate DATETIME, LastActivityDate DATETIME, Title VARCHAR(250), Tags VARCHAR(150), AnswerCount INT(11), CommentCount INT(11), FavoriteCount INT(11), ClosedDate DATETIME, CommunityOwnedDate DATETIME);
CREATE TABLE Comments (Id INT(11) NOT NULL PRIMARY KEY, PostId INT(11), Score INT(11), Text TEXT, CreationDate DATETIME, UserDisplayName VARCHAR(40), UserId INT(11));
CREATE TABLE PostLinks (Id INT(11) NOT NULL PRIMARY KEY, CreationDate DATETIME, PostId INT(11), RelatedPostId INT(11), LinkTypeId TINYINT(4));
CREATE TABLE PostReferenceGH (Id INT(11) NOT NULL PRIMARY KEY, FileId VARCHAR(40), Repo VARCHAR(255), RepoOwner VARCHAR(255), RepoName VARCHAR(255), Branch VARCHAR(255), Path TEXT, FileExt VARCHAR(255), Size INT(11), Copies INT(11), PostId INT(11), PostTypeId TINYINT(4), CommentId INT(11), SOUrl TEXT, GHUrl TEXT);
LOAD XML LOCAL INFILE "\"$DOWNLOAD_PATH/Comments.xml\""
INTO TABLE Comments(Id, PostId, Score, Text, CreationDate, UserDisplayName, UserId);
LOAD XML LOCAL INFILE "\"$DOWNLOAD_PATH/Posts.xml\""
INTO TABLE Posts(Id, PostTypeId, AcceptedAnswerId, ParentId, CreationDate,DeletionDate, Score, ViewCount, Body, OwnerUserId, OwnerDisplayName, LastEditorUserId, LastEditorDisplayName, LastEditDate, LastActivityDate, Title, Tags, AnswerCount, CommentCount, FavoriteCount, ClosedDate, CommunityOwnedDate);
LOAD XML LOCAL INFILE "\"$DOWNLOAD_PATH/PostLinks.xml\""
INTO TABLE PostLinks(Id, CreationDate, PostId, RelatedPostId, LinkTypeId);
LOAD DATA LOCAL INFILE "\"$DOWNLOAD_PATH/PostReferenceGH.csv\""
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

echo "Deleting dump files"

rm $DOWNLOAD_PATH"/Posts.xml"
rm $DOWNLOAD_PATH"/PostReferenceGH.csv"
rm $DOWNLOAD_PATH"/PostLinks.xml"
rm $DOWNLOAD_PATH"/Comments.xml"

echo "Start script to build sliced db in csv"

python3 database_maker_in_csv.py

echo "Recreate database from csv"

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
