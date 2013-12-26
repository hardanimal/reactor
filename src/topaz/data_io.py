from pymongo import MongoClient


class DUTStatus(object):
    IDLE = 1        # dut is waiting for burn in
    BLANK = 2       # dut is not inserted in the slot
    TESTING = 3     # dut is in burn in
    FAILED = 4      # dut has failed in burn in
    PASSED = 5      # dut has passed in burn in


class DB(object):
    """class to access the mongodb, save, update and check status
    """

    def __init__(self, dboption, dutlist):
        self.client = MongoClient(dboption["connectstring"])
        self.db = self.client[dboption["db_name"]]

        # collection for DUTs archived
        self.dutarchive = self.db[dboption["collection_archive"]]
        # collection for 128 running DUTs
        self.dutrunning = self.db[dboption["collection_running"]]
        self.dutlist = dutlist  # a list of dut number [1, 2, 3..]

    def init(self):
        """cleanup dut running db, set all status to idle.
        """
        self.dutrunning.remove()  # delete the real time status
        for i in self.dutlist:
            d = {"_id": i, "DUT_STATUS": DUTStatus.IDLE}
            self.dutrunning.save(d)

    def __check_status(self, dutnum):
        """check current dut status
        """
        d = self.dutrunning.find_one({"_id": dutnum})
        return d["DUT_STATUS"]

    def check_all_idle(self):
        """check if dut status are all not idle (test finish).
        """
        for i in self.dutlist:
            status = self.__check_status(i)
            if(status == DUTStatus.IDLE):
                return False    # still have idle board
        return True     # all not idle

    def fetch(self, dutnum):
        """read document of dutnum
        """
        d = self.dutrunning.find_one({"_id": dutnum})
        return d

    def update(self, d):
        """update dut running status
        """
        self.dutrunning.save(d)

    def archive(self):
        """save dut running status to archived
        """
        for i in self.dutlist:
            status = self.__check_status(i)
            if(status != DUTStatus.PASSED or status != DUTStatus.FAILED):
                # not passed or failed dut, no need to archive
                continue
            d = self.dutrunning.find({"_id": i})
            d.pop("_id")  # remove _id, archived will automatically generated
            self.dutarchived.save(d)

    def close(self):
        """close db connection
        """
        self.archive()
        self.client.close()
