from dashboard.data_visualizers import *
from dashboard.models import *

class RankingsViewManager:
    def __init__(self):
        self.SORT_ORDER_AR = {
            '안정성': 0,
            '수익성': 1,
            '성장성 및 활동성': 2,
        }

    def sidebar(self):
        ar_all = sorted(
            AccountRatio.objects.all().values(),
            key = lambda ar: self.SORT_ORDER_AR[ar['div']]
        )
        ar_data = []
        prev_div = None
        for ar in ar_all:
            if ar['div'] != prev_div:
                ar_data.append({'is_button': False, 'div_name': ar['div']})
            ar_data.append({'is_button': True, **ar})
            prev_div = ar['div']
        return {
            'account-ratio': {
                'label_kor': '재무비율',
                'rows': ar_data,
            },
        }

    def main(self, request):
        if request.method == 'POST':
            if request.POST.get('queryData') == 'true':
                if request.POST['clsSelected'] == 'AccountRatio':
                    obj = AccountRatio.objects.get(name=request.POST['itemSelected'])
                    fields_lk = {
                        'market': '상장구분',
                        'stock_code': '종목코드',
                        'corp_name': '종목명',
                        'rank': '순위',
                        'pct': '상위(%)',
                        'recent': '최근',
                        'recent_value': '최근값',
                    }

                    selected_inpt_all = request.POST.getlist('selected-inpt')
                    selected_series_all = request.POST.getlist('selected-series')
                    df = obj.get_data(dict(zip(
                        selected_inpt_all,
                        selected_series_all,
                    )))
                    dv = DataVisualizer(df['recent_value'],bounds=[.005, .995])
                    df = df.reset_index().rename(columns=fields_lk)
                    df = df.round(4)
                    df = df.replace({np.nan:None, np.inf: None, -np.inf: None})#.replace(np.inf, None)
                    return {
                        'status': 'display_result',
                        'data': {
                            'abstract': {
                                'label_kor': obj.labelKor,
                                'syntax_katex': obj.syntax_katex,
                                # 'selected_label_kor': dict(zip(
                                #     [
                                #         obj.inspectResults[inpt]['label_kor']
                                #         for inpt in selected_inpt_all
                                #     ],
                                #     [
                                #         obj.inspectResults[inpt]['choices'][oc]['label_kor']
                                #         for inpt, oc in zip(selected_inpt_all,selected_series_all)
                                #     ]
                                # )),
                                'desc': dv.get_desc(),
                                'hist': dv.get_hist(),
                            },
                            'table': {
                                'header': df.columns.tolist(),
                                'rows': json.dumps(df.values.tolist())
                            }
                        }
                    }

            elif request.POST.get('inspectData') == 'true':
                obj = AccountRatio.objects.get(name=request.POST['itemSelected'])
                if obj.inspectResults == None:
                    obj.inspect()

                inspect_results = {FsAccount.objects.get(id=k): v for k, v in obj.inspectResults.items()}
                # for k in inspect_results.keys():
                #     inspect_results[FsAccount.objects.get(id=int(k))] = inspect_results.pop(k)
                # inspct = obj.inspectResults
                comb_all = list(itertools.product(*inspect_results.values()))
                print(inspect_results.keys())
                # arg_lk_all = [FsAccount.objects.filter(accountNm=arg).first().labelKor for arg in obj.arg_all]
                result_all = [{
                    'comb': dict(zip(obj.arg_all, [c['oc'] for c in comb])),
                    'comb_lk': dict(zip(
                        [arg.labelKor for arg in inspect_results.keys()],
                        [c['label_kor'] for c in comb]
                    )),
                    'is_same_oc': reduce(lambda a, b: a['oc'] == b['oc'], comb),
                    'is_all_cfs': reduce(lambda a, b: a & b, [c['oc'] == 'CFS' for c in comb]),
                } for comb in comb_all]
                result_all = sorted(result_all, key=lambda x: (-x['is_same_oc'],-x['is_all_cfs']))

                return {
                    'status': 'inspect',
                    'data': {
                        'abstract': {
                            'label_kor': obj.labelKor,
                            'syntax_katex': obj.syntax_katex,
                            'inspect_results': inspect_results,
                        },
                        'result_all': result_all,
                        'n_stock_all': Corp.objects.filter(listedAt__isnull=False).count(),
                        'clsSelected': request.POST['clsSelected'],
                        'itemSelected': request.POST['itemSelected'],
                    },
                }
        else:
            return None
