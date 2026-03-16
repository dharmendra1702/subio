async function loadStats(){

const res = await fetch("/dashboard/api/stats/")
const data = await res.json()

document.getElementById("revenue").innerText = "₹" + data.total_revenue
document.getElementById("daily_orders").innerText = data.daily_orders

}

setInterval(loadStats,5000)

loadStats()