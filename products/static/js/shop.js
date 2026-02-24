const cards = [...document.querySelectorAll('.card')];
const grid = document.getElementById('grid');
const searchInput = document.getElementById('search');

let activeCategory="all";
let maxPrice=Infinity;
let minWeight="";
let inStock=false;

function applyFilters(){

cards.forEach(card=>{

let show=true;

// category
if(activeCategory!=="all" && card.dataset.cat!==activeCategory) show=false;

// search
if(searchInput.value){
show = show && card.dataset.name.includes(searchInput.value.toLowerCase());
}

// price
const price=parseFloat(card.dataset.price);
show = show && price<=maxPrice;

// weight
if(minWeight){
show = show && parseInt(card.dataset.weight)>=parseInt(minWeight);
}

// apply
card.classList.toggle("hide",!show);
});
}

function filterCat(cat,el){
activeCategory=cat;
document.querySelectorAll(".cat-circle").forEach(c=>c.classList.remove("active"));
el.classList.add("active");
applyFilters();
}

function searchProducts(){applyFilters()}

function sortProducts(t){

if(t==="relevance"){location.reload();return;}

if(t==="low") cards.sort((a,b)=>a.dataset.price-b.dataset.price);
if(t==="high") cards.sort((a,b)=>b.dataset.price-a.dataset.price);
if(t==="name") cards.sort((a,b)=>a.dataset.name.localeCompare(b.dataset.name));

cards.forEach(c=>grid.appendChild(c));
}

function filterPrice(v){
maxPrice=parseFloat(v);
document.getElementById("priceVal").innerText=v;
applyFilters();
}

function filterWeight(v){minWeight=v;applyFilters()}
function filterStock(e){inStock=e.checked;applyFilters()}

function clearFilters(){location.reload()}

function wish(el){
el.classList.toggle("active");
el.innerHTML=el.classList.contains("active")?"❤":"♡";
el.classList.add("pop");
setTimeout(()=>el.classList.remove("pop"),300);
}

function toggleFilters(){
document.getElementById("filterBox").classList.toggle("active");
}