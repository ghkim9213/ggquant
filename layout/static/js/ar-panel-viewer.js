class ArPanelViewer {
  constructor(
      formWrapperId,
      resultWrapperId,
      arChoices,
      ws,
      stockCode,
      legendMap,
  ) {
    this.form = $(`#${formWrapperId}`);
    this.result = $(`#${resultWrapperId}`);
    this.choiceData = JSON.parse(arChoices);
    this.ws = ws;
    this.stockCode = stockCode;
    this.ocSelected = 'CFS';
    this.nmSelected = 'ReturnOnEquity';
    this.dataSelected = null;
    this.panel = null;
    this.legendMap = legendMap;
  }

  activate() {
    this.createForm();
    this.form.find('select').trigger('change');
  }

  createForm() {
    let form = $(`
      <div class="position-relative">
        <div class="position-absolute top-50 start-50 translate-middle input-group" style="width: 50vh;">
          <button type="button" value="CFS" class="btn btn-outline-secondary btn-oc active" data-bs-toggle="button" autocomplete="off">연결</button>
          <button type="button" value="OFS" class="btn btn-outline-secondary btn-oc" data-bs-toggle="button" autocomplete="off">별도</button>
          <select class="form-select">
          </select>
        </div>
      </div>
    `);
    let _this = this;
    form.find('.btn-oc').click(function() {
      form.find('.btn-oc').removeClass('active');
      $(this).addClass('active');
      let oc = $(this).attr('value');
      _this.ocSelected = oc;
      _this.changeOptions(oc);
    });

    for (let ar of this.choiceData.CFS) {
      let optionText = ar.lk;
      if (ar.abbrev) {
        optionText = optionText + ` (${ar.abbrev})`
      }
      let option = $(`
        <option class="text-center" value="${ar.nm}">${optionText}</option>
      `);
      if (ar.nm === 'ReturnOnEquity') {
        option.attr('selected', true)
      };
      form.find('select').append(option)
    };
    form.find('select').change(function() {
      _this.nmSelected = $(this).val();
      let matched = _this.choiceData[_this.ocSelected].find(
        d => d['nm'] === $(this).val()
      );
      _this.query(matched.data);
    });
    this.form.append(form);
  }
  changeOptions(oc) {
    let options = this.choiceData[oc];
    this.form.find('option').remove();
    let _this = this;
    for (let ar of options) {
      let optionText = ar.lk;
      if (ar.abbrev) {
        optionText = optionText + ` (${ar.abbrev})`
      }
      let option = $(`
        <option class="text-center" value="${ar.nm}">${optionText}</option>
      `);
      if (ar.nm === 'ReturnOnEquity') {
        option.attr('selected', true)
      };
      this.form.find('select').append(option);
    };
  }

  query(data) {
    let _this = this;
    this.showLoader();
    this.createResultContainer()
      .then(() => this.createPanel(data))
      .then(() => this.displayPanel())
      .then(() => {
        this.showResultContainer();
        this.hideLoader();
      })
      .catch(function() {
        _this.showResultFail();
        _this.hideLoader();
      });
  }
  createResultContainer() {
    let _this = this;
    return new Promise(function(resolve) {
      _this.result.find('.result-container-main').remove();
      let container = $(`<div class="result-container result-container-main"></div>"`);
      let row = $(`<div class="row"></div>`);
      // let container = $(`<div class="row result-container result-container-main"></div>`);
      let chartArea = $(`
        <div class="col-8 row">
          <div class="chart-container" style="height: 40vh;">
            <canvas id="arpTsChart"></canvas>
          </div>
          <div class="chart-container" style="height: 40vh;">
            <canvas id="arpDistChart"></canvas>
          </div>
        </div>
      `);
      let controlArea = $(`
        <div class="col-4 table-responsive" style="height: 80vh;">
          <table class="table table-hover text-nowrap" id="arpChartControl">
            <thead>
              <tr>
                <th style="width: 20%">날짜</th>
                <th style="width: 20%">값</th>
                <th style="width: 15%">순위</th>
                <th style="width: 20%;">백분위</th>
                <th style="width: 25%;">평가</th>
              </tr>
            </thead>
            <tbody></tbody>
          </table>
        </div>
      `);
      let helpText = $(`
        <p class="form-text">* 분포도의 막대그래프는 히스토그램을, 실선그래프는 가우시안 커널 추정 분포를 의미합니다.</p>
      `);
      row.append(chartArea);
      row.append(controlArea);
      row.append(helpText);
      container.append(row);
      container.css('display', 'none');
      _this.result.append(container);
      resolve();
    });
  }
  showResultContainer() {
    this.result.find('.result-container-main').css('display', 'block');
  }
  showResultFail() {
    let fail = $(`
    <div class="position-relative result-container result-container-fail">
      <div class="position-absolute top-50 start-50 translate-middle text-center" id="arpResultLoader">
        <p class="text-muted fs-3">조회 가능한 데이터가 존재하지 않습니다.</p>
      </div>
    </div>
    `);
    fail.css({
      'height': '80vh',
      'border': '1px solid',
      'border-radius': '.25rem',
      'border-color': '#dee2e6'
    });
    this.result.append(fail);
  }
  hideResultContainer() {
    this.result.find('.result-container-main').css('display', 'none');
  }
  createPanel(data) {
    let _this = this;
    return new Promise(function(resolve) {
      _this.panel = new ArPanel(
        _this.stockCode,
        data,
        _this.ws,
        'arpTsChart',
        'arpDistChart',
        'arpChartControl',
      );
      _this.panel.tsChart.convertLegend(_this.legendMap);
      _this.panel.tsChart.showLegend();
      // _this.panel.distChart.convertLegend(_this.legendMap);
      _this.panel.distChart.hideLegend();
      resolve();
    });
  }
  displayPanel() {
    let _this = this;
    return new Promise(function(resolve, reject) {
      _this.panel.getTsData()
        .then(() => {
          _this.panel.resetTsChart();
          _this.panel.resetControl();
          resolve();
        })
        .catch(function() {
          reject()
        });
    })
  }

  showLoader() {
    this.result.find('.result-container-fail').remove();
    let loader = $(`
    <div class="position-relative result-container result-container-loader">
      <div class="position-absolute top-50 start-50 translate-middle text-center" id="arpResultLoader">
        <div class="spinner-grow text-muted mb-3" style="width: 3rem; height: 3rem;" role="status"></div>
        <p class="text-muted fw-bold">데이터베이스 조회 중</p>
      </div>
    </div>
    `);
    loader.css({
      'height': '80vh',
      'border': '1px solid',
      'border-radius': '.25rem',
      'border-color': '#dee2e6'
    });
    this.result.append(loader);
  }
  hideLoader() {
    this.result.find('.result-container-loader').remove();
  }
}
