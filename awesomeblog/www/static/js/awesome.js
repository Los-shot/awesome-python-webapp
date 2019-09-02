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

let awesome = new Awesome();
    