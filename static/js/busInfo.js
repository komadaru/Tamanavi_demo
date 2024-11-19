/** バスの種類 */
const TYPE = {
    bus_a: "BusA",
    bus_b: "BusB",
    bus_c: "BusC"
};

/** バス停 */
const POSITION = {
    Sta_a: 0,
    Sta_b: 1,
    Sta_c: 2,
    Sta_d: 3,
    Sta_e: 4,
    Sta_f: 5,
}

/** バスがいる場所 */
const STATE = {
    rest: "rest",
    stop_right: "stop_right",
    stop_left: "stop_left",
    next: "next",
    prev: "prev"
}

/** 駅の種類 */
const STA_STATE = {
    ao: "ao",
    other: "other",
    both: "both",
    top: "top",
    bottom: "bottom"
}

const CLASSNAME_STA = "station";

/** バス停名 */
const STATION = ["体育館前", "経済学部前", "総合棟", "正門守衛場", "EGG DOME", "スポーツ健康学部棟"];

const STATION_STATE = [STA_STATE.both, STA_STATE.both, STA_STATE.top, STA_STATE.top, STA_STATE.bottom, STA_STATE.ao];

const STATION_WAY = [STATE.stop_right, STATE.stop_right, STATE.stop_right, STATE.stop_left,
    STATE.stop_left, STATE.stop_left, STATE.stop_right]

const STATION_ORDER = [POSITION.Sta_d, POSITION.Sta_c, POSITION.Sta_b, POSITION.Sta_a,
    POSITION.Sta_b, POSITION.Sta_e, POSITION.Sta_f];

const DIV_STATIONS = "stations";

const DIV_ARROW = "arrow";

const BUSES = [];

const BUS_IMAGES = ["bus.png", "bus.png", "bus.png"];

const FRAME = 5000;

const P_TIME = "time";
const P_BOTTOM = "p_bottom";
const P_TOP = "p_top";

var times_station_div = [];

class Bus {
    constructor(type, src) {
        this.type = type || null;
        this.src = src || null;
        this.position = null;
        this.state = STATE.rest;
    }
    createView() {
        var div_stations = document.getElementById(DIV_STATIONS);
        let bus = document.createElement("img");
        bus.className = this.state;
        bus.id = this.type;
        bus.src = "static/image/" + this.src;
        div_stations.appendChild(bus);
    }
    set(position, state) {
        this.position = position;
        this.state = state;
        this.renew();
    }
    renew() {
        var div_stations = document.getElementById(DIV_STATIONS);
        var target = document.getElementById(this.type);
        if (this.state == STATE.rest) {
            div_stations.insertBefore(target, null);
        } else if (this.state == STATE.stop_right || this.state == STATE.stop_left) {
            var station = document.querySelectorAll("#" + DIV_STATIONS + ">." + CLASSNAME_STA);
            station = station[this.position];
            var station_children = station.children[0];
            station.insertBefore(target, station_children);
        } else if (this.state == STATE.next) {
            var arrow = document.querySelectorAll("#" + DIV_STATIONS + ">." + "arrow");
            if (this.position < arrow.length) {
                arrow = arrow[this.position];
                var arrow_child = arrow.children[1];
                arrow.insertBefore(target, arrow_child);
            } else {
                div_stations.insertBefore(target, null);
                this.state = STATE.rest;
            }
        } else if (this.state == STATE.prev) {
            var arrow = document.querySelectorAll("#" + DIV_STATIONS + ">." + "arrow");
            if (0 <= this.position - 1) {
                arrow = arrow[this.position - 1];
                var arrow_child = arrow.children[1];
                arrow.insertBefore(target, arrow_child);
            } else {
                div_stations.insertBefore(target, null);
                this.state = STATE.rest;
            }
        }
        target.className = this.state;
    }

}

/** 画面がloadされたら実行される */
window.addEventListener("load", function() {
    page();
}, false);

/** top pageを表示 */
function page() {
    view_stations();

    BUSES.push(new Bus(TYPE.bus_a, BUS_IMAGES[0]),
        new Bus(TYPE.bus_b, BUS_IMAGES[1]),
        new Bus(TYPE.bus_c, BUS_IMAGES[2]));

    view_buses();
    
    view_times();

    buses_get();
    times_get();
    setInterval(repeat, FRAME);
}

function repeat(){
    buses_get();
    times_get();
}

function buses_get(){
    fetch("navi/lastStation").then((res) => {
        return res.json();
    }).then((nowBuses) => {
        for (let i = 0; i < BUSES.length; i++){
            if ((i+1) in nowBuses){
                let index = nowBuses[(i + 1)];
                BUSES[i].set(STATION_ORDER[index], STATION_WAY[index]);
            } else {
                BUSES[i].set(null, STATE.rest);
            }
        }
        // 確認用
        // console.log(nowBuses);
    });
}

function times_get() {
    fetch("navi/estTime").then((res) => {
        return res.json();
    }).then((times) => {
        const mins = []
        for (let station in times) {
            mins.push(Math.min(...Object.values(times[station])))
        }
        // console.log(mins)
        for (let i = 0; i < mins.length; i++){
            if (mins[i] == Infinity) {
                times_station_div[i].textContent = "休";
            } else {
                let minutes = Math.round(mins[i]);
                times_station_div[i].textContent = minutes + "分";
            }
        }
    });
}

function view_stations() {
    var div_stations = document.getElementById(DIV_STATIONS);
    for (let i = 0; i < STATION.length; i++) {
        let sta = document.createElement("div");
        sta.className = CLASSNAME_STA + " " + STATION_STATE[i];
        let p = document.createElement("p");
        p.textContent = STATION[i];
        sta.appendChild(p);
        div_stations.appendChild(sta);
        if (i != STATION.length - 1) {
            let arrow = document.createElement("div");
            arrow.className = DIV_ARROW;
            let arrow1 = document.createElement("div");
            arrow.appendChild(arrow1);
            let arrow2 = document.createElement("div");
            arrow.appendChild(arrow2);
            div_stations.appendChild(arrow);
        }
    }
}

function view_buses() {
    for (let i = 0; i < BUSES.length; i++) {
        BUSES[i].createView();
    }
}

function view_times(){
    var stas = document.getElementsByClassName(CLASSNAME_STA);
    var sta_list = [];
    for (let i = 0; i < STATION.length; i++){
        sta_list.push(0);
    }
    for (let i = 0; i < STATION_ORDER.length; i++){
        if (STATION_STATE[STATION_ORDER[i]] != STA_STATE.bottom && STATION_ORDER[i] != 0 && sta_list[STATION_ORDER[i]] == 0){
            let p = document.createElement("div");
            p.textContent = i;
            p.className = P_TIME + " " + P_TOP;
            stas[STATION_ORDER[i]].appendChild(p);
            sta_list[STATION_ORDER[i]]++;
            times_station_div.push(p);
        } else if ((STATION_STATE[STATION_ORDER[i]] != STA_STATE.top) ||
        (STATION_STATE[STATION_ORDER[i]] != STA_STATE.top && sta_list[STATION_ORDER[i]] == 1)){
            let p = document.createElement("div");
            p.textContent = i;
            p.className = P_TIME + " " + P_BOTTOM + " s" + i;
            stas[STATION_ORDER[i]].appendChild(p);
            sta_list[STATION_ORDER[i]]++;
            times_station_div.push(p);
        }
    }
}