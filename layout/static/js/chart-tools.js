function intTickBeautifulizer(value) {
  if (value > 999 && value < 1e6) {
    return (value/1e3).toFixed(0) + 'K'
  } else if (value >= 1e6 && value < 1e9) {
    return (value/1e6).toFixed(0) + 'M'
  } else if (value >= 1e9 && value <1e12) {
    return (value/1e9).toFixed(0) + 'B'
  } else if (value >= 1e12) {
    return (value/1e12).toFixed(0) + 'T'
  }
}

function getColorPalette() {
  return [
    '#457CA2', "#DC3912", "#FF9900", "#109618", "#990099", "#3B3EAC", "#0099C6",
    "#DD4477", "#66AA00", "#B82E2E", "#316395", "#994499", "#22AA99", "#AAAA11",
    "#6633CC", "#E67300", "#8B0707", "#329262", "#5574A6", "#651067"
  ]
};

function dateFormatter(timestamp) {
  let date = new Date(timestamp);
  let strYear = date.getFullYear().toString();
  let strMonth = (date.getMonth()+1).toString().padStart(2,'0')
  let strDate = date.getDate().toString().padStart(2,'0')
  return `${strYear}-${strMonth}-${strDate}`
};

function hexToRgb(hex, alpha) {
  let r = parseInt(hex.slice(1, 3), 16),
    g = parseInt(hex.slice(3, 5), 16),
    b = parseInt(hex.slice(5, 7), 16);

  if (0 <= alpha && alpha <= 1) {
    return `rgba(${r}, ${g}, ${b}, ${alpha})`
  } else {
    return `rgb(${r}, ${g}, ${b})`
  }
}
