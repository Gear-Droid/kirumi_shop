const sizes = document.querySelectorAll('.size');
const colors = document.querySelectorAll('.color');
const productImgs = document.querySelectorAll('.productImg');
const gradients = document.querySelectorAll('.gradient');
const productImgBg = document.querySelector('.productBackground');

let prevColor = "blue";
let animationEnd = true;

function changeSize(){
    sizes.forEach(size => size.classList.remove('active'));
    this.classList.add('active');
}

function changeColor(){
    if(!animationEnd) return;
    let primary = this.getAttribute('primary');
    let color = this.getAttribute('color');
    let productImg = document.querySelector(`.productImg[color="${color}"]`);
    let gradient = document.querySelector(`.gradient[color="${color}"]`);
    let prevGradient = document.querySelector(`.gradient[color="${prevColor}"]`);

    colors.forEach(c => c.classList.remove('active'));
    this.classList.add('active');

    document.documentElement.style.setProperty('--primary', primary);
    
    productImgs.forEach(s => s.classList.remove('show'));
    productImg.classList.add('show');

    gradients.forEach(g => g.classList.remove('first', 'second'));
    gradient.classList.add('first');
    prevGradient.classList.add('second');

    prevColor = color;
    animationEnd = false;

    gradient.addEventListener('animationend', () => {
        animationEnd = true;
    })
}

sizes.forEach(size => size.addEventListener('click', changeSize));
colors.forEach(c => c.addEventListener('click', changeColor));

let x = window.matchMedia("(max-width: 1000px)");

function changeHeight(){
    if(x.matches){
        let productImgHeight = productImgs[0].offsetHeight;
        productImgBg.style.height = `${productImgHeight * 0.9}px`;
    }
    else{
        productImgBg.style.height = "400px";
    }
}

changeHeight();

window.addEventListener('resize', changeHeight);