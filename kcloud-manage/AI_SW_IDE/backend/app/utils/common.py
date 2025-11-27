from datetime import datetime, timedelta, timezone

KST = timezone(timedelta(hours=9))

def now_kst():
    return datetime.now(KST)