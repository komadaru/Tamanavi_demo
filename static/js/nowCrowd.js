const DIV_LIST_ICON = "listIcon";

const DIV_NOW_ICON = "nowIcon";

const P_RATE = "rate";

const P_VOTE_THANKS = "vote-thanks";

const IMAGE_SOURCE = ["free.png", "littlebusy.png", "busy.png", "verybusy.png"];

const RATE_TEXT = ["ガラガラ", "座れる程度", "肩が触れ合う", "満員"]

window.addEventListener("load", function() {
    page();
}, false);

function page() {
    view_list();
    view_now();
}

/** enumを解析して、一番多いcrowd番号を返す */
function getCrowd() {
    fetch('navi/realTimeCongestion').then((res) => {
        return res.json()
    }).then((json) => {
        var maxKey = null;
        var max = 0;
        for (key in json) {
            if (json[key] > max) {
                max = json[key];
                maxKey = key;
            }
        }
        if (maxKey == null){
            maxKey = 1;
        }
        var div_now = document.getElementById(DIV_NOW_ICON);
        let image = document.createElement("img");
        image.src = "static/image/" + IMAGE_SOURCE[maxKey - 1];
        div_now.appendChild(image);
        var p_rate = document.getElementById(P_RATE);
        p_rate.innerHTML = RATE_TEXT[maxKey - 1]
    })
}

function view_list(){
    var div_list = document.getElementById(DIV_LIST_ICON);
    for(let i = 0; i < IMAGE_SOURCE.length; i++){
        let button = document.createElement("button");
        let image = document.createElement("img");
        image.src = "static/image/" + IMAGE_SOURCE[i];
        button.appendChild(image);
        button.setAttribute("onclick", "vote(" + i + ")");
        div_list.appendChild(button);
    }
}

function vote(rate){
    const form = new FormData()
    form.append("congestion", rate + 1)
    const param = {
        method: "POST",
        body: form
    }
    // console.log(param)
    fetch('navi/vote', param).then((res) => {
        return res.json()
    }).then((json) => {
        // console.log(json);
        const votedNum = Object.values(json)[0];
        const p_vote = document.querySelector("#IconBlock>h1")
        p_vote.innerHTML = `「${RATE_TEXT[parseInt(votedNum) - 1]}」に投票しました！`
        var div_list = document.getElementById(DIV_LIST_ICON);
        for (let i = 0; i < div_list.children.length; i++) {
            const button = div_list.children.item(i)
            button.setAttribute("disabled", true)
        }
    })
}

function view_now() {
    getCrowd();
}