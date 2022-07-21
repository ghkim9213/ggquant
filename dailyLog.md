# daily log

---

__2022-07-21__

- to-do
  - db 변경사항 요약
    - update를 collect 하는데 꽤 많은 시간이 걸림 (10sec)
    - 요청마다 데이터를 쿼리하는 방식은 좋지 않을 듯
    - 데이터가 크지 않기 때문에 미리 생성해둔 뒤 websocket 등을 통해 display하는 방식으로

  - deploy 준비
    - github
    - EC2 / RDS

  - tasks 자동화

- p.s.
  - 변경사항 요약을 위해 fd index에 createdAt 추가했으나, 적절한지 의문
    - 결국 사용되지 않을거라면 migrate 되돌리기: to 0008


__2022-07-20__

- to-do
  - db 변경사항 요약 (틀만 만들어놓고 내일 테스트)
    - changes in corp
    - changes in
  - rankings
    - inspect process (완료)
      - (기준1) oc는 섞지 않는다. 반드시 분리한다
      - (기준2) 하나의 값만 보고된 경우 그 값을 취한다
      - (기준3) 두개 이상의 값이 보고된 경우 dominant type의 값을 취한다
  - 현재 구현된 부분까지 최적화 (완료)
- p.s.


__2022-07-19__

- to-do
  - history (done)
  - front 수정

- p.s.
  - 별도재무제표가 하나도 없네 (수정완료)


__2022-07-18__

- to-do
  - update process for fs

- p.s.
  - update process for fs
    - if fs exists: pass
    - else: bulk create
    - anywhere: collect details
  - duplicates often occur in data?
    - if not:
      - drop duplicates in fs from odf.get_data() (done)
      - drop duplicates in fd from odf.get_data (done)



__2022-07-17__

- to-do
  - 최초 update process: 약 1시간 소요 (완료)

- p.s.



__2022-07-16__

- to-do
  - fs 수정
    - fsaccountmanager

- p.s.
  - bulk create 문제 발생: max allowed packet ~



__2022-07-15__

- to-do
  - fs 수정 (test version으로 만들기)
    - FsTree (완료)
    - FsTypeManager (완료)
    - OpendartFileManager (완료)

- p.s.
  - dominant relationship among trees -> acnt_id로 시도해보기
  - FsAccount에서는 nm만 관리
  - accountId는 FsDetail로



__2022-07-14__

- to-do
  - update process
    - corp (완료)
      - Corp은 stockCode 기준으로 관리 (상장사 중심)
    - fs
      - 좀더 간결하게 수정
      - 이후 update process 만들기

- p.s.
  - 신규상장된 경우 opendart 업데이트 문제로 corp_code: stock_code의 맵이 형성되지 않음 -> Corp모델의 corpCode null 허용
  - fsaccount version 삭제
    - 버전간 통합된 tree를 얻을 수 있는가
      - 통합 가능성
        - vs1의 x-y간 p-c관계가 vs2에서도 유지되는가



__2022-07-13__

- to-do
  - inpect 완성 (완료)
  - rankings 프로세스 전체 수정 (완료)

- p.s.
  - 극단치 제거 알림
  - datatables
    - spinner
    - header 먼저 전시되는 현상


__2022-07-12__

- to-do
  - inspect process 수정
    - IS, CIS, DCIS간 관계 반영 (완료)
      - [IS, CIS] = DCIS
    - OFS, CFS로 구분하면, 현재까지 사용된 변수 대부분 (기업, 분기)별 한개의 값이 match됨
      - 예외처리: 한 기업, 한 분기에 여러개 값이 존재하는 경우가 변수별 1개정도 확인됨

- p.s.

  - [BS1,BS2] >> [BS3,BS4]
    - 연결 계정은 별도 계정을 포함함: 별도 계정은 연결에도 있음
      - BS2 is a subset of BS1
      - BS4 is a subset of BS3
    - BS1이 BS3보다 지배적
    - BS1이 best

  - [CF3,CF4] >> [CF1,CF2]
    - 연결 계정은 별도 계정을 포함
      - CF2 subset CF1
      - CF4 subset CF3
    - CF3가 CF1보다 지배적
    - CF3이 best

  - [CIS1,CIS2] >>
    - CIS2 subset CIS1
    - CIS1 subset DCIS1
    - CIS1 subset DCIS5
    - CIS2 subset DCIS2
    - CIS2 subset DCIS6
    - CIS4 subset CIS3
    - CIS3 subset DCIS3
    - CIS3 subset DCIS7
    - CIS4 subset DCIS4
    - CIS4 subset DCIS8


  - [DCIS1,DCIS2] >>
  - [IS1,IS2] >>


__2022-07-11__

- to-do
  - visualizations of rankings
    - histogram 및 description (완료)

- p.s.
  - AccountRatio: get_data method에서 len(s) == 0인 경우 발생 (영업이익률 등 확인)
    - if len(s) == 0: 조회 가능 데이터에서 제외해야함
  - AccountRatio: 변동율 계산 안되고 있음



__2022-07-09__

- to-do
  - 조회결과 '결과{num}' 10개 이상인 경우 잘리는거 해결해야함 (완료)
  - recommend (완료)
  - 결과 전시
   - table (완료)

- p.s.
  - visualization
    - class로 만들기? manager?
    - histogram
      - (step1) plt.hist(series)로부터 graph data를 얻고
      - (step2) chart.js


__2022-07-08__

- to-do
  - [B] template에 inspect 결과 전시가 수월하도록 수정하기 (완료)
  - [B] recommend combination process 만들기
    - recommend process for mixed type

- p.s.
  - 조회결과 '결과{num}' 10개 이상인 경우 잘리는거 해결해야함
  - recommend 대충 완성했으나 mixed type에서 문제 생김 (부채비율 확인)
  - 관측치수가 거의 없는데도 추천해버림 (영업이익률 확인, oc_score and mthd_score기준 수정 필요)


__2022-07-06__

- to-do

- done
  - [B] model for AccountRatio (완료)

- p.s.
  - [B] template에 inspect 결과 전시가 수월하도록 수정하기
  - [B] recommend combination process 만들기


__2022-07-05__

- to-do
  - [F] inspect ar


- done

- p.s.


__2022-07-04__

- to-do
  - [B] optimization
    - inputs: [ar_name, ar_label_kor, ar_syntax]
    - process
      - (1) get all accounts
      - (2) num of dataset: unique or not
        - single dataset with single fstype -> no recommendation
        - multiple datasets for a single fstype -> recommend
        - single dataset with multiple fstype -> no recommendation
      -

- done
  - [B] optimization
    - by indexing: 35sec -> 2sec 시발 드디어
  - [F] inspect ar
    - input: syntax
    - outputs:
      - 추천필터
      - 미리보기

      <!-- - 데이터 요약 -->
- p.s.


__2022-07-01__

- to-do
  - [F] datatable.js
    - scrollX
    - tab by result
    - search
    - add most recent value column
    - add ranking column
    - wiki canvas
    - beautifulize column names

- done
  - [F] datatable.js
    - scrollX (완료)
    - tab by result
    - search (완료)
    - add most recent value column
    - ranking column
    - wiki canvas
    - beautifulize column names
  - [B] query 느려지는 상황 다시 발생
    - pandas가 문제인 것으로 보임


- p.s.



__2022-06-30__

- to-do
  - [F] data to table

- done
  - [B] ar.method별 fsType (완료)
    - 한 기업이 한 기간에 fstype별로 하나의 ca2cl을 가짐
    - 한 기업이 한 기간에 단 하나의 l2eatoop를 가짐
  - [B] orm optimization (완료)
    - model간 relationship을 활용할 때 select_related(many2one)이나 prefetch_related(one2many)를 설정해주어야만 related field의 id를 동반하여 한번에 query함
      - 속도 매우 줄였음. 100sec -> 3sec
    - 다만, 전시하는 데이터의 양이 많아 back to front에서 추가적인 3-5sec의 시간이 소요됨. [해결 요망]
  - [F] data to table
    - datatables.js로 결정

- p.s.
  - [B&F] wiki canvas in rankings



__2022-06-29__

- to-do
  - [B] view for rankings

- done
  - [B] view for rankings
    - sidebar (완료)
    - sidebar to data (완료)
    - data to table (미완)
      - bootstrap-table.js 이용
      - ar.method별로 fstype을 다루는 방식이 다를 가능성
        - 예를 들어, ca2cl은 한 기업에 대해 bs1, bs2 값이 각각 존재
        - 반면, tl2eo는 한 기업이 bs1, bs3 중 하나의 값만이 존재 (실제로 그러한지 확인)
      - pandas 이용하기 vs 직접 만지기


- p.s.


__2022-06-28__

- to-do
  - [B] dashboard/rankings process 최적화
  - [B] view for rankings

- done
  - [B] dashboard/rankings process 최적화
    - 그냥 pandas로 처리했음
  - [B] view for rankings (미완)
    - view manager 만들어보기
      - item_all -> item: {'label_kor': label_kor, }

- p.s.



__2022-06-27__

- to-do
  - [B] 재무제표 sorting
  - [F] datalib -> [F] dashboard rankings benchmarking 'oecd stats'
  - [B] 기본 재무비율을 위한 backend process 최적화

- done
  - [B] 재무제표 sorting 2022-06-24_done의 문제 해결 완료
  - [B] 기본 재무비율을 위한 ...
    - ca2cl
      - 내 코드로 하면 느림
      - pandas 이용하면 빨라지긴 함
      - pandas 이용하지 않고 빠르게 읽는법
      - pandas 이용시 drop duplicates에서 적절한 조치 필요: '한 fs에 두가지 표가 들어있는 경우, 먼저 나온 값을 이용한다'는 규칙을 적용하려 하나, pandas가 설정없이 sorting을 하기 때문에 어떤 값을 취하고 어떤 값을 버린 것인지 알 수 없음.

- p.s.
  - ca2cl
    - ('140890', 'BS2', 2015q4), ('140890', 'BS2', '2018q2') 한 fs 안에 두 가지 표가 들어있음...
    - 우선 첫번째 나타난 값만 이용


__2022-06-24__

- to-do
  - [F] fs in stkrpt
  - [F] datalib
  - [B] update corp
  - [B] update fs
  - [B] random price generator
  - 머환교수님 전화 반드시.

- done
  - 머환교수님과 통화했음. 한달 뒤에 다시 전화.
  - [F] fs in stkrpt
    - 현재 로직에서 꽤 잘 전시함
    - 몇 가지 잘 작동하지 않는 경우
      - 현재 로직은 fd 중 parent가 fdAll에 포함되지 않은 경우 parent account를 갖는 dummy fd를 포함시켰음
      - 직속 parent를 찾아서 추가하기보다는, fdAll 안에서 grand parent가 있는지 확인 후 연결하는 방식으로 해보기
      - (case 1) standard에서 두 계정이 parent, child 관계임에도 작성된 fs에서는 동등한 관계로 작성된 경우 (015360, BS1, 2022, 1)

- p.s.


__2022-06-23__

- to-do
  - [B] fs 모델 복합안으로
  - [B] update corp
  - [B] update fs
  - [B] random price generator
  - [F] fs in stkrpt
  - [F] datalib
  - 머환교수님 전화 반드시.

- done
  - [B] 마참내.. all for fs creation


- p.s.


__2022-06-22__

- to-do
  - [B] fs 모델 새롭게 만들기

- done


- p.s.
  - 개빡세네 ㅅㅂ
  - fslayout 추가했으나 모델이 너무 복잡해서 코딩하기 어려움
  - 이후 작업에서도 문제가 생길지도
  - 기존안 vs 새로운안 vs 짬뽕
  - vsMap 함수를 이용하면 짬뽕시켰을 경우 이점이 많을 것으로 예상됨
  - 집에가서 새로운 모델 고민해보기.


__2022-06-21__

- to-do
  - [B] fs 채우기: nstd 처리 중 에러 발생으로 중단되었음
  - [F] datalib
    - stkDataQueryForm
      - 1안 선구현 후 2안으로 발전시키기 (2022-06-20, dailyLog 참고)
        - (1안) a form for query items

- done
  - [B] nstd 처리코드 수정
    - (수정 전)
      - nstd account id로부터 pnm을 얻은 후 상응하는 pid를 얻음
    - (수정 후)
      - nstd account의 label_kor에 상응하는 std account가 있는지 확인
      - 있다면 상응하는 std account의 parent를 상속
      - 없다면 상응하는 std account를 찾는 것을 포기하고, 수정 전 방법을 이용해 parent만 입력
    - 수정 후 예상 가능한 오류
      - 만약

- p.s.
  - [B] 버전간 account_nm의 포함관계
    - 모든 fstype의 v0 -> v1에서 일부 계정이 삭제됨
    - 모든 fstype의 v1 -> v2 -> v3에서 계정 추가만이 발생함
    - 즉, v3 {include} v2 {include} v3 ~ v0
    - account_nm이 id처럼 작용
      - 하나의 account_nm에 버전별로 상이한 id 혹은 id간 parent/child 관계

  - [B] an issue in fstype__version
    - mixed type fs가 존재함: 재무제표를 과거 표준과 현재 표준을 섞어 작성한 경우
    - 데이터 입력 절차에서 이로인한 기계적 문제점은 존재하지 않음


__2022-06-20__

- to-do
  - [B] fs 채우기
  - [F] datalib

- done
  - [B] create FS process 완료
  - [B] FS 채우기 돌려놓고 집에 감
  - [F] datalib
    - stkDataQueryForm 초안 완료
      - (1안) 모든 선택 후 미리보기 -> 다운로드 방식
      - (2안) 1선택당 query 가능한 데이터 보여주기 + 함께 있을 때 유용한 데이터 추천 방식 (dashboard, wiki headword and keywords 연동)

- p.s.
  - query의 db화
    - 쿼리 분석으로부터 쿼리 추천 시스템
    - ...


__2022-06-18__

- to-do
  - [B] getMostSimilarVs 수정
  - [F] 꾸미기

- done
  - [B] getMostSimilarVs 수정 완료
  -

- p.s.
  - krx 모든 웹사이트 점검 0700-1900


__2022-06-17__

- to-do list
  - [B] testing fs creation process
  - [F] rearranging fsaccounts to display

- done
  - fs creation process
    - frontend를 통해 들어오는 데이터를 db에 입력하는 것이 아니라면, django orm을 이용해 입력하는 것보다 직접 db에 입력하는 것이 효율적
    - 즉, dashboard 데이터들은 모두 직접 입력해야함
      - corp 수정 완료
      - fstype 수정 완료
      - fsaccount 수정 완료
      - fs 수정 중
        - getMostSimilarVs 수정 필요
        - most-similar-score 동점인 경우 처리방식 고민


__2022-06-16__

- to-do list
  - [B] testing fs creation process
  - [F] FS query form
    - qform __(완료)__
    - rearranging fsaccounts to display


__2022-06-15__

- BACKEND
  - dashboard.models
    - FsAccount 수정 및 재입력 (완료)
    - Fs creation process
      - django orm이 아닌 mysql 직접입력

- FRONTEND
  - stkrpt 기업정보 (완료)
  - 검색창


__2022-06-14__

- dashboard.tasktools
  - (corp) CorpManager 수정
  - (fs) FsManger 수정

- dashboard.models
  - Corp 재입력 (완료)
  - FsType (완료), FsAccount 재입력

- dashboard.models Fs, FsDetail
    - 문제점
      - create에 너무 많은 시간이 소요됨
        - .2 sec per a line
        - 1파일당 약 10시간 소요될 것으로 추정
        - 2016년부터 2021년까지 총 6년 / 1년당 [1분기, 2분기, 3분기, 4분기] * [재무상태표, 손익계산서, 현금흐름표]의 12개 파일 => 72개 파일
        - 2015년 [4분기] * [재무상태표, 손익계산서, 현금흐름표] => 3개 파일
        - 2022년 현재 [1분기] * [재부상태표, 손익계산서, 현금흐름표] => 3개 파일
        - 78개 파일 * 10시간 = 780시간 (32일)
      - 원인: create에 line당 최소 .1초 정도 소요되는 django 자체의 문제 (최적화를 통해 create 속도를 현재 .2sec/line에서 .1sec/line으로 줄인다 하더라도 보름이 걸림)
      - 해결방안
        - db에 직접 입력 후 relationship field 수정 (테스트 해볼 것)

    - createFs()에 kwargs: 'option': ['fs_only','detail_only','both'] 추가
