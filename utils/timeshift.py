import time
import datetime


class TimeShift:
    def __init__(self):
        pass

    @staticmethod
    def get_current_utc() -> datetime.datetime:
        utc_time = datetime.datetime.utcfromtimestamp(time.time())
        return utc_time

    @staticmethod
    def current_utc_format() -> str:
        utc_fmt = TimeShift.get_current_utc().strftime("%Y_%m_%d_%H_%M_%S")
        return utc_fmt

    @staticmethod
    def str_to_datetime(time_st):
        return datetime.datetime.strptime(time_st, "%Y_%m_%d_%H_%M_%S")

    @staticmethod
    def datetime_to_str(date):
        return date.strftime("%Y_%m_%d_%H_%M_%S")

    @staticmethod
    def get_local() -> datetime.datetime:
        local_time = datetime.datetime.now()
        return local_time

    @staticmethod
    def local_format() -> str:
        local_fmt = TimeShift.get_local().strftime("%Y-%m-%d %H:%M:%S")
        return local_fmt

    @staticmethod
    def utc_to_local(utc) -> datetime.datetime:
        now_stamp = time.time()
        local_time = datetime.datetime.fromtimestamp(now_stamp)
        utc_time = datetime.datetime.utcfromtimestamp(now_stamp)
        offset = local_time - utc_time
        local_st = utc + offset
        return local_st

    @staticmethod
    def local_to_utc(local_st) -> datetime.datetime:
        time_struct = time.mktime(local_st.timetuple())
        utc_st = datetime.datetime.utcfromtimestamp(time_struct)
        return utc_st

    @staticmethod
    def get_current_stamp():
        return int(time.time())

    @staticmethod
    def utc_to_stamp(utc_date_time):
        return TimeShift.local_to_stamp(TimeShift.utc_to_local(utc_date_time))

    @staticmethod
    def stamp_to_utc(local_stamp):
        return TimeShift.local_to_utc(TimeShift.stamp_to_local(local_stamp))

    @staticmethod
    def stamp_to_local(timestamp) -> datetime.datetime:
        return datetime.datetime. \
            fromtimestamp(timestamp)

    @staticmethod
    def local_to_stamp(localtime):
        return datetime.datetime.timestamp(localtime)

    @staticmethod
    def es_utc_str_to_stamp(localtime):
        """
        将本地时间转换成时间戳
        """
        return TimeShift.utc_to_stamp(datetime.datetime.strptime(localtime, "%Y-%m-%dT%H:%M:%S.%fZ"))

