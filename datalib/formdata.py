from dashboard.models import *
# from django import forms

UNIV_CHOICES_DICT = {
    'univAll': {
        'labelKor': '전체',
        'labelEng': 'all',
    },
    'univKOSPI': {
        'labelKor': '유가증권시장',
        'labelEng': 'KOSPI',
    },
    'univKOSDAQ': {
        'labelKor': '코스닥시장',
        'labelEng': 'KOSDAQ',
    },
}

STK_SELECTALL_CHOICES_DICT = {
    'ssAll': {
        'value': True,
        'labelKor': '전체',
        'labelEng': 'all',
    },
    'ssPick': {
        'value': False,
        'labelKor': '선택',
        'labelEng': 'pick',
    },
}

STK_CHOICES = [{'market': c.market, 'stockCode':c.stockCode, 'corpName': c.corpName} for c in Corp.objects.filter(stockCode__isnull=False)]

PRD_CHOICES_DICT = {
    'prdMax': {
        'labelKor': '최대',
        'labelEng': 'Max',
    },
    'prd1m': {
        'labelKor': '최근 1개월',
        'labelEng': 'recent 1 month'
    },
    'prd3m': {
        'labelKor': '최근 3개월',
        'labelEng': 'recent 3 months',
    },
    'prd6m': {
        'labelKor': '최근 6개월',
        'labelEng': 'recent 6 months',
    },
    'prd1y': {
        'labelKor': '최근 1년',
        'labelEng': 'recent 1 year',
    },
    'prdPick': {
        'labelKor': '직접 입력',
        'labelEng': 'pick',
    },
}

FRQ_CHOICES_DICT = {
    'frq1d': {
        'labelKor': '일별',
        'labelEng': 'day',
    },
    'frq1m': {
        'labelKor': '월별',
        'labelEng': 'month',
    },
    'frq1q': {
        'labelKor': '분기별',
        'labelEng': 'quarter',
    },
    'frq1y': {
        'labelKor': '연도별',
        'labelEng': 'year'
    }
}

QITEM_CHOICES_DICT = {
    'trading': ['open','high','low','close','vol'], # from ticks and minutes
    'fundamentals': {
        # a.accountNm: a.labelKor for a in FsAccount.objects.filter(accountNm__isnull=False)
    },
}
# d2c = lambda d: [(k:d[k]) for k in d.keys()]
#
#
#
# class StkDataQueryForm(forms.Form):
#     univ = forms.ChoiceField(
#         choices = d2c(UNIV_CHOICES_DICT),
#         required = True,
#         widget = forms.RadioSelect(
#             attrs = {
#                 'v-model': 'univSelected',
#             }
#         )
#     )
#
#     ssall = forms.ChoiceField(
#         choices = d2c(STK_SELECTALL_CHOICES_DICT),
#         required = True,
#         widget = forms.RadioSelect(
#             attrs = {
#                 'v-model': 'ssallSelected',
#             }
#         )
#     )
#
#     prd = forms.ChoiceField(
#         choices = d2c(PRD_CHOICES_DICT),
#         required = True,
#     )
#
#     # stk = forms.Choice
#
#
# class DataQueryForm(forms.Form):
#     queryType = forms.ChoiceField(
#         choices = QUERY_TYPE_CHOICES,
#         required = True,
#         widget = forms.Select(
#             attrs = {
#                 'class': 'form-select',
#                 # 'id': 'datalib-select-querytype',
#                 'v-model': 'queryType',
#             }
#         )
#     )
#     stkSelectAll = forms.ChoiceField(
#         choices = STK_SELECTALL_CHOICES,
#         required = True,
#         widget = forms.RadioSelect(
#             attrs = {
#                 'v-model': 'stkSelectAll',
#             }
#         )
#     )
#     stkSelect = forms.ChoiceField(
#         choices = STK_SELECT_CHOICES[:5],
#         widget = forms.Select(
#             attrs = {
#                 'class': 'selectpicker',
#                 'ref': 'stkSelect',
#                 'v-model': 'stkSelect',
#                 'data-live-search': 'true',
#             }
#         )
#     )
