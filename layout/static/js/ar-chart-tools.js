class ArTsChart {
   constructor(chartId, colorPalette) {
     let config = {
       type: 'scatter',
       data: {
         labels: [],
         datasets: [],
       },
       options: {
         plugins: {
           legend: {
             labels: {
               filter: function(item, data) {
                 return !item.text.includes('Path')
               }
             }
           }
         }
       },
     };
     this.chart = new Chart(
       document.getElementById(chartId),
       config
     );
     this.colorPalette = colorPalette;
   }

   update(data) {
     // parsing data
     let x = data.t;
     let y = data.val;

     // update ts chart
     this.chart.data.labels = x.map(tp => dateFormatter(tp));
     this.chart.data.datasets.push({
       type: 'line',
       label: 'valPath',
       data: y,
       borderColor: hexToRgb(this.colorPalette[1], 1),
       pointRadius: 3,
     });
     this.chart.update();
   }

   clear() {
     this.chart.data.labels = [];
     this.chart.data.datasets = [];
     this.chart.update();
   }

   showLegend() {
     this.chart.options.plugins.legend.display = true;
   }
   hideLegend() {
     this.chart.options.plugins.legend.display = false;
   }
   convertLegend(data) {
     this.chart.options.plugins.legend.labels.generateLabels = function(chart) {
       let labels = Chart.defaults.plugins.legend.labels.generateLabels(chart);
       for (let lab of labels) {
         if (data[lab.text]) {
           lab.text = data[lab.text];
         };
       }
       return labels
     }
   }
};

class ArDistChart {
   constructor(chartId, colorPalette) {
     let config = {
       type: 'scatter',
       data: {
         labels: [],
         datasets: [
           {
              type: 'bar',
              label: 'hist',
              data: null,
              borderColor: hexToRgb(colorPalette[0], .5),
              backgroundColor: hexToRgb(colorPalette[0], .5),
              yAxisID: 'y',
            }, {
              type: 'line',
              label: 'kde',
              data: null,
              borderColor: hexToRgb(colorPalette[0], 1),
              pointRadius: 0,
              yAxisID: 'y1',
            }, {
              type: 'scatter',
              label: 'valMarker',
              data: null,
              borderColor: hexToRgb(colorPalette[1], 1),
              backgroundColor: hexToRgb(colorPalette[1], 1),
              pointRadius: 7,
              pointStyle: 'circle',
              yAxisID: 'y',
            }, {
              type: 'scatter',
              label: 'avgMarker',
              data: null,
              borderColor: hexToRgb(colorPalette[0], 1),
              backgroundColor: hexToRgb(colorPalette[0], 1),
              pointRadius: 7,
              pointStyle: 'circle',
              yAxisID: 'y',
            },{
              type: 'scatter',
              label: 'q1Marker',
              data: null,
              borderColor: hexToRgb(colorPalette[0], 1),
              backgroundColor: hexToRgb(colorPalette[2], 1),
              pointRadius: 7,
              pointStyle: 'rect',
              yAxisID: 'y',
            }, {
              type: 'scatter',
              label: 'q2Marker',
              data: null,
              borderColor: hexToRgb(colorPalette[0], 1),
              backgroundColor: hexToRgb(colorPalette[0], .5),
              pointRadius: 7,
              pointStyle: 'rect',
              yAxisID: 'y',
            }, {
              type: 'scatter',
              label: 'q3Marker',
              data: null,
              borderColor: hexToRgb(colorPalette[0], 1),
              backgroundColor: hexToRgb(colorPalette[3], 1),
              pointRadius: 7,
              pointStyle: 'rect',
              yAxisID: 'y'
            }
         ],
       },
       options: {
         scales: {
           y: {
             type: 'linear',
             display: true,
             position: 'left',
             title: {
               text: '빈도',
               display: true,
             },
           },
           y1: {
             type: 'linear',
             display: true,
             position: 'right',
             title: {
               text: '확률밀도',
               display: true,
             },
             grid: {
               drawOnChartArea: false,
             },
           },
           x: {
             type: 'linear',
           }
         },
         plugins: {
           labels: {
             filter: function(item, data) {
               return !item.text.includes('Path')
             }
           },
         },
       }
     };
     this.chart = new Chart(
       document.getElementById(chartId),
       config
     );

   }

   update(data) {
     // update x
     this.chart.data.labels = data.bins;

     // update histogram
     this.chart.data.datasets.find(
       ds =>
       ds.label === 'hist'
     ).data = data.counts;
     // hist.data = d.counts;

     // update kde
     this.chart.data.datasets.find(
       ds =>
       ds.label === 'kde'
     ).data = data.kde;

     // update value marker
     this.chart.data.datasets.find(
       ds =>
       ds.label === 'valMarker'
     ).data = [{x:data.val, y:0}];

     // update avg marker
     this.chart.data.datasets.find(
       ds =>
       ds.label === 'avgMarker'
     ).data = [{x:data.avg, y:0}];

     this.chart.data.datasets.find(
       ds =>
       ds.label === 'q1Marker'
     ).data = [{x:data.q1, y:0}];

     this.chart.data.datasets.find(
       ds =>
       ds.label === 'q2Marker'
     ).data = [{x:data.q2, y:0}];

     this.chart.data.datasets.find(
       ds =>
       ds.label === 'q3Marker'
     ).data = [{x:data.q3, y:0}];

     this.chart.update();
   }

   showLegend() {
     this.chart.options.plugins.legend.display = true;
   }

   hideLegend() {
     this.chart.options.plugins.legend.display = false;
   }

   convertLegend(data) {
     this.chart.options.plugins.legend.labels.generateLabels = function(chart) {
       let labels = Chart.defaults.plugins.legend.labels.generateLabels(chart);
       for (let lab of labels) {
         lab.text = data[lab.text]
       }
       return labels
     }
   }
};

class ArPanel {
  constructor(stockCode, ar, ws, tsChartId, distChartId, controlId) {
    this.stockCode = stockCode;
    this.ar = ar;
    this.ws = ws;
    let colorPalette = getColorPalette();
    this.tsChart = new ArTsChart(tsChartId, colorPalette);
    this.distChart = new ArDistChart(distChartId, colorPalette);
    this.control = document.getElementById(controlId);
    this.ts = null;
    this.csExists = null;
    this.dist = [];
  }

  // ts methods
  sendTsInputs() {
    let _this = this;
    return new Promise(function(resolve) {
      _this.ws.send(JSON.stringify({
        type: 'ts',
        data: {
          stockCode: _this.stockCode,
          ar: _this.ar,
        }
      }));
      resolve();
    });
  }
  receiveTsData() {
    let _this = this;
    return new Promise(function(resolve, reject) {
      _this.ws.onmessage = function(e) {
        let data = JSON.parse(e.data);
        if (data === null) {
          reject();
        } else {
          let ts = data.ts;
          ts.t = JSON.parse(ts.t);
          ts.val = JSON.parse(ts.val);
          _this.ts = ts;
          _this.csExists = data.cs_exists;
          resolve();
        }
      }
    });
  }
  getTsData() {
    let _this = this;
    return new Promise(function(resolve, reject) {
      _this.sendTsInputs()
        .then(() => _this.receiveTsData())
        .then(() => resolve())
        .catch(function() {
          reject();
        });
    })
  }
  addMarkersOnTs() {
    let markers = this.distChart.chart.data.datasets.filter(
      x =>
      x.label.includes('Marker')
    );
    this.tsChart.chart.data.datasets =
      this.tsChart.chart.data.datasets.concat(markers);

    for (let m of markers) {
      this.tsChart.chart.data.datasets.push(m);
      let p = {...m};
      p.type = 'line';
      p.label = m.label.replace('Marker', 'Path');
      p.data = [];
      p.pointStyle = m.pointStyle;
      p.borderColor = 'rgba(0,0,0,0.1)';
      p.backgroundColor = m.backgroundColor;
      p.pointRadius = 3;
      this.tsChart.chart.data.datasets.push(p);
    };
  }
  resetTsChart() {
    this.tsChart.clear();
    this.tsChart.update(this.ts);
    if (this.csExists) {
      this.addMarkersOnTs();
    };
  }

  // control methods
  resetControl() {
    let reverseT = this.ts.t.slice().reverse();
    let reverseVal = this.ts.val.slice().reverse();
    $(this.control).find('tbody tr').remove();
    for (let [i, t] of reverseT.entries()) {
      let color = (i === 0) ? 'table-active': '';
      let val = (reverseVal[i] === null) ? '-': reverseVal[i].toFixed(4);
      let controlText = (!this.csExists) ? '익일 조회 가능':(
        (val === '-') ? '-': '조회하기'
      );
      let row = $(`
        <tr class="${color}" tp="${t}" role="button">
          <td>${dateFormatter(t)}</td>
          <td class="fw-bold">${val}</td>
          <td class="text-center text-muted result-cell" colspan="3">${controlText}</td>
        </tr>
      `);
      let _this = this;
      if (val !== '-') {
        row.click(function(e) {
          $(_this.control).find('tbody tr').removeClass('table-active');
          row.addClass('table-active');
          if (_this.csExists) {
            _this.updateDist(e);
          }
        });
      }
      $(this.control).find('tbody').append(row);
    };
  }

  // dist methods
  updateDist(e) {
    this.getDistData(e)
      .then(data => {
        this.updateControl(data);
        this.updateDistChart(data);
    });
  }
  getDistData(e) {
    let _this = this;
    return new Promise(function(resolve) {
      let row = $(e.target).closest('tr');
      let tp = row.attr('tp');
      let data = _this.dist.find(x => x.tp === parseInt(tp));
      if (data === undefined) {
        row.find('.result-cell').html(`
          <div class="d-flex justify-content-center align-items-center">
            <span class="text-muted">분포정보 생성 중</span>
            <div class="spinner-grow spinner-grow-sm text-success mx-3" role="status"></div>
          </div>
        `);
        _this.sendDistInputs(e)
          .then(() => _this.receiveDistData())
          .then(data => resolve(data));
      } else {
        resolve(data);
      };
    });
  }
  sendDistInputs(e) {
      let _this = this;
      return new Promise(function(resolve) {
        let tp = Number($(e.target).closest('tr').attr('tp'));
        _this.ws.send(JSON.stringify({
          type: 'dist',
          data: {
            stockCode: _this.stockCode,
            ar: _this.ar,
            tp: tp,
          }
        }));
        resolve();
      });
    }
  receiveDistData() {
      let _this = this;
      return new Promise(function(resolve) {
        _this.ws.onmessage = function(e) {
          let data = JSON.parse(e.data);
          _this.dist.push(data);
          resolve(data);
        };
      });
    }
  updateControl(data) {
    let rank = (data.rank === null) ? '-':data.rank;
    let pct = (data.pct === null) ? '-':`${(data.pct*100).toFixed(2)}%`;
    let evalLk = (data.eval === null) ? '-': (
      (data.eval === 'highest') ? '매우 높음': (
        (data.eval === 'higher') ? '높음': (
          (data.eval === 'high') ? '다소 높음': (
            (data.eval === 'mid') ? '중간 수준': (
              (data.eval === 'low') ? '다소 낮음': (
                (data.eval === 'lower') ? '낮음': '매우 낮음'
              )
            )
          )
        )
      )
    );
    let redEvals = ['highest', 'higher'];
    let blueEvals = ['lowest', 'lower'];
    let txtColor = (redEvals.includes(data.eval)) ? 'danger': (
      (blueEvals.includes(data.eval) ? 'primary': 'dark')
    );

    // $(this.control).find('tbody tr').removeClass('table-active');
    let row = $(this.control).find(`[tp='${data.tp}']`);
    // row.addClass('table-active');
    row.find('.result-cell').remove();
    row.append(`
      <td class="result-cell result-cell-rank">${rank}</td>
      <td class="result-cell result-cell-pct">${pct}</td>
      <td class="result-cell result-cell-eval text-${txtColor}">${evalLk}</td>
    `);
  }
  updateDistChart(data) {
    this.distChart.update(data);
    this.updateTsMarker('val', data.tp, data.val);
    this.updateTsMarker('avg', data.tp, data.avg);
    this.updateTsMarker('q1', data.tp, data.q1);
    this.updateTsMarker('q2', data.tp, data.q2);
    this.updateTsMarker('q3', data.tp, data.q3);
    this.tsChart.chart.update();
  }
  updateTsMarker(prefix, tp, value) {
    let m = this.tsChart.chart.data.datasets.find(
      ds =>
      ds.label === `${prefix}Marker`
    );
    m.data = [{
      x: dateFormatter(tp),
      y: value
    }];

    let p = this.tsChart.chart.data.datasets.find(
      ds =>
      ds.label === `${prefix}Path`
    );
    let pos = this.tsChart.chart.data.labels.indexOf(dateFormatter(tp));
    let isNewPoint = p[pos] === undefined;
    if (isNewPoint) {
      p.data[pos] = value;
    }
  }
}
