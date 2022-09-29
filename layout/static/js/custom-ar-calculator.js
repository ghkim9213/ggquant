class CustomArCalculator {
  constructor(
      texWrapperId,
      formWrapperId,
      subWrapperId,
      ws,
      stockCode,
      itemAll,
      legendMap,
  ) {
    this.texWrapper = $(`#${texWrapperId}`);
    this.main = $(`#${formWrapperId}`);
    this.sub = $(`#${subWrapperId}`);
    this.ws = ws;
    this.stockCode = stockCode;
    this.valid = {
      nm: true,
      lk: true,
      abbrev: true,
      operation: false,
    };
    this.regex = {
      char: /[`~!@#$%^&*()_|+\-=?;:'",.<>\{\}\[\]\\\/]/,
      nm: /^[(a-zA-Z\s)|(a-zA-Z\s)(0-9\s)]*[(a-zA-Z\s)|(0-9\s)]$/,
      lk: /^[(가-힣\s)|(가-힣\s)(0-9\s)]*[(가-힣\s)|(0-9\s)]$/,
      abbrev: /^[A-Z]*$/,
    };
    this.itemAll = itemAll;
    this.itemLetterOrder = [
      'x', 'y', 'z', 'w',
      'v', 'u', 't', 's',
      'r', 'q', 'p', 'n',
      'm', 'k', 'j', 'i',
    ];
    this.dataSelected = null;

    this.carPanel = null;
    this.legendMap = legendMap;
  }

  activate() {
    this.createForm();
    this.createTex();
    this.activateValidation();
    this.activateItemSearchBtn();
  }

  createForm() {
    // div
    let divFormWrapper = this.getFormWrapper('carDiv', '구분');
    let divForm = $(`
      <select class="form-select" name="carDiv" id="carDiv">
        <option value="안정성">안정성</option>
        <option value="수익성" selected>수익성</option>
        <option value="성장성">성장성</option>
        <option value="활동성">활동성</option>
        <option value="생산성">생산성</option>
        <option value="기타">기타</option>
      </select>
    `);
    divFormWrapper.append(divForm);
    this.carDiv = divForm;
    this.main.append(divFormWrapper);

    // lk
    let lkFormWrapper = this.getFormWrapper('carLk', '재무비율명 (한글)');
    let lkForm = $(`
      <input type="text" class="form-control" name="carLk" id="carLk">
    `);
    let lkHelpText = $(`
      <div class="form-text">한글로 시작하는 한글 및 숫자의 조합</div>
    `);
    lkFormWrapper.append(lkForm);
    this.lk = lkForm;
    lkFormWrapper.append(lkHelpText);
    this.main.append(lkFormWrapper);

    let nmabbrevWrapper = $(`
      <div class="d-flex flex-row"></div>
    `);

    let nmFormWrapper = this.getFormWrapper('carNm', '재무비율명 (영문)');
    let nmForm = $(`
      <input type="text" class="form-control" name="carNm" id="carNm">
    `);
    let nmHelpText = $(`
      <div class="form-text">알파벳으로 시작하는 알파벳 및 숫자의 조합</div>
    `);
    nmFormWrapper.append(nmForm);
    nmFormWrapper.addClass('col-9 me-1');
    this.nm = nmForm;
    nmFormWrapper.append(nmHelpText);
    nmabbrevWrapper.append(nmFormWrapper);
    // this.main.append(nmFormWrapper);

    let abbrevFormWrapper = this.getFormWrapper('carAbbrev', '약어 (영문대문자)');
    let abbrevForm = $(`
      <input type="text" class="form-control" name="carAbbrev" id="carAbbrev">
    `);
    let abbrevHelpText = $(`
      <div class="form-text">알파벳 대문자</div>
    `);
    abbrevFormWrapper.append(abbrevForm);
    this.abbrev = abbrevForm;
    abbrevFormWrapper.append(abbrevHelpText);
    abbrevFormWrapper.addClass('col-3 me-1');
    nmabbrevWrapper.append(abbrevFormWrapper);

    this.main.append(nmabbrevWrapper);

    let itemsFormWrapper = this.getFormWrapper('carItems', '계정 선택');
    let itemsForm = $(`
      <div class="table-responsive" style="max-height: 20vh;">
      <table class="table table-hover overflow-auto" id="carItems" style="table-layout: fixed;">
        <thead>
          <tr>
            <th scope="col" style="width: 10%"></th>
            <th scope="col" style="width: 10%">id</th>
            <th scope="col" style="width: 10%">구분</th>
            <th scope="col" style="width: 40%">계정명</th>
            <th scope="col" style="width: 30%">상태</th>
          </tr>
        </thead>
        <tbody></tbody>
        <tfoot>
        </tfoot>
      </table>
      </div>
    `);
    let itemSearchBar = $(`
      <tr class="item-search-bar">
        <th>
          <button class="btn btn-outline-primary">
            <i class="bi bi-plus-lg"></i>
          </button>
        </th>
        <td>-</td>
        <td>-</td>
        <td>-</td>
        <td>-</td>
      </tr>
    `);
    // this.itemSearchBar = itemSearchBar;
    itemsForm.find('tfoot').append(itemSearchBar);

    itemsFormWrapper.append(itemsForm);
    this.items = itemsForm;
    this.main.append(itemsFormWrapper);

    let operFormWrapper = this.getFormWrapper('carOper', '연산 정의');
    let operators = $(`
      <div class="btn-group mx-auto float-end mb-3" role="group">
        <button class="btn btn-outline-secondary btn-operator" value="+"><i class="bi bi-plus-lg"></i></button>
        <button class="btn btn-outline-secondary btn-operator" value="-"><i class="bi bi-dash-lg"></i></button>
        <button class="btn btn-outline-secondary btn-operator" value="*"><i class="bi bi-x-lg"></i></button>
        <button class="btn btn-outline-secondary btn-operator" value="/"><i class="bi bi-slash-lg"></i></button>
        <button class="btn btn-outline-secondary btn-operator" value="()">()</button>
      </div>
    `);
    let _this = this;
    operators.find('.btn-operator').click(function() {
      let operator = $(this).attr('value');
      _this.addToOperation(operator);
    });
    let changeInForm = $(`
      <input type="checkbox" class="btn-check" id="carChangeIn" autocomplete="off">
    `);
    let changeInFormLabel = $(`
      <label class="btn btn-outline-primary" for="carChangeIn">변동율</label>
    `);
    operators.find('.btn-group').append(changeInForm);
    operators.find('.btn-group').append(changeInFormLabel);
    this.changeIn = changeInForm;
    let operForm = $(`
      <textarea name="carOper" id="carOper" cols="30" rows="4" class="form-control"></textarea>
    `);
    let operHelpText = $(`
      <div class="form-text" id="carOperHelp"></div>
    `);
    operFormWrapper.append(operators);
    operFormWrapper.append(operForm);
    operFormWrapper.append(operHelpText);
    operFormWrapper.removeClass('mb-3');
    this.main.append(operFormWrapper);
    this.operation = operForm;

    let submitBtn = $(`
      <button class="btn btn-primary float-end" disabled>입력값 검사</button>
    `);
    submitBtn.click(function() {
      _this.checkCar();
    });
    this.submitBtn = submitBtn;
    this.main.append(submitBtn);
  }
  getFormWrapper(id, label) {
    return $(`
      <div class="mb-3">
        <label for="${id}" class="form-label">${label}</label>
      </div>
    `);
  }

  activateValidation() {
    let _this = this;
    _this.nm.keyup(function() {
      let nm = $(this).val();
      _this.validate('nm', nm);
      _this.updateSubmitBtn();
    });
    _this.lk.keyup(function() {
      let lk = $(this).val();
      _this.validate('lk', lk);
      _this.updateSubmitBtn();
    });
    _this.abbrev.keyup(function() {
      let abbrev = $(this).val();
      _this.validate('abbrev', abbrev);
      _this.updateSubmitBtn();
    });
    _this.operation.keyup(function() {
      let oper = $(this).val();
      let operV = _this.validate('operation', oper);
      let operHelpText = _this.main.find('#carOperHelp');
      if (operV.isValid) {
        operHelpText.html('연산이 올바르게 정의되었습니다.')
          .removeClass('text-danger')
          .addClass('text-success');
        let tex = _this.getTex();
        _this.displayTex(tex);
      } else {
        operHelpText.html(operV.msg)
          .removeClass('text-success')
          .addClass('text-danger');
        _this.displayTex('');
      };
      _this.updateSubmitBtn();
    });
  }
  validate(key, value) {
    let msg;
    let isValid = this.isValid(key, value);
    if (key === 'operation') {
      msg = isValid.msg;
      isValid = isValid.valid;
    };
    if (isValid) {
      this.valid[key] = true;
      this[key].addClass('border');
      this[key].removeClass('border-danger');
    } else if (value === '') {
      this.valid[key] = false;
      this[key].removeClass('border');
      this[key].removeClass('border-danger');
    } else {
      this.valid[key] = false;
      this[key].addClass('border');
      this[key].addClass('border-danger');
    };
    return {msg: msg, isValid: isValid}
  }
  isValid(key, value) {
    if (key === 'nm') {
      return this.regex.nm.test(value) && !this.regex.char.test(value) || value == '';
    } else if (key === 'lk') {
      return this.regex.lk.test(value) && !this.regex.char.test(value) || value == '';
    } else if (key === 'abbrev') {
      return this.regex.abbrev.test(value) && !this.regex.char.test(value) || value == '';
    } else if (key === 'operation') {
      let letterAll = this.getItemAry().map(item => item.letter);
      let operatorAll = ['+', '-', '*', '/'];
      function isLetter(char) {
        return letterAll.includes(char);
      };
      function isInteger(char) {
        let regexInt = /[0-9]/
        return regexInt.test(char)
      };
      function isOperator(char) {
        return operatorAll.includes(char);
      };
      function pOpen(char) {
        return char === '('
      };
      function pClose(char) {
        return char === ')'
      };
      function isNotAvailableChar(char) {
        return !isInteger(char) && !isLetter(char) && !isOperator(char) && !pOpen(char) && !pClose(char)
      };
      let msg;
      let prev;
      let pOpened = [];
      let charAll = value.replaceAll(' ','').split('');
      if (charAll.length === 0) {
        msg = '수식을 입력하세요.';
        return {msg: msg, valid: false}
      } else {
        charAll.push(';');
      };
      if (isOperator(charAll[0])) {
        msg = `연산 대상이 올바르게 정의되지 않았습니다: '${charAll[0]}'.`;
        return {msg: msg, valid: false}
      };
      for (let char of charAll) {
        // at-char validation
        if (char === ';') {
          if (isOperator(prev)) {
            msg = `연산 대상이 올바르게 정의되지 않았습니다: '${prev}'.`;
            return {msg: msg, valid: false}
          };
          break
        }
        if (isNotAvailableChar(char)) {
          msg = `사용할 수 없는 문자가 포함되었습니다: '${char}'.`;
          return {msg: msg, valid: false}

        // frontward validation
        } else if (pOpen(char)) {
          if (isInteger(prev)) {
            msg = `계정과 정수 사이의 연산이 정의되지 않았습니다: '${prev}${char}'.`;
            return {msg: msg, valid: false}
          };
          if (isLetter(prev)) {
            msg = `계정 사이의 연산이 정의되지 않았습니다: '${prev}${char}'.`;
            return {msg: msg, valid: false}
          };
          pOpened.push(true);
        } else if (pClose(char)) {
          if (isOperator(prev)) {
            msg = `연산 대상이 올바르게 정의되지 않았습니다: '${prev}${char}'.`;
            return {msg: msg, valid: false}
          };
          pOpened.pop();
        } else if (isInteger(char)) {
          if (pClose(prev) || isLetter(prev)) {
            msg = `계정과 정수 사이의 연산이 정의되지 않았습니다: '${prev}${char}'.`
            return {msg: msg, valid: false}
          };
        } else if (isLetter(char)) {
          if (pClose(prev) || isLetter(prev)) {
            msg = `계정 간 연산이 정의되지 않았습니다: '${prev}${char}'.`;
            return {msg: msg, valid: false}
          };
          if (isInteger(prev)) {
            msg = `정수와 계정 사이의 연산이 정의되지 않았습니다: '${prev}${char}'`;
            return {msg:msg, valid: false}
          }
        } else if (isOperator(char)) {
          if (pOpen(char) || isOperator(prev)) {
            msg = `연산 대상이 올바르게 정의되지 않았습니다: '${prev}${char}'.`;
            return {msg: msg, valid: false}
          };
        } else if (isOperator(prev)) {
          if (!isLetter(char)) {
            msg = `연산 대상이 올바르게 정의되지 않았습니다: '${prev}${char}'.`;
            return {msg:msg, valid: false}
          };
        };
        prev = char;
      };
      if (pOpened.length > 0) {
        msg = '괄호가 올바르게 닫히지 않았습니다.';
        return {msg: msg, valid: false}
      };
      return {msg: null, valid: true}
    }
  }
  updateSubmitBtn() {
    if (this.isValidAll()) {
      this.submitBtn.attr('disabled', false);
    } else {
      this.submitBtn.attr('disabled', true);
    };
  }
  isValidAll() {
    let validItems = this.items.find('text-danger').length === 0;
    let validOthers = !Object.values(this.valid).includes(false);
    return validItems && validOthers
  }

  activateItemSearchBtn() {
    let btn = this.items.find('.item-search-bar .btn');
    let _this = this;
    btn.click(function() {
      _this.itemSearch();
    });
  }
  itemSearch() {
    let _this = this;
    new Promise(function(resolve) {
      _this.createItemSearchBar();
      _this.createItemSearchContainer();
      resolve();
    }).then(() => _this.itemSearchFilter());
  }
  createItemSearchBar() {
    let sr = `
      <td colspan="4">
        <div class="d-flex flex-row">
          <div class="col-2 mx-1">
            <select class="form-select item-oc">
              <option value="CFS" selected>연결</option>
              <option value="OFS">별도</option>
            </select>
          </div>
          <div class="col-10 mx-1">
            <div class="input-group">
              <span class="input-group-text"><i class="bi bi-search"></i></span>
              <input class="form-control item-lk" type="text" placeholder="당기순이익(손실)">
            </div>
          </div>
        </div>
      </td>
    `;
    let bar = this.items.find('.item-search-bar');
    bar.find('td').remove();
    bar.append(sr);
  }
  createItemSearchContainer() {
    let container = $('<div class="result-container result-container-search overflow-auto"></div>');
    let bar = this.items.find('.item-search-bar');
    let closeBtn = $(`
      <button class="btn btn-close m-3 sticky-top float-end"></button>
    `);
    let _this = this;
    closeBtn.click(function() {
      container.remove();
      container.css('display', 'none');
      bar.find('td').remove();
      bar.append('<td>-</td><td>-</td><td>-</td><td>-</td>');
    });
    container.append(closeBtn);

    let sp = $(`
    <p class="form-text m-3">해당 기업이 보고하지 않은 계정 혹은 K-IFRS 표준에 맞게 보고하지 않은 계정은 검색되지 않습니다.</p>
    <div class="d-flex flex-row">
      <p class="form-text m-3 fw-bold">검색된 계정</p>
      <div class="item-matched m-3">
        <span class="form-text m-3">계정명을 입력하세요</span>
      </div>
    </div>
    <div>
      <p class="form-text m-3 fw-bold">검색 가능 계정 목록</p>
      <div class="item-filtered item-filtered-bs m-3">
        <p class="form-text">재무상태표</p>
      </div>
      <div class="item-filtered item-filtered-pl m-3">
        <p class="form-text">손익계산서</p>
      </div>
      <div class="item-filtered item-filtered-cf m-3">
        <p class="form-text">현금흐름표</p>
      </div>
    </div>
    `);
    container.append(sp);

    this.sub.append(container);
    this.sub.find('.result-container').css('display', 'none');
    container.css('display', 'block');
  }
  itemSearchFilter() {
    let container = this.sub.find('.result-container-search');
    let bar = this.items.find('.item-search-bar');
    let _this = this;
    bar.find('.item-oc').change(function() {
      let oc = $(this).val();
      bar.find('.item-lk').keyup(function() {
        let lk = $(this).val();
        container.find('.item-filtered span').remove();
        let fltrd = _this.itemAll.filter(
          item =>
          (item.oc == oc)
          && (item.lk.includes(lk))
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
              <td>-</td><td>-</td><td>-</td><td>-</td>
            `);
            _this.checkItem(e);
          });
          container.find(`.item-filtered-${ftDiv}`).append(badge);
        };

        let matched = container.find('.item-matched');
        matched.find('span').remove();
        let m = _this.itemAll.find(
          item =>
          (item.oc == oc)
          && (item.lk == lk)
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
              <td>-</td><td>-</td><td>-</td><td>-</td>
            `);
            _this.checkItem(e);
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

  checkItem(e) {
    this.sendItemInputs(e)
      .then(() => this.receiveItemResult())
      .then(data => this.updateItem(data))
    }
  sendItemInputs(e) {
    let _this = this;
    let oc = $(e.target).attr('oc');
    let nm = $(e.target).attr('nm');
    return new Promise(function(resolve) {
      _this.ws.send(JSON.stringify({
        type: 'checkItem',
        data: {
          stockCode: _this.stockCode,
          oc: oc,
          nm: nm
        }
      }));
      resolve();
    });
  }
  receiveItemResult() {
    let _this = this;
    return new Promise(function(resolve) {
      _this.ws.onmessage = function(e) {
        resolve(JSON.parse(e.data));
      };
    });
  }
  updateItem(data) {
    let letter = this.itemLetterOrder.shift();
    let status = data.status.ts && data.status.cs;
    let statusLk = (status) ? '조회 가능':'조회 불가';
    let statusColor = (status) ? 'text-success':'text-danger';
    let row = $(`
      <tr class="item" role="button">
        <th><button class="btn btn-close"></button></th>
        <td class="item-content item-letter">${letter}</td>
        <td class="item-content item-oc">${(data.item.oc === 'CFS') ? '연결':'별도'}</td>
        <td class="item-content item-lk">${data.item.lk}</td>
        <td class="item-content item-status ${statusColor}">${statusLk}</td>
        <input type="hidden" name="itemNm" value="${data.item.nm}">
        <input type="hidden" name="itemOc" value="${data.item.oc}">
      </tr>
    `);
    let _this = this;
    row.find('.btn-close').click(function(e) {
      let _row = $(e.target).closest('tr');
      let _letter = _row.find('.item-letter').html();
      _this.itemLetterOrder.unshift(_letter);
      _row.remove();
    });
    row.find('.item-content').click(function(e) {
      let _row = $(e.target).closest('tr');
      let _letter = _row.find('.item-letter').html();
      _this.addToOperation(_letter);
    });
    this.items.find('tbody').append(row);
  }

  disableForm() {
    this.main.find('input').attr('disabled', true);
    this.main.find('select').attr('disabled', true);
    this.main.find('textarea').attr('disabled', true);
    this.main.find('button').attr('disabled', true);
    this.main.find('.item-content').off('click');
  }
  enableForm() {
    this.main.find('input').attr('disabled', false);
    this.main.find('select').attr('disabled', false);
    this.main.find('textarea').attr('disabled', false)
    this.main.find('button').attr('disabled', false);
    let _this = this;
    this.main.find('.item-content').click(function(e) {
      let _row = $(e.target).closest('tr');
      let _letter = _row.find('.item-letter').html();
      _this.addToOperation(_letter);
    });
  }

  createTex() {
    let tex = $(`
      <p class="position-absolute top-50 start-50 translate-middle display-tex"></p>
    `);
    this.texWrapper.append(tex);
  }
  displayTex(tex) {
    let el = this.texWrapper.find('.display-tex')[0];
    katex.render(tex, el, {displayMode: true});
  }
  getTex() {
    let texLk = `\\text{${this.lk.val()}}`;
    let texBody = this.getTexBody();
    let items = this.getItemAry();
    for (let item of items) {
      texBody = texBody.replaceAll(item.letter, `\\text{${item.lk}}`);
      texBody = texBody.replaceAll(`\\te\\text{${item.lk}}t`, '\\text');
    }
    return texLk + '=' + texBody
  }
  getTexBody(){
    let oper = this.operation.val();
    if ((oper !== null) && (oper !== '')) {
      var pos = -1, ch;
      function nextChar(){
        ch = (++pos < oper.length) ? oper.charAt(pos) : -1;
      }
      function eat(charToEat) {
        while (ch == ' ') nextChar();
        if (ch == charToEat) {
          nextChar();
          return true;
        }
        return false;
      }
      function parse(){
        nextChar();
        var x = parseExpression();
        if (pos < oper.length) throw `Unexpected: ${ch}`
        return x;
      }
      function parseExpression() {
        var x = parseTerm();
        for (;;) {
          if      (eat('+')) x = `${x} + ${parseTerm()}` // addition
          else if (eat('-')) x = `${x} - ${parseTerm()}` // subtraction
          else return x;
        }
      }
      function parseTerm() {
        var x = parseFactor();
        for (;;) {
          if      (eat('*')) x=`${x} \\times ${parseTerm()}`; // multiplication
          else if (eat('/')) x= `\\frac{${x}}{${parseTerm()}}`; // division
          else return x;
        }
      }
      function parseFactor() {
        if (eat('+')) return `${parseFactor()}`; // unary plus
        if (eat('-')) return `-${parseFactor()}`; // unary minus

        var x;
        var startPos = pos;
        if (eat('(')) { // parentheses
          x = `{(${parseExpression()})}`
          eat(')');
        } else if ((ch >= '0' && ch <= '9') || ch == '.') { // numbers
          while ((ch >= '0' && ch <= '9') || ch == '.') nextChar();
          x = oper.substring(startPos, pos);
        } else if (ch >= 'a' && ch <= 'z') { // variables
          while (ch >= 'a' && ch <= 'z') nextChar();
          x = oper.substring(startPos, pos);
          if(x.length>1){
            x = `\\${x} {${parseFactor()}}`;
          }
        } else {
          throw `Unexpected: ${ch}`;
        }
        if (eat('^')) x = `${x} ^ {${parseFactor()}}` //superscript
        if(eat('_')) x = `${x}_{${parseFactor()}}`;

        return x;
      }
      return `${parse()}`;
    } else {
      return '';
    }
  }


  // operation
  addToOperation(val) {
    let syntax = this.operation.val();

    let txtArea = this.operation[0];
    let scrollPos = txtArea.scrollTop;
    let caretPos = txtArea.selectionStart;

    let syntaxFront = syntax.substring(0, caretPos);
    let syntaxBack = syntax.substring(txtArea.selectionEnd, syntax.length);
    this.operation.val(syntaxFront + val + syntaxBack);
    caretPos = caretPos + val.length;
    if (val === '()') {
      caretPos = caretPos - 1
    };
    txtArea.selectionStart = caretPos;
    txtArea.selectionEnd = caretPos;
    this.operation.focus();
    txtArea.scrollTop = scrollPos;
    this.operation.keyup();
  }

  // check car
  checkCar() {
    this.showLoader();
    this.disableForm();
    this.createCheckCarResultContainer();
    this.sendCheckCarInputs()
      .then(() => this.receiveCheckCarResult())
      .then(data => this.updateCheckCarResultContainer(data))
      .then(container => {
        container.css('display', 'block');
        this.hideLoader();
      });
  }
  showLoader() {
    this.sub.find('.result-container').css('display', 'none');
    let loader = $(`
      <div class="result-container result-container-loader position-relative">
        <div class="position-absolute top-50 start-50 translate-middle text-center">
          <div class="spinner-grow text-muted mb-3" style="width: 3rem; height: 3rem;" role="status"></div>
          <p class="text-muted fw-bold">데이터베이스 조회 중</p>
        </div>
      </div>
    `);
    loader.css('display', 'block');
    this.sub.append(loader);
  }
  hideLoader() {
    this.sub.find('.result-container-loader').remove();
  }
  getCar() {
    return {
      stockCode: this.stockCode,
      customAr: {
        nm: this.nm.val(),
        lk: this.lk.val(),
        abbrev: this.abbrev.val(),
        carDiv: this.carDiv.val(),
        items: this.getItemAry(),
        changeIn: false,
        operation: this.operation.val(),
      }
    }
  }
  getItemAry() {
    let objAry = [];
    this.items.find('.item').each(function() {
      let obj = {};
      obj.letter = $(this).find('.item-letter').html();
      obj.nm = $(this).find('input[name="itemNm"]').val();
      obj.lk = $(this).find('.item-lk').html();
      obj.oc = $(this).find('input[name="itemOc"]').val();
      objAry.push(obj)
    });
    return objAry
  }
  sendCheckCarInputs() {
    let _this = this;
    return new Promise(function(resolve) {
      _this.ws.send(JSON.stringify({
        type: 'checkCar',
        data: _this.getCar()
      }));
      resolve();
    });
  }
  receiveCheckCarResult() {
    let _this = this;
    return new Promise(function(resolve) {
      _this.ws.onmessage = function(e) {
        resolve(JSON.parse(e.data));
      };
    });
  }
  createCheckCarResultContainer() {
    let container = $(`<div class="result-container result-container-check overflow-auto"></div>`);
    container.append(`
      <h5 class="fw-bold">입력값 검사결과</h5>
      <hr>
    `);
    container.append(`
      <div class="check-result check-result-desc mb-3">
        <p class="fw-bold">검사결과 요약</p>
        <ul></ul>
      </div>
    `);

    let matched = $(`
      <div class="check-result check-result-matched mb-3">
        <p class="fw-bold">검색된 재무비율</p>
        <table class="table"></table>
      </div>
    `);
    matched.css('display', 'none');
    container.append(matched);

    let question = $(`
      <div class="check-result check-result-question mb-3">
        <p>입력한 재무비율과 동일한가요?</p>
        <div class="form-check">
          <input class="check-result check-result-answer form-check-input" type="radio" name="useMatched" id="matchedYes" value="y" checked>
          <label class="form-check-label" for="matchedYes">
            예, 동일하며 위의 정보로 재무비율을 계산합니다.
          </label>
        </div>
        <div class="form-check">
          <input class="check-result check-result-answer form-check-input" type="radio" name="useMatched" id="matchedNo" value="n">
          <label class="form-check-label" for="matchedNo">
            아니오, 동일하지 않으며 입력값대로 재무비율을 계산합니다.
          </label>
        </div>
      </div>
    `);
    question.css('display', 'none');
    container.append(question);

    let inputAbstract = $(`
      <div class="check-result check-result-input mb-3">
        <p class="fw-bold">입력값 요약</p>
        <table class="table"></table>
      </div>
    `);
    inputAbstract.css('display', 'none');
    container.append(inputAbstract);

    let caution = $(`
      <div class="check-result check-result-caution">
        <p class="fw-bold">주의사항</p>
        <ul>
          <li>계산 실행시 해당 재무비율이 데이터베이스에 자동으로 등록되며, 다른 유저 또한 결과를 검색 및 조회할 수 있습니다.</li>
          <li>데이터베이스 내 동일한 연산의 재무비율이 존재함에도 재무비율명, 약어, 구분 등 식별정보만을 변경하여 새롭게 등록되는 경우, 데이터베이스의 원활한 관리를 위해 등록 취소될 수 있습니다.</li>
          <li>일반적으로 알려진 재무비율이 새롭게 등록되는 경우, 결과 공유 및 관리의 용이성을 위해 입력사항이 변경될 수 있습니다.</li>
        </ul>
        <div class="form-check">
          <input class="form-check-input check-result-agree" type="checkbox">
          <label class="form-check-label" for="cautionAgree">
            주의사항을 확인했습니다.
          </label>
        </div>
      </div>
    `);
    caution.css('display', 'none');
    container.append(caution);

    let btns = $(`
      <div class="btn-group mx-auto float-end mb-3" role="group">
        <button class="btn btn-outline-primary btn-fix">수정하기</button>
        <button class="btn btn-primary btn-submit">계산하기</button>
      </div>
    `);
    let _this = this;
    btns.find('.btn-fix').click(function() {
      _this.enableForm();
      container.remove();
    });
    btns.find('.btn-submit').click(function() {
      _this.caculate();
    });
    container.append(btns);

    container.css('display', 'none');
    this.sub.append(container);
  }
  updateCheckCarResultContainer(data) {
    let _this = this;
    return new Promise(function(resolve) {
      let container = _this.sub.find('.result-container-check');

      let desc = container.find('.check-result-desc ul');
      let inputAbstract = container.find('.check-result-input');
      let inputAbstractTable = _this.createCheckCarResultTable(data.inputs);
      inputAbstract.find('table').append(inputAbstractTable);

      let matched = container.find('.check-result-matched');
      let question = container.find('.check-result-question');
      let caution = container.find('.check-result-caution');
      let queryBtn = container.find('.btn-submit');

      if (data.matched) {
        _this.dataSelected = data.matched;
        let descMatched = $(`
          <li>입력값과 동일한 것으로 추정되는 재무비율이 검색되었습니다.</li>
          <li><span class="text-success">즉시 조회 가능한 시계열정보가 확인되었습니다.</span></li>
        `);
        desc.append(descMatched);
        let matchedTable = _this.createCheckCarResultTable(data.matched);
        matched.find('table').append(matchedTable);
        matched.css('display', 'block');
        question.css('display', 'block');
        inputAbstract.css('display', 'none');
        caution.css('display', 'none');
        queryBtn.attr('disabled', false);
      } else {
        _this.dataSelected = data.inputs;
        let descMatched = $(`
          <li>입력값과 동일한 재무비율이 데이터베이스에 존재하지 않습니다.</li>
          <li><span class="text-success">즉시 조회 가능한 시계열정보가 확인되었습니다.</span></li>
        `);
        desc.append(descMatched);
        matched.css('display', 'none');
        question.css('display', 'none');
        inputAbstract.css('display', 'block');
        caution.css('display', 'block');
        queryBtn.attr('disabled', true);
      };
      if (data.non_batched_items.length > 0) {
        let n = data.non_batched_items.length;
        let itemLkAll = data.non_batched_items.map(
          item =>
          `(${(item.oc === 'CFS') ? '연결':'별도'}) ${item.lk}`
        ).join(', ');
        let descNonBatched = $(`
          <li>
            <span class="text-danger">분포정보를 확인할 수 없습니다.</span>
            <ul>
              <li>다음 ${n}개 계정의 분포정보가 데이터베이스에 등록되지 않았습니다: ${itemLkAll}.</li>
              <li>계산 실행시 해당 계정의 분포정보 등록이 자동요청되며 <span class="fw-bold">익일 오전 7시</span>부터 결과를 확인할 수 있습니다.</li>
              <li>마찬가지로 본 재무비율의 분포정보 또한 익일 오전 7시부터 확인할 수 있습니다.</li>
            </ul>
        `);
        desc.append(descNonBatched);
      } else {
        let descNonBatched = $(`
          <li><span class="text-success">즉시 조회 가능한 분포정보가 확인되었습니다.</span></li>
        `);
        desc.append(descNonBatched);
      };
      // container.find('.check-result-desc').append(desc);

      // interactions btw contents
      container.find('input[name="useMatched"]').change(function() {
        if ($(this).val() === 'y') {
          inputAbstract.css('display', 'none');
          caution.css('display', 'none');
          queryBtn.attr('disabled', false);
          _this.dataSelected = data.matched;
        } else {
          inputAbstract.css('display', 'block');
          caution.css('display', 'block');
          queryBtn.attr('disabled', true);
          _this.dataSelected = data.inputs;
        };
      });

      container.find('.check-result-agree').change(function() {
        if (this.checked) {
          queryBtn.attr('disabled', false);
        } else {
          queryBtn.attr('disabled', true);
        };
      });
      resolve(container);
    });
  }
  createCheckCarResultTable(tableData) {
    let abbrev = (tableData.abbrev == '') ? '-':tableData.abbrev;
    let tBody = $(`
      <tbody>
        <tr>
          <th>재무비율명 (한글)</th>
          <td>${tableData.lk}</td>
        </tr>
        <tr>
          <th>재무비율명 (영문) / 약어</th>
          <td>${tableData.nm} / ${abbrev}</td>
        </tr>
        <tr>
          <th>구분</th>
          <td>${tableData.carDiv}</td>
        </tr>
        <tr>
          <th>연산</th>
          <td>${tableData.operation}</td>
        </tr>
      </tbody>
    `);
    $(tableData.items).each(function(i, v) {
      let ocLk = (v.oc === 'CFS') ? '연결':'별도';
      let vDesc = `(${ocLk}) ${v.lk}`
      let row = $(`
        <tr>
          <th class="text-end">${v.letter}</th>
          <td>${vDesc}</td>
        </tr>
      `);
      tBody.append(row);
    });
    tBody.find('tr th').css('padding-right', '10px');
    return tBody
  }

  caculate() {
    this.showLoader();
    this.createResultContainer()
      .then(() => this.createCarPanel())
      .then(() => this.displayCarPanel())
      .then(() => {
        this.hideLoader();
        this.sub.find('.result-container').css('display', 'none');
        this.sub.find('.result-container-main').css('display', 'block');
      });
  }
  createResultContainer() {
    let _this = this;
    return new Promise(function(resolve) {
      let container = $('<div class="result-container result-container-main"></div>');
      let closeBtn = $(`
        <button class="btn btn-close float-end"></button>
      `);
      closeBtn.click(function() {
        container.remove();
        _this.sub.find('.result-container').remove();
        _this.enableForm();
      });
      container.append(closeBtn);

      let chartNav = $(`
        <ul class="nav nav-tabs" role="tablist">
          <li class="nav-item" role="presentation">
            <button class="nav-link active" id="carTs-tab" data-bs-toggle="tab" data-bs-target="#carTs" type="button" role="tab" aria-controls="carTs" aria-selected="true">시계열</button>
          </li>
          <li class="nav-item" role="presentation">
            <button class="nav-link" id="carDist-tab" data-bs-toggle="tab" data-bs-target="#carDist" type="button" role="tab" aria-controls="carDist" aria-selected="false">횡단면 분포</button>
          </li>
        </ul>
      `);
      container.append(chartNav);

      let chartContents = $(`<div class="tab-content"></div>`);
      let tsChart = $(`
        <div class="tab-pane fade show active" id="carTs" role="tabpanel" aria-labelledby="carTs-tab">
          <canvas id="carTsChart"></canvas>
        </div>
      `);
      chartContents.append(tsChart);
      let distChart = $(`
        <div class="tab-pane fade" id="carDist" role="tabpanel" aria-labelledby="carDist-tab">
          <canvas id="carDistChart"></canvas>
        </div>
      `);
      chartContents.append(distChart);
      container.append(chartContents);

      let chartControl = $(`
        <div class="table-responsive" style="height: 45vh;">
          <table class="table table-hover text-nowrap" id="carChartControl">
            <thead class="fix-header">
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
      container.append(chartControl);
      container.css('display', 'none');
      _this.sub.append(container);
      resolve();
    });
  }
  createCarPanel() {
    let _this = this;
    return new Promise(function(resolve) {
      _this.carPanel = new ArPanel(
        _this.stockCode,
        _this.dataSelected,
        _this.ws,
        'carTsChart',
        'carDistChart',
        'carChartControl',
      );
      _this.carPanel.tsChart.convertLegend(_this.legendMap);
      _this.carPanel.tsChart.showLegend();
      _this.carPanel.distChart.convertLegend(_this.legendMap);
      _this.carPanel.distChart.showLegend();
      resolve();
    })
  }
  displayCarPanel() {
    let _this = this;
    return new Promise(function(resolve) {
      _this.carPanel.getTsData()
        .then(() => {
          _this.carPanel.resetTsChart();
          _this.carPanel.resetControl();
          resolve();
        });
    });
  }

}
