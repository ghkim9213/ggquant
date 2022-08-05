def categories(request):
    return {'categories': {
        'dashboard': {
            'name': 'dashboard',
            'url': '/dashboard',
            'icon': 'bi bi-bar-chart-line-fill',
            'disabled': False,
            'helptext': [
                '종목별 실시간 거래 데이터, 공시데이터, 제무재표 데이터를 전시합니다',
                '항목별 실시간 순위를 전시합니다',
            ],
        },
        'datalab': {
            'name': 'datalab',
            'url': '/datalab',
            'icon': 'bi bi-boxes',
            'disabled': True,
            'helptext': [
                '데이터베이스에 등재된 데이터를 이용해 분석할 수 있는 python playground를 제공합니다',
                '분석결과를 보고서 형식으로 게시합니다',
            ],
        },
        'wiki': {
            'name': 'wiki',
            'url': '/wiki',
            'icon': 'bi bi-mortarboard-fill',
            'disabled': False,
            'helptext': [
                '자본시장관련 전반의 지식을 공유하는 오픈백과입니다',
                '엄격한 인용정책을 준수하며, 주기적으로 전문가들에 의해 검토됩니다'
            ],
        },
        'ggdb': {
            'name': 'ggdb',
            'url': '/ggdb',
            'icon': 'bi bi-cloud-download-fill',
            'disabled': False,
            'helptext': [
                '공유 데이터베이스에 등재된 데이터를 요청하고 다운로드합니다',
                '공유 데이터베이스에 접근 가능한 python module의 사용권한과 매뉴얼을 제공합니다'
            ],
        },
    }}
