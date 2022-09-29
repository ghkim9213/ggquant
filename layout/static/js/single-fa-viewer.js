class SingleFaViewer {
  constructor(stockCode, ws, chartId, controlId, colorPalette, faAll) {
    this.stockCode = stockCode;
    this.ws = ws;
    let config = {
      type: 'scatter',
      data: {
        labels: [],
        datasets: [],
      },
      options: {
        plugins: {
          legend: {
            display: false
          }
        },
        responsive: true,
        scales: {
          "yl": {
            type: 'logarithmic',
            display: true,
            positon: 'left',
            title: {
              text: '값 (KRW)',
              display: true,
            },
            ticks: {
              callback: function(value) {
                return intTickBeautifulizer(value)
              }
            }
          },
          "yr": {
            type: 'linear',
            display: true,
            position: 'right',
            title: {
              text: '변동율 (%)',
              display: true,
            },
            grid: {
              drawOnChartArea: false,
            },
          }
        },
      }
    };
    this.chart = new Chart(
      document.getElementById(chartId),
      config
    )
    this.control = $(`#${controlId}`);
    this.colorPalette = colorPalette;
    this.faAll = faAll;
    this.data = null;
    this.records = [];
  }

  activate() {
    let _this = this;
    new Promise(function(resolve) {
      _this.createControl();
      resolve();
    }).then(() => {
      // create dummy event for default input
      let e = {};
      e.target = '<div oc="CFS" nm="ProfitLoss"></div>';
      _this.query(e);
    });
  }

  createControl() {
    let controlTable = $(`
      <table class="table table-hover">
        <thead>
          <tr>
            <th scope="col" style="width: 5%"></th>
            <th scope="col" style="width: 10%">구분</th>
            <th scope="col" style="width: 25%">계정명</th>
            <th scope="col" style="width: 30%">표준경로</th>
            <th scope="col" style="width: 15%">상태</th>
            <th scope="col" style="width: 5%">색상</th>
            <th scope="col" style="width: 5%">값</th>
            <th scope="col" style="width: 5%">변동율</th>
          </tr>
        </thead>
        <tbody></tbody>
        <tfoot></tfoot>
      </table>
    `);
    let searchBar = $(`
      <tr class="fa-search-bar">
        <th scope="row">
          <button class="btn btn-outline-primary" id="activateFaSearchBtn">
            <i class="bi bi-plus-lg"></i>
          </button>
        </th>
        <td class="fa-search-bar fa-search-oc">-</td>
        <td class="fa-search-bar fa-search-lk">-</td>
        <td>-</td>
        <td>-</td>
        <td>-</td>
        <td>-</td>
        <td>-</td>
      </tr>
    `);
    let searchBtn = searchBar.find('button');
    let _this = this;
    searchBtn.click(function() {
      _this.faSearch();
    });
    controlTable.find('tfoot').append(searchBar);
    this.control.append(controlTable);
  }

  faSearch() {
    let _this = this;
    new Promise(function(resolve) {
      _this.createSearchBar();
      _this.createSearchContainer();
      resolve()
    }).then(() => this.searchFilter());
  }
  createSearchBar() {
    let bar = this.control.find('.fa-search-bar');
    let ocForm = $(`
      <select class="form-select">
        <option value="CFS" selected>연결</option>
        <option value="OFS">별도</option>
      </select>
    `);
    bar.find('.fa-search-oc').html('');
    bar.find('.fa-search-oc').append(ocForm);
    let lkForm = $(`
      <div class="input-group">
        <span class="input-group-text"><i class="bi bi-search"></i></span>
        <input class="form-control" type="text" id="faSearched" placeholder="당기순이익(손실)">
      </div>
    `);
    bar.find('.fa-search-lk').html('');
    bar.find('.fa-search-lk').append(lkForm);
  }
  createSearchContainer() {
    let controlTable = this.control.find('table');
    controlTable.find('caption').remove();
    let container = $(`<caption></caption>`);
    let closeBtn = $(`
      <button class="btn btn-close m-3"></button>
    `);
    let _this = this;
    closeBtn.click(function(e) {
      let _container = $(e.target).closest('caption');
      _container.remove();
    });
    let sc = $(`
      <p class="form-text m-3">해당 기업이 보고하지 않은 계정 혹은 K-IFRS 표준에 맞게 보고하지 않은 계정은 검색되지 않습니다.</p>
      <div class="d-flex flex-row">
        <p class="form-text m-3 fw-bold">검색된 계정</p>
        <div class="fa-matched m-3">
          <span class="form-text m-3">계정명을 입력하세요</span>
        </div>
      </div>
      <div>
        <p class="form-text m-3 fw-bold">검색 가능 계정 목록</p>
        <div class="fa-filtered fa-filtered-bs m-3">
          <p class="form-text">재무상태표</p>
        </div>
        <div class="fa-filtered fa-filtered-pl m-3">
          <p class="form-text">손익계산서</p>
        </div>
        <div class="fa-filtered fa-filtered-cf m-3">
          <p class="form-text">현금흐름표</p>
        </div>
      </div>
    `);
    container.append(closeBtn);
    container.append(sc);
    controlTable.append(container);
  }
  searchFilter() {
    let container = this.control.find('caption');
    let bar = this.control.find('.fa-search-bar');
    let _this = this;
    bar.find('.fa-search-oc select').change(function() {
      let oc = $(this).val();
      bar.find('.fa-search-lk input').keyup(function() {
        let lk = $(this).val();
        container.find('.fa-filtered span').remove();
        let fltrd = _this.faAll.filter(
          fa =>
          (fa.oc == oc)
          && (fa.lk.includes(lk))
        );
        for (let f of fltrd) {
          let ftDiv = f.ft_div.toLowerCase();
          let badge = $(`
            <span class="badge rounded-pill bg-secondary me-1" role="button" oc="${f.oc}" nm="${f.nm}">
              ${f.lk}
            </span>
          `);
          badge.click(function(e) {
            container.html('');
            container.css('display', 'none');
            bar.find('td').remove();
            bar.append(`
              <td class="fa-search-bar fa-search-oc">-</td>
              <td class="fa-search-bar fa-search-lk">-</td>
              <td>-</td>
              <td>-</td>
              <td>-</td>
              <td>-</td>
            `);
            _this.query(e);
          });
          container.find(`.fa-filtered-${ftDiv}`).append(badge);
        };

        let matched = container.find('.fa-matched');
        matched.find('span').remove();
        let m = _this.faAll.find(
          fa =>
          (fa.oc == oc)
          && (fa.lk == lk)
        );
        if (m) {
          let badge = $(`
            <span class="badge rounded-pill bg-success" role="button" oc="${m.oc}" nm="${m.nm}">
              ${m.lk}
            </span>
          `);
          badge.click(function(e) {
            container.html('');
            container.css('display', 'none');
            bar.find('td').remove();
            bar.append(`
              <td class="fa-search-bar fa-search-oc">-</td>
              <td class="fa-search-bar fa-search-lk">-</td>
              <td>-</td>
              <td>-</td>
              <td>-</td>
              <td>-</td>
            `);
            _this.query(e);
          });
          matched.append(badge);
        } else {
          matched.append(`
            <span class="form-text">매치된 계정이 없습니다. 계정명을 정확히 입력해주세요.</span>
          `);
        };
      }).trigger('keyup');
    }).trigger('change');
  }

  query(e) {
    this.createControlRow(e);
    this.send(e)
      .then(() => this.receive())
      .then(() => {
        this.updateControlRow(e);
        this.updateRecords()
          .then(() => this.updateChart());
      })
  }
  createControlRow(e) {
    let oc = $(e.target).attr('oc');
    let nm = $(e.target).attr('nm');
    let row = $(`
      <tr id="sfaControlRow-${oc}-${nm}">
        <th><button class="btn btn-close"></button></th>
        <td class="text-center" colspan="7">
          <div class="spinner-grow spinner-grow-sm text-success" role="status"></div>
        </td>
      </tr>
    `);
    this.control.find('tbody').append(row);
  }
  send(e) {
    let _this = this;
    return new Promise(function(resolve) {
      let oc = $(e.target).attr('oc');
      let nm = $(e.target).attr('nm');
      _this.ws.send(JSON.stringify({
        stockCode: _this.stockCode,
        oc: oc,
        nm: nm
      }));
      resolve();
    });
  }
  receive() {
    let _this = this;
    return new Promise(function(resolve) {
      _this.ws.onmessage = function(e) {
        _this.data = JSON.parse(e.data);
        _this.data.fa_info = JSON.parse(_this.data.fa_info);
        _this.data.chart_data.t = JSON.parse(_this.data.chart_data.t);
        _this.data.chart_data.y_val = JSON.parse(_this.data.chart_data.y_val);
        _this.data.chart_data.y_growth = JSON.parse(_this.data.chart_data.y_growth);
        let hex = _this.colorPalette.shift();
        _this.data.hex = hex;
        resolve();
      };
    });
  }
  updateControlRow(e) {
    let oc = $(e.target).attr('oc');
    let nm = $(e.target).attr('nm');
    let row = $(`#sfaControlRow-${oc}-${nm}`);
    let _this = this;
    row.find('.btn-close').click(function(e) {
      let _row = $(e.target).closest('tr');
      let _hex = _row.find('input[name="hex"]').val();

      // remove from records
      for (let r of _this.records) {
        delete r[`v${_hex}`];
        delete r[`g${_hex}`];
      }

      // remove from chart
      _this.chart.data.datasets = _this.chart.data.datasets.filter(
        ds =>
        (ds.label !== `v${_hex}`)
        && (ds.label !== `g${_hex}`)
      );
      _this.chart.update();

      // recover colorPalette
      _this.colorPalette.unshift(_hex);

      // remove row
      _row.remove();
    });

    let msg = (this.data.chart_data===null)?'데이터 없음':'전시 중';
    let clr = (this.data.chart_data===null)?'text-danger':'text-success';
    row.find('td').remove();
    let newTd = $(`
      <td class="result-cell result-cell-oc">${(oc==='CFS')?'연결':'별도'}</td>
      <td class="result-cell result-cell-lk">${(this.data.fa_info.lk)}</td>
      <td class="result-cell result-cell-path">${this.data.fa_info.path}</td>
      <td class="result-cell result-cell-status ${clr}">${msg}</td>
      <td class="result-cell result-cell-color"><i class="bi bi-square-fill" style="color: ${this.data.hex};"></i></td>
      <td class="result-cell">
        <div class="form-check form-switch">
          <input type="checkbox" class="form-check-input value-switch" checked>
        </div>
      </td>
      <td class="result-cell">
        <div class="form-check form-switch">
          <input type="checkbox" class="form-check-input growth-switch" checked>
        </div>
      </td>
      <input type="hidden" name="hex" value="${this.data.hex}">
    `);
    newTd.find('.value-switch').change(function(e) {
      let _row = $(e.target).closest('tr');
      let _hex = _row.find('input[name="hex"]').val();
      let tg = _this.chart.data.datasets.find(
        ds => ds.label === `v${_hex}`
      );
      if ($(this).is(':checked')) {
        tg.hidden = false;
      } else {
        tg.hidden = true;
      };
      _this.chart.update();
    });
    newTd.find('.growth-switch').change(function(e) {
      let _row = $(e.target).closest('tr');
      let _hex = _row.find('input[name="hex"]').val();
      let tg = _this.chart.data.datasets.find(
        ds => ds.label === `g${_hex}`
      );
      if ($(this).is(':checked')) {
        tg.hidden = false;
      } else {
        tg.hidden = true;
      };
      _this.chart.update();
    });
    row.append(newTd);
  }
  updateRecords() {
    let _this = this;
    return new Promise(function(resolve) {
      for (let [i, tp] of _this.data.chart_data.t.entries()) {
        let row = _this.records.find(
          r =>
          (r.tp === tp)
        );
        let v = _this.data.chart_data.y_val[i];
        let g = _this.data.chart_data.y_growth[i];
        if (row) {
          row[`v${_this.data.hex}`] = v;
          row[`g${_this.data.hex}`] = g;
        } else {
          row = {tp: tp};
          row[`v${_this.data.hex}`] = v;
          row[`g${_this.data.hex}`] = g;
          _this.records.push(row);
        }
      };
      _this.records.sort((a,b) => a.tp - b.tp);
      resolve();
    });
  }
  updateChart() {
    let x = this.records.map(
      row => dateFormatter(row.tp)
    );
    this.chart.data.labels = x;
    let n = this.records.map(
      row => Object.keys(row).length
    );
    let nMax = Math.max(...n);
    let fullRow = this.records.find(
      row =>
      Object.keys(row).length === nMax
    );
    for (let k of Object.keys(fullRow)) {
      if (k !== 'tp') {
        let vg = k.slice(0,1);
        let hex = k.slice(1);
        let alpha = (vg === 'v')?1:.5;
        let clr = hexToRgb(hex, alpha);
        let s = this.records.map(
          row => row[k]
        );
        let ds = this.chart.data.datasets.find(
          ds => ds.label === k
        );
        if (ds) {
          ds.data = s
        } else {
          if (vg === 'v') {
            ds = {
              type: 'line',
              label: k,
              data: s,
              borderColor: clr,
              yAxisID: 'yl',
            }
          } else {
            ds = {
              type: 'bar',
              label: k,
              data: s,
              borderColor: clr,
              backgroundColor: clr,
              yAxisID: 'yr'
            }
          };
          this.chart.data.datasets.push(ds);
        };
      };
    };
    this.chart.update();
  }
}
