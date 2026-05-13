const API_URL = "http://127.0.0.1:8000";

let tradeCharts = {};
let tradeHistories = {};
let priceChart;
let priceHistory = [];
let pnlHistory = [];
let pnlChart;

// =============================
async function loadStatus() {

    try{
        const res = await fetch(API_URL + "/status");
        const data = await res.json();

        document.getElementById("capital").innerText =
            (data.capital || 0).toFixed(2);

        document.getElementById("position").innerText =
            (data.positions && data.positions.length > 0)
                ? "🟢 Operando"
                : "🔴 Fora";

        document.getElementById("symbol").innerText =
            (data.positions || []).map(p => p.symbol).join(", ") || "-";

        let totalProfit = data.total_profit || 0;
        let totalValue = data.total_value || 0;

        document.getElementById("positionProfit").innerText =
            totalProfit.toFixed(2);

        document.getElementById("positionValue").innerText =
            "R$ " + totalValue.toFixed(2);

        document.getElementById("variation").innerText =
            totalProfit.toFixed(2) + "%";

        if(data.positions && data.positions.length > 0){
            document.getElementById("entryPrice").innerText =
                data.positions[0].entry_price.toFixed(4);
        } else {
            document.getElementById("entryPrice").innerText = "-";
        }

        document.getElementById("breakEven").innerText =
            data.break_even_active ? "🟢 ATIVO" : "⚪ OFF";

        const el = document.getElementById("currentPrice");

        if(totalProfit >= 0){
            el.innerText = "+R$ " + totalProfit.toFixed(2);
            el.style.color = "#22c55e";
        } else {
            el.innerText = "R$ " + totalProfit.toFixed(2);
            el.style.color = "#ef4444";
        }

        document.getElementById("profitValue").innerText =
            totalProfit.toFixed(2);

        renderTrades(data.positions || []);

        // 🔥 GRÁFICO (AGORA CERTO)
        pnlHistory.push(totalProfit);

        if(pnlHistory.length > 50){
            pnlHistory.shift();
        }

        pnlChart.data.labels = pnlHistory.map((_, i) => i);
        pnlChart.data.datasets[0].data = pnlHistory;

        pnlChart.update();

    } catch(e){
        console.log("Erro status:", e);
    }

    // 🔥 gráfico PnL
    if(!pnlChart) return;

    if(pnlHistory.length > 50){
        pnlHistory.shift();
    }

    pnlChart.data.labels = pnlHistory.map((_, i) => i);
    pnlChart.data.datasets[0].data = pnlHistory;

    // cor dinâmica
    pnlChart.data.datasets[0].borderColor =
        totalProfit >= 0 ? "#22c55e" : "#ef4444";

    pnlChart.update();
}


// =============================
async function loadSignal(){
    try{
        const res = await fetch(API_URL + "/signal");
        const signals = await res.json(); // 👈 agora é lista

        const container = document.getElementById("signalCard");
        container.innerHTML = "";

        if(!signals || signals.length === 0){
            container.innerHTML = "<p>Sem sinal</p>";
            return;
        }

        signals.forEach(signal => {

            const div = document.createElement("div");

            div.innerHTML = `
                <p>SINAL: ${signal.symbol} @ ${signal.price}</p>
                <button onclick="confirmTrade('${signal.symbol}')">
                    Confirmar ${signal.symbol}
                </button>
            `;

            container.appendChild(div);
        });

    } catch(e){
        console.log("Erro signal:", e);
    }
}
    
// =============================
function renderTrades(positions = []){

    const container = document.getElementById("tradesContainer");

    if(!positions || positions.length === 0){
        container.innerHTML = "";
        return;
    }

    positions.forEach((pos) => {

        const id = "chart_" + pos.symbol;

        // 🔥 cria card se não existir
        if(!document.getElementById(id)){

            const card = document.createElement("div");
            card.classList.add("trade-card");

            card.innerHTML = `
                <div class="trade-header">
                    <span class="trade-title">${pos.symbol}</span>
                    <button class="close-btn" onclick="closeSingle('${pos.symbol}')">✖</button>
                </div>

                <div id="info_${id}"></div>
                <canvas id="${id}" height="100"></canvas>
            `;

            container.appendChild(card);

            tradeHistories[id] = [];

            const ctx = document.getElementById(id).getContext("2d");

            tradeCharts[id] = new Chart(ctx, {
                type: "line",
                data: {
                    labels: [],
                    datasets: [{
                        data: [],
                        borderWidth: 2,
                        tension: 0.4,
                        fill: true
                    }]
                },
                options: {
                    animation: false,
                    plugins: { legend: { display: false }},
                    scales: { x: { display: false }, y: { display: false }}
                }
            });
        }

        const profit = pos.profit || 0;
        const price = pos.current_price || 0;

        if(!price) return;

        const info = document.getElementById("info_" + id);

        info.innerHTML = `
            <span class="${profit >= 0 ? 'trade-profit' : 'trade-loss'}">
                ${profit.toFixed(2)} (${pos.variation.toFixed(2)}%)
            </span>
        `;

        // 🔥 AQUI É O SEGREDO (PREÇO REAL)
        tradeHistories[id].push({
        price: price,
        time: Date.now()
    });

        const chart = tradeCharts[id];

        chart.data.labels = tradeHistories[id].map(p => p.time);
        chart.data.datasets[0].data = tradeHistories[id].map(p => p.price);

        chart.data.datasets[0].borderColor =
            profit >= 0 ? "#22c55e" : "#ef4444";

        chart.data.datasets[0].backgroundColor =
            profit >= 0
                ? "rgba(34,197,94,0.15)"
                : "rgba(239,68,68,0.15)";
                

        chart.update();
    });
}

// =============================
async function loadTrades(){

    try{
        const res = await fetch(API_URL + "/trades");
        const trades = await res.json();

        const list = document.getElementById("tradeList");
        list.innerHTML = "";

        trades.slice().reverse().forEach(trade => {

            const item = document.createElement("div");
            item.classList.add("trade-item");

            const isProfit = trade.result >= 0;

            item.innerHTML = `
                <div>
                    <strong>${trade.symbol}</strong><br>
                    ${trade.entry_price.toFixed(4)} → ${trade.exit_price.toFixed(4)}<br>
                    ${trade.timestamp}
                </div>
                <div style="color:${isProfit ? '#22c55e' : '#ef4444'}">
                    ${isProfit ? '+' : ''}${trade.result.toFixed(2)}
                </div>
            `;

            list.appendChild(item);
        });

    } catch(e){
        console.log("Erro trades:", e);
    }
}

// =============================
// 🔥 TOP MOEDAS
async function loadTopCoins() {

    try{
        const res = await fetch(API_URL + "/all_coins");
        const coins = await res.json();

        const container = document.getElementById("topCoins");
        const bestContainer = document.getElementById("bestCoinsList");

        container.innerHTML = "";
        bestContainer.innerHTML = "";

        coins.slice(0, 100).forEach(coin => {

            const change = parseFloat(coin.priceChangePercent || 0);
            const color = change >= 0 ? "#22c55e" : "#ef4444";

            const div = document.createElement("div");

            div.innerHTML = `
                <strong>${coin.symbol}</strong>
                <span style="color:${color}; float:right;">
                    ${change.toFixed(2)}%
                </span>
            `;

           div.onclick = () => {

    const s1 = document.getElementById("symbol1");
    const s2 = document.getElementById("symbol2");

    if(s1.value === coin.symbol || s2.value === coin.symbol){
        return; // evita duplicar
    }

    if(!s1.value){
        s1.value = coin.symbol;
    } else if(!s2.value){
        s2.value = coin.symbol;
    } else {
        s2.value = coin.symbol; // substitui a segunda
    }
};

            container.appendChild(div);
        });

        coins.slice(0, 10).forEach((coin, i) => {

            const div = document.createElement("div");

            div.innerHTML = `
                ${i+1} 🔥 <strong>${coin.symbol}</strong>
                <span style="float:right; color:#22c55e;">
                    ${parseFloat(coin.priceChangePercent).toFixed(2)}%
                </span>
            `;

            bestContainer.appendChild(div);
        });

    } catch(e){
        console.log("Erro top coins:", e);
    }
}

// =============================
// 🔥 HOT COINS
async function loadHotCoins(){

    try{
        const res = await fetch(API_URL + "/hot_coins");
        const coins = await res.json();

        const container = document.getElementById("hotCoins");
        container.innerHTML = "";

        coins.forEach((coin, i) => {

            const div = document.createElement("div");

            div.innerHTML = `
                ${i+1} 🔥 <strong>${coin.symbol}</strong>
                <span style="float:right; color:#22c55e;">
                    ${coin.variation.toFixed(2)}%
                </span>
            `;

            container.appendChild(div);
        });

    } catch(e){
        console.log("Erro hot coins:", e);
    }
}

// =============================
// 📈 GRÁFICO DE PREÇO
function initPriceChart(){

    const ctx = document.getElementById('priceChart').getContext('2d');

    priceChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Preço',
                data: [],
                borderColor: "#3b82f6",
                tension: 0.3
            }]
        }
    });
}

async function loadPrice(){

    try{
        const res = await fetch(API_URL + "/status");
        const data = await res.json();

        if(!data.positions || (data.positions || []).length === 0) return;

        const price = data.positions[0].current_price;

        priceHistory.push(price);

        if(priceHistory.length > 50){
            priceHistory.shift();
        }

        priceChart.data.labels = priceHistory.map((_, i) => i);
        priceChart.data.datasets[0].data = priceHistory;

        priceChart.update();

    } catch(e){
        console.log("Erro price:", e);
    }
}

// =============================
async function confirmTrade(symbol){
    await fetch(API_URL + "/confirm_trade", {
        method:"POST",
        headers:{ "Content-Type":"application/json" },
        body: JSON.stringify({ symbol })
    });
}

async function closeSingle(symbol){

    if(!confirm("Fechar trade de " + symbol + "?")) return;

    try{
        const res = await fetch(API_URL + "/close_position", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ symbol: symbol })
        });

        const data = await res.json();

        console.log("Fechado:", data);

        // 🔥 REMOVE NA HORA DA TELA (sem esperar refresh)
        Object.keys(tradeCharts).forEach(id => {
            if(id.includes(symbol)){
                const el = document.getElementById(id);
                if(el){
                    el.parentElement.remove();
                }
                delete tradeCharts[id];
                delete tradeHistories[id];
            }
        });

    } catch(e){
        console.log("Erro fechar:", e);
    }
}

async function updateControl(){

    console.log("🔥 aplicando estratégia");

    const symbol1 = document.getElementById("symbol1").value;
    const symbol2 = document.getElementById("symbol2").value;

    const take = parseFloat(document.getElementById("takeInput").value) || null;
    const stop = parseFloat(document.getElementById("stopInput").value) || null;

    console.log("📤 enviando:", symbol1, symbol2, take, stop);

    try{
        const res = await fetch(API_URL + "/update_control", {
            method:"POST",
            headers:{ "Content-Type":"application/json" },
            body: JSON.stringify({
                symbols: [symbol1, symbol2],
                take_profit: take,
                stop_loss: stop
            })
        });

        const data = await res.json();
        console.log("✅ resposta:", data);

    } catch(e){
        console.log("❌ erro:", e);
    }
}

async function closeSingle(symbol){

    if(!confirm("Fechar trade de " + symbol + "?")) return;

    try{
        const res = await fetch(API_URL + "/close_position", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ symbol: symbol })
        });

        const data = await res.json();

        Object.keys(tradeCharts).forEach(id => {
            if(id.includes(symbol)){
                const el = document.getElementById(id);

                if(el){
                    const card = el.parentElement;

                    // 🔥 AQUI
                    card.style.transition = "0.3s";
                    card.style.opacity = "0";

                    setTimeout(() => card.remove(), 300);
                }

                delete tradeCharts[id];
                delete tradeHistories[id];
            }
        });

    } catch(e){
        console.log("Erro fechar:", e);
    }
}

// =============================
function refresh(){
    console.log("🔄 atualizando...");
    loadStatus();
    loadSignal();
    loadTopCoins();
    loadHotCoins();
    loadTrades();
    loadPrice();
}

function initPnLChart(){
    const el = document.getElementById('capitalChart');

    if(!el){
        console.log("❌ canvas não encontrado");
        return;
    }

    const ctx = el.getContext('2d');

    pnlChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Lucro/Prejuízo',
                data: [],
                borderColor: '#22c55e',
                backgroundColor: 'rgba(34,197,94,0.1)',
                fill: true,
                tension: 0.4
            }]
        }
    });

    console.log("✅ gráfico criado");
}

// 👇 COLOCA AQUI EMBAIXO
document.getElementById("positionValueInput").addEventListener("input", updatePreview);
document.getElementById("riskMode").addEventListener("change", updatePreview);

function updatePreview(){

    const value = parseFloat(document.getElementById("positionValueInput").value) || 0;
    const mode = document.getElementById("riskMode").value;

    let autoTake = 0;
    let autoStop = 0;

    if(mode === "conservador"){
        autoTake = value * 0.02;
        autoStop = value * 0.01;
    }

    if(mode === "moderado"){
        autoTake = value * 0.04;
        autoStop = value * 0.02;
    }

    if(mode === "agressivo"){
        autoTake = value * 0.08;
        autoStop = value * 0.04;
    }

    // MOSTRA NA TELA
    document.getElementById("previewValue").innerText =
        "R$ " + value.toFixed(2);

    document.getElementById("takeValue").innerText =
        "R$ " + autoTake.toFixed(2);

    document.getElementById("stopValue").innerText =
        "R$ " + autoStop.toFixed(2);

    // 🔥 AUTO PREENCHER SE ESTIVER VAZIO
    const takeInput = document.getElementById("takeInput");
    const stopInput = document.getElementById("stopInput");

    if(!takeInput.value){
        takeInput.value = autoTake.toFixed(2);
    }

    if(!stopInput.value){
        stopInput.value = autoStop.toFixed(2);
    }
}


// =============================
initPriceChart();
initPnLChart();
setInterval(refresh, 3000);
refresh();