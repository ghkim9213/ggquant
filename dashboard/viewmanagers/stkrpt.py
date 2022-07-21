from dashboard.models import *

class StkrptViewManager:

    def __init__(self, request):
        self.request = request
        if request.method == 'POST':
            self.stock_code = request.POST.get('stock_code')
        else:
            self.stock_code = '005930'

    def search(self):
        corp_all = Corp.objects.all()
        return json.dumps({c.corpName : c.stockCode for c in corp_all})

    @property
    def corp(self):
        return Corp.objects.prefetch_related('fs','fs__type').get(stockCode=self.stock_code)

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
