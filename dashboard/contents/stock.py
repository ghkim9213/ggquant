from dashboard.models import *

def getParent(fa, truncFaAll):
    # loc = fdAll.index(fd)
    if fa.parent == None:
        return None
    elif fa.parent not in truncFaAll:
        return getParent(fa.parent, truncFaAll)
    else:
        return fa.parent


def get_clean_fd_all(fs):
    if fs == None:
        return None
    else:
        fd_all = fs.details.all()


def get_clean_fdAll(obj_fs):
    if obj_fs == None:
        return None
    else:
        fd_all = list(obj_fs.details.all())
        root = fdAll[0].account.parent
        title = f"{obj_fs.corp.corpName} {'별도' if obj_fs.type.oc == 'OFS' else '연결'} {root.labelKor.replace('[abstract]','')} ({obj_fs.by}년도 {obj_fs.bq}분기, {obj_fs.type.method})"
        if root not in [fd.account for fd in fdAll]:
            fdAll = [FsDetail(account=root)] + fdAll
        faAll = []
        clean_fdAll = []
        for i, fd in enumerate(fdAll):
            faAll.append(fd.account)
            parent = getParent(fd.account,faAll)
            clean_fd = {
                'id': i,
                'pid': faAll.index(parent) if parent != None else None,
                'labelKor': fd.account.labelKor.strip().replace('[abstract]',''),
                'value': fd.value,
                'currency': fd.currency,
                'isStandard': fd.account.isStandard,
            }
            clean_fdAll.append(clean_fd)
        return {'title': title, 'details': clean_fdAll[1:]}
