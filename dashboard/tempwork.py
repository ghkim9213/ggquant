from .viewmanagers.main import *

import time

mvm = MainViewManager()
self = mvm

dbrpt = []

corp_field_name_all = {
    'stockCode': '종목코드',
    'corpCode': 'DART고유번호',
    'corpName': '회사명',
    'industry': '업종명',
    'product': '주요생산품',
    'ceo': 'CEO',
    'homepage': '홈페이지',
    'district': '지역',
    'market': '상장구분',
    'fye': '결산월',
}

start = time.time()
# corp
corp_listed_all = Corp.objects.filter(listedAt=self.today)
print('corp_listed', corp_listed_all.count())
for corp in corp_listed_all:
    dbrpt.append({
        'status': 'success',
        'message': f"'{corp.corpName}'이(가) 생성되었습니다(예상 사유: 상장)."
    })
corp_delisted_all = Corp.objects.filter(delistedAt=self.today)
print('corp_delisted', corp_delisted_all.count())
for corp in corp_delisted_all:
    dbrpt.append({
        'status': 'danger',
        'message': f"'{corp.corpName}'이(가) 제거되었습니다(예상 사유: 상장 폐지)."
    })
corp_history_all = CorpHistory.objects.select_related('corp').filter(updatedAt=self.today)
print('corp_history', corp_history_all.count())
for ch in corp_history_all:
    dbrpt.append({
        'status': 'warning',
        'message': f"'{ch.corp.corpName}'의 {corp_field_name_all[ch.changeIn]}이 변경되었습니다: {ch.prevValue} -> {getattr(ch.corp, ch.changeIn)}."
    })


# fs
fs_created_all = Fs.objects.select_related('corp','type').order_by('-createdAt').filter(createdAt=self.today)
print('fs_created', fs_created_all.count())
for fs in fs_created_all:
    dbrpt.append({
        'status': 'success',
        'message': f"'{fs.corp.corpName}'의 {fs.by}년도 {fs.bq}분기 {fs.type.labelKor}가 생성되었습니다.",
    })
fd_created_all = FsDetail.objects.select_related('fs','fs__corp','fs__type').order_by('-createdAt').filter(createdAt=self.today)
print('fd_created', fd_created_all.count())
for fd in fd_created_all:
    dbrpt.append({
        'status': 'success',
        'message': f"'{fd.fs.corp.corpName}'의 {fd.fs.by}년도 {fd.fs.bq}분기 {fd.fs.type.labelKor}상 {fd.labelKor.strip()} 계정이 생성되었습니다: {fd.value}{fd.currency}."
    })
fd_history_all = FsDetailHistory.objects.select_related('fd','fd__fs','fd__fs__type').filter(updatedAt=self.today)
print('fd_history', fd_history_all.count())
for fdh in fd_history_all:
    dbrpt.append({
        'status': 'warning',
        'message':f"{fdh.fd.fs.corp.corpName}의 {fdh.fd.fs.by}년도 {fdh.fd.fs.bq}분기 {fdh.fd.fs.type.labelKor}상 {fdh.fd.labelKor.strip()} 계정의 값이 변경되었습니다: {fdh.prevValue}{fdh.fd.currency} -> {fdh.fd.value}{fdh.fd.currency}."
    })

print(time.time()-start)
