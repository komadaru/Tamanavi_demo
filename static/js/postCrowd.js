const CANVAS_ID = "#chart";

var Labels = ["8", "9", "10", "11", "12", "13", "14", "15", "16", "17", "18", "19"];
var day = 0
const DAYS = ["月", "火", "水", "木", "金", "土"]
var congestion = null
var chart = null

window.addEventListener("load", function() {
    getList();
}, false);


function createChart(day) {
    const ctx = document.querySelector(CANVAS_ID).getContext("2d");
    chart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: Labels,
            datasets: [{
                label: DAYS[day] + "曜の混雑度",
                data: Object.values(congestion[day]),
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false
        }
    });
}

function updateChart(day) {
    if(chart) {
        chart.destroy()
    }
    createChart(day)
}

function getList() {
    fetch("navi/congestionHistory").then((res) => {
        return res.json()
    }).then((json) => {
        congestion = json.byTime
        createChart(day);
    })
}