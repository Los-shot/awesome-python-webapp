'use strict'

let Awesome = function(){

}

Awesome.prototype.setUser = function(user){
    this.user = user;
    console.log('user:',user)
}

Awesome.prototype.setUser = function(user){
    this.user = user;
}

Awesome.prototype.getUser = function(user){
    return this.user;
}

Awesome.prototype.getQueryString = function(name){
    let reg = new RegExp("(^|&)" + name + "=([^&]*)(&|$)", "i");
    let r = window.location.search.substr(1).match(reg);
    
    if (r != null) {
        return unescape(r[2]);
    };

    return null;
}

Awesome.prototype.timeFormat = function(timestamp,fmt = 'yyyy-MM-dd hh:mm:ss'){
    let regExps = {
        "M+": new RegExp("(M+)"),
        "d+": new RegExp("(d+)"),
        "h+": new RegExp("(h+)"),
        "m+": new RegExp("(m+)"),
        "s+": new RegExp("(s+)"),
        "S": new RegExp("(S)"),
        "%s": new RegExp("(%s)"),
        "{d}": /({\d+})/g
    };

    let date = new Date(timestamp * 1000);

    let o = {
        "M+": date.getMonth() + 1,
        "d+": date.getDate(),
        "h+": date.getHours(),
        "m+": date.getMinutes(),
        "s+": date.getSeconds(),
        // "q+": Math.floor((data.getMonth() + 3) / 3), //季度 
        "S": date.getMilliseconds() //毫秒 
    };
    if (/(y+)/.test(fmt)) {
        fmt = fmt.replace(RegExp.$1, (date.getFullYear() + "").substr(4 - RegExp.$1.length));
    }
    for (var k in o)
        if (regExps[k].test(fmt)) {
            fmt = fmt.replace(RegExp.$1, (RegExp.$1.length == 1) ? (o[k]) : (("00" + o[k]).substr(("" + o[k]).length)));
        }
    return fmt;
}

let awesome = new Awesome();
    