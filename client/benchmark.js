var ctx;
var clients_count = 1;
var bot_clients;
var ticks = 0;
var finished_thread = 0;
var logBoard;
var initial_time;
var keep_update;
$().ready(
    function(){
        var canvas = $('#stage')[0];
        ctx = canvas.getContext("2d");
        logBoard = $('#logs')[0];
        keep_update = $('#keep-update')[0];
        $('#mov').click(move);
        $('#reg').click(register);
        $('#log').click(login);
        $('#clients').change(clients);
        $('#single-player-throughput').click(spt);
        $('#multiple-player-throughput').click(mpt);
        $('#update').click(update);
        setInterval(function(){
            // clear canvas
            ctx.beginPath();
            ctx.stroestyle = 'none';
            ctx.rect(0,0,500,500);
            ctx.fillStyle = 'white';
            ctx.fill()
            ctx.closePath();
            // draw clients
            try{
                for(var i = 0; i < clients_count; i++){
                    bot_clients[i].draw();
                }
            }catch (err){}

            if (finished_thread === clients_count){
                logBoard.innerHTML += `<br/>Sent moving operation for ${clients_count} clients. Total local processing time: ${initial_time}, Totol transmission time: ${ticks}, Average time: ${ticks/clients_count}`;
                ticks = 0;
                finished_thread = 0;
            }
        },500);
        setInterval(function(){
            if (keep_update.checked){
                for(var i = 0; i < clients_count; i++){
                    bot_clients[i].updatePosition();
                }
            }
        }, 3000)
        bot_clients = [new Client(0)];
    }
)

function point(x, y, color){
    ctx.beginPath();
    ctx.stroestyle = 'none';
    ctx.rect(x-2,y-2,4,4);
    ctx.fillStyle = color;
    ctx.fill()
    ctx.closePath();
}
function move(){
    ticks = 0;
    finished_thread = 0;
    initial_time = performance.now();
    for (var i = 0 ; i < clients_count ; i++){
        bot_clients[i].move();
    }
}
function register(){
    for (var i = 0 ; i < clients_count ; i++){
        bot_clients[i].register();
    }
    alert('Register finished!');
}
function login(){
    for (var i = 0 ; i < clients_count ; i++){
        bot_clients[i].login();
    }
    alert('Login finished!');
}

function clients(){
    clients_count = parseInt(2 ** ($('#clients')[0].value /10));
    $('#counts')[0].innerText = clients_count;
    bot_clients = new Array();
    for (var i = 0 ; i < clients_count ; i++){
        bot_clients.push(new Client(i));
    }
}

class Client {
    constructor(number, type='serverless') {
        this.username = `test${number}`;
        // this.position = [0,0];
        this.position = [0, 0];
        this.expose_number = 0;
        this.color = getRandomColor();
        if (type === 'serverless'){
            this.register = this.register_serverless;
            this.login = this.login_serverless;
            this.move = this.move_serverless;
            this.get_throughput = this.get_move_throughput;
        }
    }
    register_serverless(){
        $.post('https://7v5r09dlhj.execute-api.us-west-1.amazonaws.com/beta/pask-main', JSON.stringify({op: 'register', account: this.username, password: this.username}));
    }
    login_serverless(){
        $.post('https://7v5r09dlhj.execute-api.us-west-1.amazonaws.com/beta/pask-main', JSON.stringify({op: 'login', account: this.username, password: this.username})).done(
            function(data){this.token = data.token;}.bind(this)
        );
    }
    move_serverless(target){
        var t0 = performance.now();
        $.post('https://7v5r09dlhj.execute-api.us-west-1.amazonaws.com/beta/pask-main', JSON.stringify({op: 'move', token: this.token, target: target})).done(
            function(){
                finished_thread ++;
                ticks += performance.now() - t0;
                if (finished_thread === clients_count){
                    initial_time = performance.now() - initial_time;
                }
            }
        );
    }
    get_move_throughput(silent_mode=false){
        var start_time = performance.now();
        var last_check = 0;
        this.counter = 0;
        this._get_move_throughput();
        var handler = function(){
            if (!silent_mode) logBoard.innerHTML += `<br/>Throughput ${this.counter - last_check} Request/Second in no overlapping fashion.`;
            else this.expose_number = this.counter - last_check;
            last_check = this.counter;
            if (this.counter < 1000) setTimeout(handler,1000);
        }.bind(this);
        setTimeout(handler,1000)
    }
    _get_move_throughput(){
        $.post('https://7v5r09dlhj.execute-api.us-west-1.amazonaws.com/beta/pask-main', JSON.stringify({op: 'whoami', token: this.token})).done(
            function(data){
                this.counter ++;
                this.position = data.position;
                if (this.counter <= 1000){
                    this._get_move_throughput();
                }
            }.bind(this)
        );
    }
    draw(){
        point(...this.position, this.color);
    }
    updatePosition(){
        $.post('https://7v5r09dlhj.execute-api.us-west-1.amazonaws.com/beta/pask-main', JSON.stringify({op: 'whoami', token: this.token})).done(
            function(data){
                this.position = data.position;
            }.bind(this)
        );
    }
}


function getRandomColor() {
    var letters = '0123456789ABCDEF';
    var color = '#';
    for (var i = 0; i < 6; i++) {
      color += letters[Math.floor(Math.random() * 16)];
    }
    return color;
  }

function spt(){
    bot_clients[0].get_throughput();
}

function mpt(){
    var loop = true;
    var counter = 0;
    for (var i = 0; i< clients_count; i++){
        bot_clients[i].get_throughput(true);
    }
    var handler = function(){
        counter = 0;
        for (var i = 0; i< clients_count; i++){
            counter += bot_clients[i].expose_number;
            if (bot_clients[i].counter >= 1000) loop = false;
        }
        logBoard.innerHTML += `<br/>Throughput ${counter} Request/Second in no overlapping fashion.`;
        if (loop) setTimeout(handler, 1000);
    }
    setTimeout(handler, 1000);
}

function update(){
    for (var i = 0; i< clients_count; i++){
        bot_clients[i].updatePosition();
    }
}