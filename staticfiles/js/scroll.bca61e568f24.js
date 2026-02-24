/* =====================================================
   GLOBAL SCROLL ANIMATION
===================================================== */

const animated = document.querySelectorAll(".animate");

const revealObserver = new IntersectionObserver(entries => {
  entries.forEach(entry => {
    if (entry.isIntersecting) entry.target.classList.add("show");
  });
}, { threshold: 0.2 });

animated.forEach(el => revealObserver.observe(el));

/* =====================================================
   PRODUCT CAROUSEL (DESKTOP + MOBILE)
===================================================== */

const track = document.getElementById("carousel");
const dotsBox = document.getElementById("carouselDots");

if (track) {

  const SPEED = 3000;
  let index = 0;

  const originals = Array.from(track.children);
  const originalsCount = originals.length;

  /* DOTS */

  originals.forEach((_, i) => {
    const dot = document.createElement("span");
    dot.onclick = () => jump(i);
    dotsBox.appendChild(dot);
  });

  /* CLONE FOR INFINITE LOOP */

  for (let i = 0; i < 3; i++) {
    originals.forEach(slide => track.appendChild(slide.cloneNode(true)));
  }

  let items = Array.from(track.children);
  const total = items.length;
  let ITEM = items[0].offsetWidth;

  function setWidth() {
    ITEM = items[0].offsetWidth;
  }

  function update() {

    track.style.transform = `translateX(-${index * ITEM}px)`;

    items.forEach(i => i.classList.remove("active"));

    const center = window.innerWidth <= 768 ? index + 1 : index + 2;
    if (items[center]) items[center].classList.add("active");

    dotsBox.querySelectorAll("span").forEach(d => d.classList.remove("active"));
    dotsBox.children[index % originalsCount]?.classList.add("active");
  }

  function move() {

    index++;

    if (index >= total - originalsCount) {

      track.style.transition = "none";
      index = originalsCount;
      track.style.transform = `translateX(-${index * ITEM}px)`;
      track.offsetHeight;
      track.style.transition = "transform .8s ease";

    } else {
      track.style.transition = "transform .8s ease";
      update();
    }
  }

  function jump(i) {
    const set = Math.floor(index / originalsCount);
    index = set * originalsCount + i;
    update();
  }

  setInterval(move, SPEED);

  window.addEventListener("resize", () => {
    setWidth();
    update();
  });

  setWidth();
  index = originalsCount;
  update();

  /* MOBILE ACTIVE CENTER */

  if (window.innerWidth <= 768) {

    function mobileActive() {
      const center = track.scrollLeft + track.offsetWidth / 2;

      items.forEach(item => {
        const pos = item.offsetLeft + item.offsetWidth / 2;
        item.classList.toggle("active", Math.abs(center - pos) < item.offsetWidth / 2);
      });
    }

    track.addEventListener("scroll", mobileActive);

    setInterval(() => {
      track.scrollBy({ left: track.offsetWidth * .7, behavior: "smooth" });
    }, SPEED);

    mobileActive();
  }
}

/* =====================================================
   ALTERNATING PRODUCTS
===================================================== */

const altRows = document.querySelectorAll(".alt-row");
const headings = document.querySelectorAll(".alt-content h3");

window.addEventListener("scroll", () => {

  altRows.forEach((row, i) => {
    if (row.getBoundingClientRect().top < window.innerHeight - 120) {
      row.style.transitionDelay = `${i * .15}s`;
      row.classList.add("show");
    }
  });

  headings.forEach(h => {
    if (h.getBoundingClientRect().top < window.innerHeight - 150) {
      h.classList.add("line");
    }
  });

});

/* =====================================================
   FARM TO FORK
===================================================== */

const flowItems = document.querySelectorAll(".flow-item");
const processSection = document.querySelector(".process-classic");

if (processSection) {

  new IntersectionObserver(e => {
    if (e[0].isIntersecting) {
      processSection.classList.add("show");
      flowItems.forEach((el, i) => setTimeout(() => el.classList.add("show"), i * 200));
    }
  }, { threshold: .4 }).observe(processSection);
}

/* =====================================================
   WHY STRIP
===================================================== */

document.querySelectorAll(".why-line").forEach(el => {
  new IntersectionObserver(e => {
    if (e[0].isIntersecting) el.classList.add("show");
  }, { threshold: .4 }).observe(el);
});

/* =====================================================
   FEEDBACK
===================================================== */

document.querySelectorAll(".feedback-card").forEach(card => {
  revealObserver.observe(card);
});

/* =====================================================
   FOOTER
===================================================== */

const footer = document.querySelector(".footer");

window.addEventListener("scroll", () => {
  if (footer && footer.getBoundingClientRect().top < window.innerHeight - 100) {
    footer.classList.add("show");
  }
});