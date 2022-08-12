from dashboard.models import *
from django.db.models import Max
# from ggdb.batchtools.temp import *

import datetime

class StkrptViewManager:

    def __init__(self, request):
        self.request = request
        stock_code = request.POST.get('stock_code')
        if stock_code == None:
            stock_code = '005930'
        self.corp = Corp.objects.get(stockCode=stock_code)

    def search(self):
        corp_all = Corp.objects.all()
        return json.dumps({c.corpName : c.stockCode for c in corp_all})

    def recent_history(self):
        today = datetime.datetime.today().date()
        recent_from = today - datetime.timedelta(weeks=12)
        fs_recent_fqe = self.corp.fs.all().aggregate(recent=Max('fqe'))['recent']

        ch_all = CorpHistory.objects.filter(corp=self.corp, updatedAt__gte=recent_from)
        ch_nm_map = {
            'market': '상장구분',
            'listedAt': '상장일',
            'ceo': 'CEO',
            'fye': '결산월',
            'industry': '업종',
            'homepage': '홈페이지',
            'product': '주요 상품',
        }
        ch_values = (
            [f"[{ch.updatedAt}] '{ch_nm_map[ch.changeIn]}' 항목이 '{ch.prevValue}'에서 '{getattr(self.corp, ch.changeIn)}'(으)로 변경되었습니다." for ch in ch_all]
            + [f"[{self.corp.createdAt}] ggdb가 KRX KIND의 {self.corp.corpName} ({self.corp.stockCode}) 기업정보 추적을 시작합니다."]
        )
        if self.corp.delistedAt != None:
            ch_values = [f"[{self.corp.delistedAt}] ggdb가 KRX KIND의 {self.corp.corpName} ({self.corp.stockCode}) 기업정보 추적을 종료합니다."] + ch_values

        recent_fs_all = Fs.objects.filter(corp=self.corp, fqe=fs_recent_fqe)
        recent_fs_values = [f"[{fs.createdAt}] ggdb가 OPEN DART의 {self.corp.corpName} ({self.corp.stockCode}) {fs.by}년도 {fs.bq}분기 ({fs.fqe}) '{fs.type.labelKor}' 추적을 시작합니다." for fs in recent_fs_all]

        recent_fdh_all = FsDetailHistory.objects.filter(fd__fs__corp=self.corp, updatedAt__gte=recent_from).select_related('fd','fd__fs', 'fd__fs__type')
        recent_fdh_values = []
        for fdh in recent_fdh_all:
            recent_fdh_values.append(f"[{fdh.updatedAt}] OPEN DART의 {self.corp.corpName} ({self.corp.stockCode}) {fdh.fd.fs.by}년도 {fdh.fd.fs.bq}분기 '{fdh.fd.fs.type.labelKor}' 내 '{fdh.fd.labelKor.strip()}' 계정이 {format(fdh.prevValue,',')} {fdh.fd.currency}에서 {format(fdh.fd.value,',')} {fdh.fd.currency}로 수정되었습니다.")

        recent_arvh_all = AccountRatioValueHistory.objects.filter(arv__corp=self.corp, updatedAt__gte=recent_from).select_related('arv')
        recent_arvh_values = [f"[{arvh.updatedAt}] OPEN DART 재무제표 데이터 수정에 따라 {self.corp.corpName} ({self.corp.stockCode}) {arvh.arv.by}년도 {arvh.arv.bq}분기 '{arvh.arv.ar.labelKor}'이 {round(arvh.prevValue,4)}에서 {round(arvh.arv.value,4)}로 수정되었습니다." for arvh in recent_arvh_all]
        return {
            '기업정보': ch_values,
            '재무제표': recent_fs_values,
            '재무제표 계정': recent_fdh_values,
            '재무비율': recent_arvh_values,
        }

    def ar_viewer(self):
        rows = AccountRatioCrossSectionManager().table_rows()

        ar_all = AccountRatio.objects.all()
        return {
            oc: {
                ar: ar.values.filter(corp=self.corp, method=oc)
                for ar in ar_all
            } for oc in ['CFS', 'OFS']
        }

    def fs_viewer(self):
        fs_all = self.corp.fs.all()
        fs_list = sorted([{
            'ftnm': fs.type.name,
            # 'label_kor': fs.type.labelKor,
            'by': fs.by,
            'bq': fs.bq,
        } for fs in fs_all], key=lambda x: (-x['by'], -x['bq']))

        if self.request.POST.get('fsFilter') == 'true':
            fs = self.corp.fs.filter(
                type__name = self.request.POST['ftnm_selected'],
                by = self.request.POST['by_selected'],
                bq = self.request.POST['bq_selected'],
            ).latest()
        else:
            fs = None
        treeview_data = get_treeview_data(fs)
        return {
            'fs_list': json.dumps(fs_list),
            'treeview_data': treeview_data,
        }


def get_parent_fd(fd, fd_prev_all):
    parent_acnt = fd.account.parent if fd.is_standard else fd.parent
    fd_parent = list(filter(lambda x: x.account == parent_acnt, fd_prev_all))
    if len(fd_parent) > 0:
        return fd_parent[0]
    else:
        fd_dummy = FsDetail(account=parent_acnt)
        return get_parent_fd(fd_dummy, fd_prev_all)


def get_treeview_data(fs):
    if fs == None:
        return None
    else:
        fd_all = fs.details.all()
        root_a = fd_all.first().account.parent
        title = f"{fs.corp.corpName}, {fs.type.labelKor}"

        fd_prev_all = []
        treeview_data = []
        if root_a not in [fd.account for fd in fd_all]:
            fd_prev_all.append(FsDetail(account=root_a))

        for i, fd in enumerate(fd_all):
            fd.labelKor = fd.labelKor.replace('[abstract]','').strip()
            fd_parent = get_parent_fd(fd, fd_prev_all)
            parent_in_tree = list(filter(lambda x: x['obj'] == fd_parent, treeview_data))
            pidt = parent_in_tree[0]['idt'] if len(parent_in_tree) > 0 else None
            treeview_data.append({
                'idt': i,
                'pidt': pidt,
                'obj': fd,
            })

            fd_prev_all.append(fd)
        return {'title': title, 'data': treeview_data}

# for d in treeview_data:
#     print(d, d['fd'].labelKor)
    # parent = fd.parent if fd.accountId.startswith('entity') else fd.account.parent
