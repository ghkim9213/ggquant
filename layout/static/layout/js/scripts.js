// Vue.filter('float', function(value){
//   return value.toLocaleString(undefined, {'mininumFractionDigits':2,'maximumFractionDigits':2})
// })
//
// Vue.filter('integer', function(value){
//   return value.toLocaleString()
// })
//
// const tickApp = new Vue({
//   el: '#ticksExample',
//   data: {
//     ticks: null,
//     emptycols: null
//   },
//   created: function(){
//     const socket = new WebSocket('ws://' + window.location.host + '/ws/ticks/')
//
//     let _this = this;
//
//     socket.onmessage = function(event){
//       _this.ticks = JSON.parse(event.data)
//       if (_this.ticks.items === null) {
//         _this.emptycols = Array.from(Array(10))
//       } else {
//         _this.emptycols = Array.from(Array(10 - _this.ticks.items.length).keys())
//       }
//       console.log(_this.ticks)
//     }
//   }
// })
//
// const minuteApp = new Vue({
//   el: '#minutesExample',
//   data: {
//     minutes: null
//   },
//   created: function(){
//     const socket = new WebSocket('ws://' + window.location.host + '/ws/minutes/')
//
//     let _this = this;
//
//     socket.onmessage = function(event){
//       _this.minutes = JSON.parse(event.data);
//       console.log(_this.minutes)
//     }
//   }
// })
