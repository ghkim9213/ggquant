from dashboard.models import *

import datetime

class MainViewManager:
    DEFAULT_STOCK_CODE = '005930'
    CATEG = {
        'header': {
            'title': 'Dashboard',
            'desc': '지표별, 종목별, 포트폴리오별 분석결과를 제공합니다.',
        },
        'contents': {
            'indicators': {
                'title': '지표별 분석',
                'desc': '재무비율, 가격비율 등 다양한 지표들에 대한 종합분석결과를 조회합니다.',
                'url': '/dashboard/indicators',
                'disabled': False,
            },
            'stkrpt': {
                'title': '종목별 분석',
                'desc': '종목별 분석 보고서를 조회합니다. 관심종목에 대해 더 깊게 알아보세요.',
                'url': f'/dashboard/stkrpt/{DEFAULT_STOCK_CODE}',
                'disabled': False,
            },
            'pfrpt': {
                'title': '포트폴리오별 분석',
                'desc': '포트폴리오별 분석 보고서를 생성합니다. 당신의 포트폴리오를 입력하고 분석결과를 받아보세요.',
                'url': None,
                'disabled': True,
            },
        }
    }

    def __init__(self):
        self.today = datetime.datetime.today().date()
        # pass

    def dbrpt(self):
        # corp
        corp_listed_all = Corp.objects.filter(listedAt=self.today)
        corp_delisted_all = Corp.objects.filter(delistedAt=self.today)
        corp_history_all = CorpHistory.objects.filter(updatedAt=self.today)


        # fs
        fs_created_all = Fs.objects.filter(createdAt=self.today)
        fd_created_all = FsDetail.objects.filter(createdAt=self.today)
        fd_history_all = FsDetailHistory.objects.filter(updatedAt=self.today)
