// 🌟 Glitter particles background
const glow = document.querySelector('.glow-bg');

if (glow) {
  setInterval(() => {
    const spark = document.createElement('div');
    spark.classList.add('spark');
    spark.style.left = Math.random() * 100 + 'vw';
    spark.style.animationDuration = 2 + Math.random() * 3 + 's';
    glow.appendChild(spark);
    setTimeout(() => spark.remove(), 5000);
  }, 200);
}
