const renderer = {
  // Override code block
  code(code, infostring) {
      // infostring이 Math일 때만 KaTex로 별도로 렌더링해 줍니다.
      if (infostring === 'Math') {
          // TeX 문법에 오류가 있어도 에러를 일으키지 않습니다.
          return katex.renderToString(code, { throwOnError: false });
      } else {
          try {
              return `<pre class = "language-${infostring}"><code class = "language-${infostring}">${Prism.highlight(
                  code,
                  Prism.languages[infostring],
                  infostring
              )}</code></pre>`;
          } catch (err) {
              return false;
          }
      }
  },
  // Override inline code
  codespan(code) {
      // 첫 캐릭터가 '$'일 때 KaTeX로 렌더링한다.
      if (code[0] === '$') {
          return katex.renderToString(code.substring(1), {
              throwOnError: false,
          });
      } else {
          // or just use original code
          return `<code class = "inline-code">${code}</code>`;
      }
  },
};

const tokenizer = {
  // $ ... $로 감싸진 블럭을 codespan으로 처리합니다.
  codespan(src) {
    const match = src.match(/^([`$])(?=[^\s\d$`])([^`$]*?)\1(?![`$])/);
    if (match) {
      return {
        type: 'codespan',
        raw: match[0],
        // codespan은 infostring이 없으니까 TeX인 경우 문자열의 제일 앞에 $를 써줍니다.
        text:
            match[1] === '$' ? `$${match[2].trim()}` : match[2].trim(),
      };
    }
    return false;
  },
  // 인라인 텍스트가 $ ... $를 만나도 멈추도록 오버라이드 합니다.
  inlineText(src, inRawBlock, smartypants) {
    const cap = src.match(
      /^([`$]+|[^`$])(?:[\s\S]*?(?:(?=[\\<!\[`$*]|\b_|$)|[^ ](?= {2,}\n))|(?= {2,}\n))/
    );
    if (cap) {
      var text;
      if (inRawBlock) {
        text = this.options.sanitize
        ? this.options.sanitizer
        ? this.options.sanitizer(cap[0])
        : cap[0]
        : cap[0];
      } else {
        text = this.options.smartypants ? smartypants(cap[0]) : cap[0];
      }
      return {
        type: 'text',
        raw: cap[0],
        text: text,
      };
    }
  },
  // $$ ... $$ 블럭을 코드블럭으로 처리하도록 오버라이드 해 줍니다.
  fences(src) {
    const cap = src.match(
      /^ {0,3}(`{3,}|\${2,}(?=[^`\n]*\n)|~{3,})([^\n]*)\n(?:|([\s\S]*?)\n)(?: {0,3}\1[~`\$]* *(?:\n+|$)|$)/
    );
    if (cap) {
      return {
        type: 'code',
        raw: cap[0],
        codeBlockStyle: 'indented',
        // $$ ... $$ 블럭일 때 lang을 Math로 설정합니다.
        lang: cap[1] === '$$' ? 'Math' : cap[2].trim(),
        text: cap[3],
      };
    }
  },
};

marked.use({ renderer, tokenizer });

// const hws = JSON.parse("{{ headwords | escapejs }}")
// const defaultMsg = {
//   div: '필수: 분류 선택',
//   headword: '필수: 표제어 (128자 이내, 중복 불가)',
//   definition: '필수: 정의 (Markdown, MathJax 지원)',
//   description: '선택: 상세 (Markdown, MathJax 지원)',
//   keywords: '선택: 관련키워드 ("," 구분자로 작성. 예를 들어, "keyword1, keyword2, keyword3")'
// }
//
// Vue.createApp({
//   data() {
//     return {
//       // defaultData: null,
//       div: {
//         value: null,
//         isValid: false,
//         msg: defaultMsg.div,
//       },
//       headword: {
//         value: null,
//         isValid: false,
//         msg: defaultMsg.headword,
//       },
//       definition: {
//         value: null,
//         isValid: false,
//         msg: defaultMsg.definition,
//       },
//       description: {
//         value: null,
//         isValid: true,
//         msg: defaultMsg.description,
//       },
//       keywords: {
//         value: null,
//         isValid: true,
//         msg: defaultMsg.keywords,
//       },
//       isDisabledButton: null,
//     }
//   },
//   computed: {
//     compiledMarkdown() {
//       return marked.parse(
//         `# ${this.headword.value}\n\n---\n\n- Wiki for: ${this.div.value}\n- Keywords: ${this.keywords.value}\n\n---\n\n## 정의\n\n${this.definition.value}\n\n---\n\n${this.description.value}`
//       )
//     },
//     checkForm() {
//       this.isDisabledButton = !(
//         this.div.isValid
//         && this.headword.isValid
//         && this.definition.isValid
//       )
//     }
//   },
//   methods: {
//     checkDivForm() {
//       if (this.div.value) {
//         this.div.isValid = true
//       } else {
//         this.div.isValid = false
//       };
//     },
//     checkHeadwordForm() {
//       tooLong = this.headword.value.length > 128;
//       tooShort = this.headword.value.length === 0;
//       // hwValidLength = this.headword.value.length <= 128;
//       hwUnique = !hws.includes(this.headword.value);
//       if (tooLong) {
//         this.headword.isValid = false
//         this.headword.msg = '너무 긴 표제어입니다. 128자 이내로 작성해주세요.'
//       } else if (tooShort) {
//         this.headword.isValid = false
//         this.headword.msg = defaultMsg.headword
//       } else if (!hwUnique) {
//         this.headword.isValid = false
//         this.headword.msg = `'${this.headword.value}'의 문서가 이미 존재합니다.`
//       } else {
//         this.headword.isValid = true
//         this.headword.msg = defaultMsg.headword
//       }
//     },
//     checkDefinitionForm() {
//       if (this.definition.value) {
//         this.definition.isValid = true
//       } else {
//         this.definition.isValid = false
//       };
//     },
//   }
// }).mount("#articleEditor")
