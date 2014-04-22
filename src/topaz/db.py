#!/usr/bin/env python
# encoding: utf-8
"""database interface for topaz bi.
"""
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from config import DUTStatus, DBOPTION


class DB(object):
    """class to access the mongodb, save, update and check status
    """

    def __init__(self, dutlist):
        self.client = MongoClient(DBOPTION["connectstring"])
        self.db = self.client[DBOPTION["db_name"]]

        # collection for DUTs archived
        self.dutarchive = self.db[DBOPTION["collection_archive"]]
        # collection for 128 running DUTs
        self.dutrunning = self.db[DBOPTION["collection_running"]]
        self.dutlist = dutlist  # a list of dut number [1, 2, 3..]
        self.setup()

    def setup(self):
        """cleanup dut running db, set all status to idle."""
        #self.dutrunning.remove()  # delete the real time status
        for i in self.dutlist:
            self.dutrunning.find_and_modify({"_id": i}, remove=True)
            d = {"_id": i, "STATUS": DUTStatus.IDLE}
            self.dutrunning.save(d)

    def fetch(self, dutnum):
        """read document of dutnum """
        d = self.dutrunning.find_one({"_id": dutnum})
        if not d:
            raise PyMongoError("dut {0} is not found.".format(dutnum))
        return d

    def update(self, d):
        """update dut in dutrunning """
        self.dutrunning.save(d)

    #def update_status(self, dutnum, status, msg=""):
    #    """update dut["STATUS"]"""
    #    d = self.dutrunning.find_one({"_id": dutnum})
    #    d["STATUS"] = status
    #    d["MESSAGE"] = msg
    #    self.dutrunning.save(d)

    def archive(self):
        """save dut running status to archived."""
        for i in self.dutlist:
            dut = self.fetch(i)
            status = dut["STATUS"]
            if(status != DUTStatus.PASSED and status != DUTStatus.FAILED):
                # not passed or failed dut, no need to archive
                continue
            d = self.dutrunning.find_one({"_id": i})
            d.pop("_id")
            self.dutarchive.save(d)

    def close(self):
        """close db connection."""
        self.archive()
        self.client.close()


if __name__ == "__main__":
    db = DB([1])
    db.setup()
    mydict = db.fetch(1)
    mydict.update({"SN": "123", "STATUS": "PASS"})
    db.update(mydict)
    db.close()
