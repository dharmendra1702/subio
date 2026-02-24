new Chart(document.getElementById("salesChart"),{
type:"line",
data:{
labels:["Mon","Tue","Wed","Thu","Fri","Sat"],
datasets:[{
data:[12,20,15,30,22,35],
borderColor:"#00ff9d",
tension:.4,
fill:true
}]
},
options:{
plugins:{legend:{display:false}},
scales:{x:{display:false},y:{display:false}}
}
});