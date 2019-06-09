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
        canvas.onclick = move_client_0;
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
        }, 100)
        clients();
    }
)
function move_client_0(e){
    bot_clients[0].move([e.offsetX, e.offsetY])
}
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
            var tmp = [Math.floor(Math.random() * 501), Math.floor(Math.random() * 501)];
        bot_clients[i].move(tmp);
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
        bot_clients.push(new Client(i, fashion));
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
            this.updatePosition = this.updatePosition_serverless;
        }else{
            this.io = io(backend);
            this.register = this.register_server;
            this.login = this.login_server;
            this.move = this.move_server;
            this.io.on('move', this.move_callback.bind(this))
            this.get_throughput = this.get_move_throughput_server;
            this.updatePosition = this.updatePosition_server;
            this.io.on('whoami', this.update_callback_handler.bind(this));
            this.throughput_measuring = false;
        }
    }

    updatePosition_server(){
        this.io.emit('whoami');
    }
    update_callback_handler(data){
        if (this.throughput_measuring){
            this.counter++;
            this.io.emit('whoami');
        }
        this.position = data.position;
    }

    register_server(){
        this.io.emit('register', {username: this.username, password: this.username});
    }

    login_server(){
        this.io.emit('login', {username: this.username, password: this.username});
    }

    move_callback(){
        finished_thread ++;
        ticks += performance.now() - this.t0;
        if (finished_thread === clients_count){
            initial_time = performance.now() - initial_time;
        }
    }

    move_server(target){
        this.t0 = performance.now();
        this.io.emit('move', {target: target});
    }

    get_move_throughput_server(silent_mode=false){
        this.throughput_measuring = true;
        var last_check = 0;
        this.counter = 0;
        var start_time = performance.now();
        this.io.emit('whoami');
        var handler = function(){
            if (!silent_mode) logBoard.innerHTML += `<br/>Throughput ${this.counter - last_check} Request/Second in no overlapping fashion.`;
            else this.expose_number = this.counter - last_check;
            last_check = this.counter;
            if (this.counter < 1000) {
                setTimeout(handler,1000);
            }else{
                this.throughput_measuring = false;
            }
        }.bind(this);
        setTimeout(handler,1000)
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
    updatePosition_serverless(){
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