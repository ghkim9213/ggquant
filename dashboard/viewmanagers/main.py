from dashboard.models import *

import datetime

class MainViewManager:
    categ = {
        'header': {
            'title': 'Dashboard',
            'desc': '종목별, 포트폴리오별 실시간 분석결과 및 요인별 순위를 제공합니다.',
        },
        'contents': {
            'stkrpt': {
                'title': 'Stock Reports',
                'desc': '종목별 실시간 분석결과 보고서를 조회합니다. 보고서는 기업 개황, 최근 공시, 최근 컨센서스 등의 정보 또한 포함하고 있습니다.',
                'url': '/dashboard/stkrpt',
            },
            'pfrpt': {
                'title': 'Portfolio Reports',
                'desc': '포트폴리오별 실시간 분석결과 보고서를 조회합니다. 요인 포트폴리오 등 미리 준비된 포트폴리오뿐만 아니라 직접 입력한 포트폴리오에 대한 성과를 분석하고 추적할 수 있습니다.',
                'url': None,
            },
            'rankings': {
                'title': 'Rankings',
                'desc': '지표별 실시간 종목 순위를 조회합니다.',
                'url': '/dashboard/rankings',
            }
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
