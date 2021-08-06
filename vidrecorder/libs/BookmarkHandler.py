import os
# import datetime
# import sys

class BookmarkHandler():
    def __init__(self, pathDir, timeStamp):
        self.myPath = pathDir
        self.myTime = timeStamp

    def createBookmark(self, tagBox, descBox):
        bmPath = self.myPath + "/logs/"
        # if not os.path.isdir(dir_path):
        #     os.mkdir(dir_path)
        # if(not os.path.exists(bmPath)):
        #     open(bmPath,"w+")
        with open(bmPath + "bookmarks.txt", "a") as f:
            delim = "-"
            tagTxt = tagBox.get()
            descTxt = descBox.get()
            # f= open(bmPath,"a+")
            logLine = f"{self.myTime} {delim} {tagTxt} {delim} {descTxt}"
            f.write(logLine + "\n")
